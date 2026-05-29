"""
Single-file Smart Reader application with both PDF and YouTube assistant modes.
"""
import hashlib
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

from configure import EMBEDDINGS_MODEL, LLM_MODEL, LLM_TEMPERATURE, CHUNK_SIZE, CHUNK_OVERLAP
from database import MyDB

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
PDF_STORAGE = TEMP_DIR / "pdfs"
INDEX_STORAGE = TEMP_DIR / "pdf_memory"
PDF_STORAGE.mkdir(parents=True, exist_ok=True)
INDEX_STORAGE.mkdir(parents=True, exist_ok=True)

db = MyDB()


def _get_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha1(file_bytes).hexdigest()


def _load_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)


def _get_index_dir(file_hash: str) -> Path:
    return INDEX_STORAGE / file_hash


def _load_or_build_pdf_index(pdf_path: Path, docs):
    file_hash = _get_file_hash(pdf_path.read_bytes())
    index_dir = _get_index_dir(file_hash)

    if index_dir.exists() and any(index_dir.iterdir()):
        return FAISS.load_local(str(index_dir), _load_embeddings()), file_hash

    index_dir.mkdir(parents=True, exist_ok=True)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    splits = text_splitter.split_documents(docs)
    vector_store = FAISS.from_documents(splits, _load_embeddings())
    vector_store.save_local(str(index_dir))
    return vector_store, file_hash


def extract_video_id(url):
    pattern = r"(?:v=|youtu.be/)([a-zA-Z0-9_-]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


@st.cache_resource
def load_model():
    llm = HuggingFaceEndpoint(
        repo_id=LLM_MODEL,
        task="text-generation",
        temperature=LLM_TEMPERATURE,
    )
    return ChatHuggingFace(llm=llm)


@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(model_name=EMBEDDINGS_MODEL)


@st.cache_resource
def build_yt_vector_store(video_id):
    api = YouTubeTranscriptApi()
    transcript_data = api.fetch(video_id)
    transcript = " ".join(snippet.text for snippet in transcript_data)

    splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    chunks = splitter.split_text(transcript)

    vector_store = FAISS.from_texts(chunks, load_embeddings())
    return vector_store, transcript


st.set_page_config(page_title="Smart Reader", page_icon="📚", layout="wide")

