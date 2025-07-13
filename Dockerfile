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
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY verify_startup.py .

# Create directory for Chroma persistence
RUN mkdir -p ./chroma_db

# Create a simple entrypoint script for better error handling
RUN echo '#!/bin/bash\nset -e\necho "Starting Knowledge Base Agent..."\npython verify_startup.py\nif [ $? -eq 0 ]; then\n    echo "Verification passed, starting application..."\n    exec python main.py\nelse\n    echo "Verification failed, exiting..."\n    exit 1\nfi' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with verification
CMD ["/app/entrypoint.sh"]
