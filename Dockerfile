# Use a slim Python base image for smaller builds.
FROM python:3.11-slim

# Set working directory.
WORKDIR /app

# Install system dependencies required by some Python packages.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc git curl && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency definitions.
COPY requirements.txt ./

# Install Python dependencies.
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files.
COPY . /app

# Expose Streamlit default port.
EXPOSE 8501

# Set environment variables for Streamlit.
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLECORS=false \
    STREAMLIT_SERVER_PORT=8501 \
    PYTHONUNBUFFERED=1

# Run the app.
CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0"]
