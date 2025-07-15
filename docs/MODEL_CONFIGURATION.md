# Model Configuration Guide

This guide explains how to configure and switch between different LLM and embedding models in the Knowledge Base Agent.

## Overview

The Knowledge Base Agent supports multiple LLM and embedding providers:

### LLM Providers
- **OpenAI**: GPT models (gpt-4o, gpt-4o-mini, gpt-3.5-turbo, etc.)
- **Gemini**: Google's Gemini models (gemini-1.5-pro, gemini-1.5-flash, etc.)
- **Azure OpenAI**: Azure-hosted OpenAI models
- **Ollama**: Local/self-hosted models (llama3.1, mistral, codellama, etc.)

### Embedding Providers
- **OpenAI**: text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002
- **Gemini**: models/embedding-001
- **Ollama**: nomic-embed-text, all-minilm, mxbai-embed-large
- **HuggingFace**: sentence-transformers models (fallback, local)

## Configuration

### Environment Variables

The configuration is managed through environment variables in your `.env` file:

```bash
# LLM Configuration
LLM_PROVIDER=ollama  # Options: openai, gemini, azure_openai, ollama
LLM_MODEL=llama3.1:8b  # Model name for the chosen provider
LLM_API_BASE_URL=http://localhost:11434/v1  # Base URL (mainly for ollama)

# Embedding Configuration
EMBEDDING_MODEL=nomic-embed-text  # Embedding model name
EMBEDDING_API_BASE_URL=http://localhost:11434/v1/embeddings  # Base URL (mainly for ollama)

# API Keys (configure only what you need)
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
```

### Example Configurations

#### OpenAI Configuration
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=sk-your-openai-key
```

#### Gemini Configuration
```bash
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=models/embedding-001
GEMINI_API_KEY=your-gemini-key
```

#### Ollama Configuration (Local)
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text
LLM_API_BASE_URL=http://localhost:11434/v1
EMBEDDING_API_BASE_URL=http://localhost:11434/v1/embeddings
```

#### Azure OpenAI Configuration
```bash
LLM_PROVIDER=azure_openai
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-large
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

## Usage

### 1. Manual Configuration

1. Copy `.env.sample` to `.env`:
   ```bash
   cp .env.sample .env
   ```

2. Edit `.env` with your preferred configuration

3. Restart the application:
   ```bash
   python main.py
   ```

### 2. Using the Model Switch Utility

The `switch_models.py` utility provides an easy way to switch between providers:

```bash
# Switch to OpenAI
python switch_models.py switch openai --llm-model gpt-4o-mini --embedding-model text-embedding-3-small

# Switch to Ollama
python switch_models.py switch ollama --llm-model llama3.1:8b --embedding-model nomic-embed-text

# Switch to Gemini
python switch_models.py switch gemini --llm-model gemini-1.5-flash

# Show current configuration
python switch_models.py show

# Show model recommendations
python switch_models.py recommendations
```

### 3. API Endpoints

Check configuration status via API:

```bash
# Get current configuration
curl http://localhost:8000/config

# Validate configuration
curl http://localhost:8000/config/validate

# Get model recommendations
curl http://localhost:8000/config/models
```

## Testing Configuration

Use the test script to verify your configuration:

```bash
python test_configuration.py
```

This will:
- Show current configuration status
- Test LLM initialization and invocation
- Test embedding generation
- Display model recommendations

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - Ensure API keys are properly set in `.env`
   - Check that keys have proper permissions
   - Verify key format (no extra quotes or spaces)

2. **Ollama Connection Issues**
   - Ensure Ollama is running: `ollama serve`
   - Check if the model is available: `ollama list`
   - Verify the base URL is correct

3. **Model Not Found**
   - Check if the model name is correct
   - For Ollama, pull the model: `ollama pull llama3.1:8b`
   - Use model recommendations endpoint for valid names

4. **Embedding Model Issues**
   - Ensure embedding model is compatible with provider
   - Check API base URLs for custom endpoints
   - Verify model dimensions match your vector database

### Validation

The system automatically validates configurations on startup. Check logs for validation errors:

```bash
# Check configuration validity
python switch_models.py show
```

### Provider-Specific Setup

#### Ollama Setup
1. Install Ollama: https://ollama.ai/
2. Start Ollama server: `ollama serve`
3. Pull desired models:
   ```bash
   ollama pull llama3.1:8b
   ollama pull nomic-embed-text
   ```

#### OpenAI Setup
1. Get API key from: https://platform.openai.com/api-keys
2. Set in environment: `OPENAI_API_KEY=sk-your-key`

#### Gemini Setup
1. Get API key from: https://makersuite.google.com/app/apikey
2. Set in environment: `GEMINI_API_KEY=your-key`

#### Azure OpenAI Setup
1. Create Azure OpenAI resource
2. Deploy models in Azure Portal
3. Get endpoint and key from Azure Portal
4. Set environment variables:
   ```bash
   AZURE_OPENAI_API_KEY=your-key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   ```

## Best Practices

1. **Model Selection**
   - Use smaller models for development (gpt-4o-mini, llama3.1:8b)
   - Use larger models for production (gpt-4o, llama3.1:70b)
   - Consider cost and latency requirements

2. **Embedding Models**
   - Match embedding dimensions with your vector database
   - Consider model performance vs. cost trade-offs
   - Use the same embedding model for indexing and querying

3. **Security**
   - Never commit API keys to version control
   - Use environment variables for sensitive data
   - Consider using key management services in production

4. **Performance**
   - Local models (Ollama) provide faster responses but require more resources
   - Cloud APIs offer better scalability but have network latency
   - Consider hybrid approaches for different use cases

## Migration

To migrate from the old configuration system:

1. Update your `.env` file with the new variables
2. Remove old individual API key configurations
3. Set `LLM_PROVIDER` and `EMBEDDING_MODEL` explicitly
4. Test configuration with `python test_configuration.py`
5. Restart the application