st.markdown("""
<style>
    .block-container { max-width: 1150px; }
    [data-testid="stSidebar"] { min-width: 320px; }
    .status-badge {
        display: inline-block; padding: 4px 12px; border-radius: 12px;
        font-size: 0.85rem; font-weight: 600;
    }
    .badge-ready  { background: #d4edda; color: #155724; }
    .badge-idle   { background: #fff3cd; color: #856404; }
    .feature-box {
        padding: 1.5rem;
        border-radius: 8px;
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    .feature-box h3 {
        margin-top: 0;
        color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

st.title("📚 Smart Reader")
st.write("A single-file application for PDF document QA and YouTube transcript chat.")

if "current_app" not in st.session_state:
    st.session_state.current_app = "PDF Reader"

with st.sidebar:
    st.header("🧭 Navigation")
    st.session_state.current_app = st.radio(
        "Select Mode:",
        ["PDF Reader", "YouTube Chatbot"],
        index=0 if st.session_state.current_app == "PDF Reader" else 1,
    )
    st.divider()
    st.markdown("**Smart Reader** combines PDF QA and YouTube transcript search in one app.")

# PDF state
if "pdf_chat_history" not in st.session_state:
    st.session_state.pdf_chat_history = []
if "pdf_docs_loaded" not in st.session_state:
    st.session_state.pdf_docs_loaded = False
if "pdf_index" not in st.session_state:
    st.session_state.pdf_index = None
if "pdf_file_hash" not in st.session_state:
    st.session_state.pdf_file_hash = None
if "pdf_filename" not in st.session_state:
    st.session_state.pdf_filename = None
if "pdf_summary" not in st.session_state:
    st.session_state.pdf_summary = None

# YouTube state
if "yt_video_loaded" not in st.session_state:
    st.session_state.yt_video_loaded = False
if "yt_video_id" not in st.session_state:
    st.session_state.yt_video_id = None
if "yt_messages" not in st.session_state:
    st.session_state.yt_messages = []

if st.session_state.current_app == "PDF Reader":
    st.subheader("PDF Reader")
    st.caption("Upload a PDF document and ask questions about its contents.")

    with st.sidebar:
        st.subheader("PDF Controls")
        uploaded_file = st.file_uploader("Drop your PDF here", type=["pdf"])

        if uploaded_file is not None:
            if st.button("Load PDF", use_container_width=True):
                with st.spinner("Loading PDF and building memory..."):
                    try:
                        file_bytes = uploaded_file.getbuffer()
                        file_hash = _get_file_hash(file_bytes)
                        pdf_path = PDF_STORAGE / f"{file_hash}.pdf"
                        pdf_path.write_bytes(file_bytes)

                        if st.session_state.pdf_file_hash != file_hash:
                            st.session_state.pdf_chat_history = []
                            st.session_state.pdf_summary = None

                        st.session_state.pdf_file_hash = file_hash
                        st.session_state.pdf_filename = uploaded_file.name

                        index_dir = _get_index_dir(file_hash)
                        if index_dir.exists() and any(index_dir.iterdir()):
                            vector_store = FAISS.load_local(str(index_dir), _load_embeddings())
                        else:
                            loader = PyPDFLoader(str(pdf_path))
                            docs = loader.load()
                            vector_store, _ = _load_or_build_pdf_index(pdf_path, docs)

                        st.session_state.pdf_index = vector_store
                        st.session_state.pdf_docs_loaded = True
                        db.add_upload(
                            "pdf",
                            uploaded_file.name,
                            str(pdf_path),
                            metadata={"file_hash": file_hash, "index_dir": str(index_dir)},
                        )
                        st.success("✅ PDF loaded and memorized successfully!")
                    except Exception as e:
                        st.error(f"❌ Error loading PDF: {str(e)[:200]}")

        if st.session_state.pdf_docs_loaded:
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.pdf_chat_history = []
                st.session_state.pdf_summary = None
                st.rerun()

            if st.button("Summarize PDF", use_container_width=True):
                with st.spinner("Summarizing document from memory..."):
                    try:
                        docs = st.session_state.pdf_index.similarity_search("Summarize the document", k=20)
                        context_text = "\n\n".join(doc.page_content for doc in docs)

                        summary_template = PromptTemplate.from_template(
                            """Provide a concise summary of the following document.

Document: {context}

Summary:"""
                        )

                        chain = summary_template | load_model() | StrOutputParser()
                        summary = chain.invoke({"context": context_text[:5000]})
                        st.session_state.pdf_summary = summary
                    except Exception as e:
                        st.error(f"❌ Error summarizing PDF: {str(e)[:200]}")

    if not st.session_state.pdf_docs_loaded:
        st.info("👈 Upload a PDF file from the sidebar to get started.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Loaded:** {st.session_state.pdf_filename}")
        with col2:
            st.markdown('<span class="status-badge badge-ready">✅ Ready</span>', unsafe_allow_html=True)

        if st.session_state.pdf_summary:
            with st.expander("Document Summary", expanded=True):
                st.write(st.session_state.pdf_summary)

        st.divider()
        st.subheader("Chat about your PDF")
        for role, message in st.session_state.pdf_chat_history:
            with st.chat_message(role):
                st.markdown(message)

        if prompt_text := st.chat_input("Ask a question about the PDF..."):
            st.session_state.pdf_chat_history.append(("user", prompt_text))
            st.chat_message("user").markdown(prompt_text)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    docs = st.session_state.pdf_index.similarity_search(prompt_text, k=5)
                    context_text = "\n\n".join(doc.page_content for doc in docs)

                    chat_template = ChatPromptTemplate.from_template(
                        """You are a helpful assistant. Answer the question based on the provided context.

Context: {context}

Chat History: {history}

Question: {question}

Answer:"""
                    )
                    history_text = "\n".join(
                        [f"User: {m}" if r == "user" else f"Assistant: {m}" for r, m in st.session_state.pdf_chat_history[-5:]]
                    )
                    chain = chat_template | load_model() | StrOutputParser()
                    response = chain.invoke({
                        "context": context_text,
                        "history": history_text,
                        "question": prompt_text,
                    })

                    st.markdown(response)
                    st.session_state.pdf_chat_history.append(("assistant", response))

elif st.session_state.current_app == "YouTube Chatbot":
    st.subheader("YouTube Chatbot")
    st.caption("Paste a YouTube link, load the transcript, and ask anything about the video.")

    with st.sidebar:
        st.subheader("Video Setup")
        yt_link = st.text_input("YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")
        load_btn = st.button("🔍 Load Transcript", use_container_width=True)

        if load_btn and yt_link:
            video_id = extract_video_id(yt_link)
            if not video_id:
                st.sidebar.error("Invalid YouTube URL.")
                st.stop()

            if video_id != st.session_state.yt_video_id:
                st.session_state.yt_messages = []

            try:
                with st.spinner("Fetching transcript & building index..."):
                    vector_store, transcript = build_yt_vector_store(video_id)
                st.session_state.yt_video_loaded = True
                st.session_state.yt_video_id = video_id
                db.add_upload(
                    "youtube",
                    f"YouTube_{video_id}",
                    yt_link,
                    metadata={"video_id": video_id, "transcript_length": len(transcript)},
                )
            except TranscriptsDisabled:
                st.sidebar.error(" No captions available for this video.")
                st.stop()
            except Exception as e:
                st.sidebar.error(f" Error: {e}")
                st.stop()
        elif load_btn and not yt_link:
            st.sidebar.warning("Please paste a URL first.")

        if st.session_state.yt_video_loaded:
            st.markdown('<span class="status-badge badge-ready">✅ Ready</span>', unsafe_allow_html=True)
            st.image(f"https://img.youtube.com/vi/{st.session_state.yt_video_id}/hqdefault.jpg", use_container_width=True)
            st.divider()
            if st.button(" Clear chat", use_container_width=True):
                st.session_state.yt_messages = []
                st.rerun()

    if not st.session_state.yt_video_loaded:
        st.markdown("---")
        st.info("👈 Paste a YouTube video URL in the sidebar and click **Load Transcript** to get started.")
    else:
        vector_store, transcript = build_yt_vector_store(st.session_state.yt_video_id)
        with st.expander(" Transcript", expanded=False):
            st.write(transcript)

        parser = StrOutputParser()
        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 4})
        parallel_chain = RunnableParallel({
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        })
        chain = parallel_chain | PromptTemplate(
            template="""
      You are a helpful assistant.
      Answer ONLY from the provided transcript context.
      If the context is insufficient, just say This information is not available in the provided context.

      {context}
      Question: {question}
    """,
            input_variables=["context", "question"],
        ) | load_model() | parser

        for msg in st.session_state.yt_messages:
            st.chat_message(msg["role"]).write(msg["content"])

        if user_query := st.chat_input("Ask a question about the video..."):
            st.session_state.yt_messages.append({"role": "user", "content": user_query})
            st.chat_message("user").write(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = chain.invoke(user_query)
                st.write(result)
                st.session_state.yt_messages.append({"role": "assistant", "content": result})
