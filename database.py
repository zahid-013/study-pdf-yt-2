"""
Database module for managing uploads and metadata using PostgreSQL.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json
import logging
from configure import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_SSLMODE

logger = logging.getLogger(__name__)


class MyDB:
    """PostgreSQL database handler for managing document uploads and metadata."""
    
    def __init__(self):
        """Initialize database connection settings without forcing a connection."""
        self.connection_params = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "database": DB_NAME,
            "sslmode": DB_SSLMODE,
        }
        self.enabled = bool(DB_HOST and DB_USER and DB_PASSWORD and DB_NAME)
        self.initialized = False

        if self.enabled:
            try:
                self._init_database()
            except psycopg2.Error as e:
                logger.error(f"Database initialization error: {e}")
                self.enabled = False
        else:
            logger.warning("Database disabled: missing configuration.")
    
    def _get_connection(self):
        """Get a database connection."""
        if not self.enabled:
            raise psycopg2.OperationalError("Database is disabled or unavailable.")

        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            self.enabled = False
            raise
    
    def _init_database(self):
        """Initialize database tables if they don't exist."""
        if not self.enabled:
            logger.warning("Skipping database initialization because DB is disabled.")
            return

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create uploads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploads (
                    id SERIAL PRIMARY KEY,
                    upload_type VARCHAR(50) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    file_path TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create chat history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    upload_id INTEGER REFERENCES uploads(id),
                    role VARCHAR(50) NOT NULL,
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_uploads_type 
                ON uploads(upload_type);
            """)
            
            conn.commit()
            cursor.close()
            conn.close()
            self.initialized = True
            logger.info("Database initialized successfully")
        except psycopg2.Error as e:
            logger.error(f"Database initialization error: {e}")
            self.enabled = False
            raise
    
    def add_upload(self, upload_type, filename, file_path, metadata=None):
        """
        Add a new upload record to the database.
        
        Args:
            upload_type (str): Type of upload (pdf or youtube)
            filename (str): Original filename
            file_path (str): Path where file is stored
            metadata (dict): Additional metadata
        
        Returns:
            int|None: ID of inserted record or None if DB is disabled
        """
        if not self.enabled:
            logger.warning("Database disabled; skipping add_upload.")
            return None

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO uploads (upload_type, filename, file_path, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING id;
            """, (upload_type, filename, file_path, metadata_json))
            
            upload_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Added upload record: {upload_id}")
            return upload_id
        except psycopg2.Error as e:
            logger.error(f"Error adding upload: {e}")
            raise
    
    def add_chat_message(self, upload_id, role, message):
        """
        Add a chat message to history.
        
        Args:
            upload_id (int): ID of the associated upload
            role (str): Role (user or assistant)
            message (str): Message content
        """
        if not self.enabled:
            logger.warning("Database disabled; skipping add_chat_message.")
            return None

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO chat_history (upload_id, role, message)
                VALUES (%s, %s, %s);
            """, (upload_id, role, message))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Added chat message for upload {upload_id}")
        except psycopg2.Error as e:
            logger.error(f"Error adding chat message: {e}")
            raise
    
    def get_uploads(self, upload_type=None):
        """
        Retrieve upload records.
        
        Args:
            upload_type (str, optional): Filter by upload type
        
        Returns:
            list: List of upload records
        """
        if not self.enabled:
            logger.warning("Database disabled; returning empty upload list.")
            return []

        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            if upload_type:
                cursor.execute("""
                    SELECT * FROM uploads 
                    WHERE upload_type = %s
                    ORDER BY created_at DESC;
                """, (upload_type,))
            else:
                cursor.execute("""
                    SELECT * FROM uploads 
                    ORDER BY created_at DESC;
                """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except psycopg2.Error as e:
            logger.error(f"Error retrieving uploads: {e}")
            raise
    
    def get_chat_history(self, upload_id):
        """
        Retrieve chat history for an upload.
        
        Args:
            upload_id (int): ID of the upload
        
        Returns:
            list: List of chat messages
        """
        if not self.enabled:
            logger.warning("Database disabled; returning empty chat history.")
            return []

        try:
            conn = self._get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT role, message, created_at FROM chat_history 
                WHERE upload_id = %s
                ORDER BY created_at ASC;
            """, (upload_id,))
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            return results
        except psycopg2.Error as e:
            logger.error(f"Error retrieving chat history: {e}")
            raise
    
    def delete_upload(self, upload_id):
        """
        Delete an upload record and its chat history.
        
        Args:
            upload_id (int): ID of the upload to delete
        """
        if not self.enabled:
            logger.warning("Database disabled; skipping delete_upload.")
            return None

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete associated chat history
            cursor.execute("DELETE FROM chat_history WHERE upload_id = %s;", (upload_id,))
            
            # Delete upload record
            cursor.execute("DELETE FROM uploads WHERE id = %s;", (upload_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"Deleted upload record: {upload_id}")
        except psycopg2.Error as e:
            logger.error(f"Error deleting upload: {e}")
            raise
