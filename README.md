# 📚 Smart Reader

A unified platform for intelligent document analysis combining **PDF Reader** and **YouTube Chatbot** with PostgreSQL database integration.

## 🚀 Features

### 📄 PDF Reader
- Upload and analyze PDF documents
- Smart document indexing with FAISS vector store
- Instant document summarization
- Interactive chat interface for Q&A
- Persistent chat history in PostgreSQL

### ▶️ YouTube Chatbot
- Extract transcripts from YouTube videos
- Intelligent question answering
- Context-aware responses
- Semantic search over video content
- Video thumbnail preview

### 💾 Database
- PostgreSQL (Supabase) integration
- Persistent storage of uploads and chat history
- Query history and metadata tracking

## 📋 Requirements

- Python 3.9+
- PostgreSQL database (Supabase)
- HuggingFace API token

## 🔧 Installation

### 1. Clone or download the project

```bash
cd advance-pdf-read
```

### 2. Create a virtual environment (recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root by copying `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your actual values:

```env
# Get your HuggingFace token from https://huggingface.co/settings/tokens
HUGGINGFACE_API_TOKEN=your_token_here

# Your Supabase PostgreSQL credentials
DB_HOST=db.usebsanqiuurcbeneuhn.supabase.co
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=thisispasssword
DB_NAME=postgres
```

### 5. Verify database connection

The application automatically initializes database tables on first run. Ensure:
- PostgreSQL service is accessible
- Credentials in `.env` are correct
- Network allows connection to Supabase

## 🚀 Running the Application

### Start the main application

```bash
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`

### Features available in sidebar

- **📄 PDF Reader** - Upload and chat about PDFs
- **▶️ YouTube Chatbot** - Analyze YouTube videos

## 📁 Project Structure

```
advance-pdf-read/
├── main.py                          # Main Streamlit app entry point
├── requirements.txt                 # Project dependencies
├── .env.example                     # Environment variables template
├── .env                             # Environment variables (create from .env.example)
│
├── study_config.py                  # Configuration settings
├── study_db.py                      # PostgreSQL database handler
│
├── pages/
│   ├── 1_📄_PDF_Reader.py           # PDF reader page
│   └── 2_▶️_YouTube_Chatbot.py       # YouTube chatbot page
│
├── temp/
│   ├── pdfs/                        # Uploaded PDF files
│   └── pdf_memory/                  # FAISS vector stores
│
└── README.md                        # This file
```

## 🗄️ Database Schema

### `uploads` table
```sql
CREATE TABLE uploads (
    id SERIAL PRIMARY KEY,
    upload_type VARCHAR(50) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### `chat_history` table
```sql
CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    upload_id INTEGER REFERENCES uploads(id),
    role VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HUGGINGFACE_API_TOKEN` | HuggingFace API token | Required |
| `DB_HOST` | PostgreSQL host | `db.usebsanqiuurcbeneuhn.supabase.co` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | Required |
| `DB_NAME` | Database name | `postgres` |

### Application Settings (in `study_config.py`)

```python
EMBEDDINGS_MODEL = "BAAI/bge-small-en-v1.5"  # Embedding model
LLM_MODEL = "meta-llama/Llama-3.3-70B-Instruct"  # Language model
LLM_TEMPERATURE = 0.5  # Model temperature (0-1)
CHUNK_SIZE = 1500  # Text chunk size for splitting
CHUNK_OVERLAP = 300  # Overlap between chunks
SIMILARITY_SEARCH_K = 5  # Number of results in semantic search
```

## 💡 Usage Examples

### PDF Reader

1. Open the app and navigate to **📄 PDF Reader**
2. Upload a PDF file
3. Click "Load PDF"
4. Optional: Click "Summarize PDF" for a quick overview
5. Ask questions about the PDF content
6. Chat history is automatically saved

### YouTube Chatbot

1. Navigate to **▶️ YouTube Chatbot**
2. Paste a YouTube video URL
3. Click "Load Transcript"
4. View the video thumbnail and transcript (in sidebar)
5. Ask questions about the video content
6. Get context-aware responses

## 🤖 AI Models Used

- **LLM**: Meta Llama 3.3 70B Instruct
- **Embeddings**: BAAI BGE-small-en-v1.5
- **Vector Store**: FAISS (Facebook AI Similarity Search)

## 🔐 Security Notes

- Keep `.env` file private (don't commit to git)
- Use environment variables for sensitive data
- Database credentials should follow your organization's security policies
- Add `.env` to `.gitignore` if using version control

## 📦 Dependencies

Key packages:
- **streamlit**: Web interface framework
- **langchain**: LLM framework
- **langchain-huggingface**: HuggingFace integration
- **faiss-cpu**: Vector similarity search
- **psycopg2**: PostgreSQL adapter
- **python-dotenv**: Environment variable management

See `requirements.txt` for complete list.

## 🐛 Troubleshooting

### Database Connection Error
- Verify database credentials in `.env`
- Check network connectivity to Supabase
- Ensure PostgreSQL service is running

### Model Loading Slow
- First run downloads models (may take time)
- Subsequent runs use cache
- Check internet connection and disk space

### PDF Upload Error
- Ensure PDF is not corrupted
- Check file size (large files may timeout)
- Verify temporary directory has write permissions

### YouTube Error
- Confirm video has captions/transcripts enabled
- Try another video to verify connectivity
- Check YouTube Transcript API availability

## 🚀 Performance Tips

1. **First run**: Allow extra time for model downloads
2. **Reuse sessions**: Keep app running to avoid reloading
3. **PDF size**: Keep PDFs under 50MB for optimal performance
4. **Database**: Ensure stable internet connection for Supabase

## 📝 API Tokens

Get your HuggingFace token:
1. Visit https://huggingface.co/settings/tokens
2. Create a new token with read permissions
3. Add to `.env` file as `HUGGINGFACE_API_TOKEN`

## 🤝 Contributing

Feel free to:
- Report issues
- Suggest improvements
- Submit pull requests

## 📄 License

This project is open source. Use and modify as needed.

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review error messages in terminal
3. Check database connectivity
4. Verify API token validity

---

**Happy reading! 📚**
