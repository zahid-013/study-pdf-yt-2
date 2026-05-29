"""
Configuration settings for the study application.
"""
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

# HuggingFace Model Configuration
EMBEDDINGS_MODEL = "BAAI/bge-small-en-v1.5"
LLM_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
LLM_TEMPERATURE = 0.5

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "")
if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    DB_HOST = parsed.hostname or "db.usebsanqiuurcbeneuhn.supabase.co"
    DB_PORT = parsed.port or 5432
    DB_USER = parsed.username or "postgres"
    DB_PASSWORD = parsed.password or "thisispasssword"
    DB_NAME = parsed.path.lstrip("/") or "postgres"
else:
    DB_HOST = os.getenv("DB_HOST", "db.usebsanqiuurcbeneuhn.supabase.co")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "thisispasssword")
    DB_NAME = os.getenv("DB_NAME", "postgres")
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")

# HuggingFace API Token
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

# Application Settings
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300
SIMILARITY_SEARCH_K = 5
