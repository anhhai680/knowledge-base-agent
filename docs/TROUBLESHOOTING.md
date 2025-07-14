# Troubleshooting Guide

## Common Issues and Solutions

### 1. OpenAI API Issues

#### Error: "Project does not have access to model text-embedding-ada-002"

**Possible Causes:**
- API key doesn't have access to the embedding model
- Insufficient credits or quota exceeded
- Wrong API key or project configuration

**Solutions:**
1. **Check API Key Validity:**
   ```bash
   python test_apis.py
   ```

2. **Verify OpenAI Account:**
   - Login to [OpenAI Platform](https://platform.openai.com)
   - Check your usage limits and billing
   - Ensure your project has access to `text-embedding-ada-002`

3. **Alternative Solutions:**
   - Use Gemini embeddings (set `GEMINI_API_KEY` in `.env`)
   - Use local HuggingFace embeddings (no API key required)

### 2. Docker Port Conflicts

#### Error: Port already in use

**Solution:**
The docker-compose.yml has been configured to avoid conflicts:
- Knowledge Base Agent: `localhost:8000`
- Chroma DB: `localhost:8001`
- UI: `localhost:3000`

### 3. Chroma Connection Issues

#### Error: Cannot connect to Chroma database

**Solutions:**
1. **For Docker Environment:**
   ```bash
   docker-compose up chroma -d
   # Wait for Chroma to start, then:
   docker-compose up knowledge-base-agent
   ```

2. **For Local Development:**
   ```bash
   # Install and run Chroma locally
   pip install chromadb
   chroma run --host localhost --port 8001
   ```

### 4. Embedding Provider Fallback

The system now supports automatic fallback between embedding providers:

1. **OpenAI** (primary) - requires API key
2. **Gemini** (secondary) - requires API key  
3. **HuggingFace** (fallback) - local, no API key needed

### 5. Environment Configuration

#### Docker vs Local Development

**Docker Environment (.env):**
```bash
CHROMA_HOST=chroma
CHROMA_PORT=8000
```

**Local Development (.env):**
```bash
CHROMA_HOST=localhost
CHROMA_PORT=8001
```

### 6. Testing Your Setup

Run the comprehensive test script:
```bash
python test_apis.py
```

This will test:
- ✅ OpenAI API connection
- ✅ Gemini API connection  
- ✅ HuggingFace local embeddings
- ✅ Chroma database connection

### 7. Quick Fixes

#### Reset Everything:
```bash
# Stop all containers
docker-compose down -v

# Rebuild and restart
docker-compose up --build
```

#### Use Local Embeddings Only:
Remove or comment out API keys in `.env`:
```bash
# OPENAI_API_KEY=your_key_here
# GEMINI_API_KEY=your_key_here
```

The system will automatically use local HuggingFace embeddings.

### 8. Performance Considerations

**Local HuggingFace Embeddings:**
- ✅ No API costs
- ✅ No rate limits
- ⚠️ Slower than cloud APIs
- ⚠️ Uses local CPU/memory

**Cloud APIs (OpenAI/Gemini):**
- ✅ Fast processing
- ✅ High quality embeddings
- ⚠️ API costs apply
- ⚠️ Rate limits may apply

### 9. Getting Help

If you're still experiencing issues:

1. Check the logs:
   ```bash
   docker-compose logs knowledge-base-agent
   docker-compose logs chroma
   ```

2. Run the test script:
   ```bash
   python test_apis.py
   ```

3. Verify your environment variables are correctly set in `.env`
