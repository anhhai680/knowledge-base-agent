#!/bin/bash
set -e

echo "🚀 Starting Knowledge Base Agent..."
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"

# Wait for external services to be ready
echo "⏳ Waiting for external services..."
sleep 10

# Test Chroma connectivity
echo "🔍 Testing Chroma connectivity..."
for i in {1..5}; do
    if curl -s -f http://$CHROMA_HOST:$CHROMA_PORT/api/v2/heartbeat &>/dev/null; then
        echo "✅ Chroma is responding"
        break
    else
        echo "Attempt $i/5: Chroma not ready yet, waiting..."
        sleep 5
    fi
done

# Test Ollama connectivity (if using Ollama)
if [ "$LLM_PROVIDER" = "ollama" ]; then
    echo "🔍 Testing Ollama connectivity..."
    ollama_base_url=${LLM_API_BASE_URL:-"http://ollama:11434"}
    
    for i in {1..3}; do
        if curl -s -f $ollama_base_url/api/version &>/dev/null; then
            echo "✅ Ollama is responding"
            break
        else
            echo "Attempt $i/3: Ollama not ready yet, waiting..."
            sleep 5
        fi
    done
fi

# Show environment information
echo "📋 Environment Information:"
echo "  - APP_ENV: $APP_ENV"
echo "  - LLM_PROVIDER: $LLM_PROVIDER"
echo "  - LLM_MODEL: $LLM_MODEL"
echo "  - LLM_API_BASE_URL: $LLM_API_BASE_URL"
echo "  - EMBEDDING_MODEL: $EMBEDDING_MODEL"
echo "  - CHROMA_HOST: $CHROMA_HOST"
echo "  - CHROMA_PORT: $CHROMA_PORT"

echo "🚀 Starting FastAPI application..."
exec python main.py
