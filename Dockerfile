FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# RUN pip install --no-cache-dir --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY verify_startup.py .

# Copy entrypoint script
COPY entrypoint.sh .
RUN chmod +x /app/entrypoint.sh

# Create directory for Chroma persistence
RUN mkdir -p ./chroma_db

# Set default environment variables
ENV APP_ENV=production
ENV LLM_PROVIDER=ollama
ENV LLM_MODEL=llama3.2:3b
ENV LLM_API_BASE_URL=http://ollama:11434
ENV EMBEDDING_MODEL=nomic-embed-text
ENV EMBEDDING_API_BASE_URL=http://ollama:11434
ENV LOG_LEVEL=INFO
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV CHROMA_HOST=chroma
ENV CHROMA_PORT=8000
ENV CHUNK_SIZE=1000
ENV CHUNK_OVERLAP=200
ENV MAX_TOKENS=4000
ENV TEMPERATURE=0.8

# Expose port
EXPOSE 8000

# Health check with more lenient timing
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with verification
CMD ["/app/entrypoint.sh"]
