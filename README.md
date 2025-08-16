# Knowledge Base Agent

An AI-powered knowledge base agent that can index GitHub repositories and answer questions about your code using RAG (Retrieval-Augmented Generation).

## Features

- **GitHub Repository Indexing**: Automatically index code from GitHub repositories
- **Intelligent Q&A**: Ask questions about your codebase and get accurate answers
- **Multiple LLM Support**: Works with OpenAI GPT, Google Gemini, Azure OpenAI, and Ollama
- **Multiple Embedding Models**: Support for OpenAI, Gemini, Ollama, and HuggingFace embeddings
- **Easy Model Switching**: Simple configuration system for changing models
- **Vector Search**: Uses Chroma for efficient semantic search
- **Accurate Document Counting**: Tracks both original files and processed chunks separately
- **REST API**: Full-featured API for integration
- **Web UI**: Simple web interface for chatting with your code

## Supported Models

### LLM Providers
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-3.5-turbo, etc.
- **Gemini**: Gemini-1.5-pro, Gemini-1.5-flash, Gemini-pro
- **Azure OpenAI**: Azure-hosted OpenAI models
- **Ollama**: Local models (Llama3.1, Mistral, CodeLlama, etc.)

### Embedding Providers
- **OpenAI**: text-embedding-3-small, text-embedding-3-large, text-embedding-ada-002
- **Gemini**: models/embedding-001
- **Ollama**: nomic-embed-text, all-minilm, mxbai-embed-large
- **HuggingFace**: sentence-transformers models (fallback)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- GitHub token (for private repositories)
- OpenAI API key or Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd knowledge-base-agent
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Configure your models**
   ```bash
   cp .env.sample .env
   # Edit .env with your preferred LLM and embedding models
   
   # Quick examples:
   # For OpenAI: LLM_PROVIDER=openai, LLM_MODEL=gpt-4o-mini
   # For Ollama: LLM_PROVIDER=ollama, LLM_MODEL=llama3.1:8b
   # For Gemini: LLM_PROVIDER=gemini, LLM_MODEL=gemini-1.5-flash
   ```

   Or use the model switching utility:
   ```bash
   # Switch to Ollama (local)
   python switch_models.py switch ollama --llm-model llama3.1:8b --embedding-model nomic-embed-text
   
   # Switch to OpenAI
   python switch_models.py switch openai --llm-model gpt-4o-mini --llm-api-key your-key
   
   # Check current configuration
   python switch_models.py show
   ```

4. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Running with Docker Compose (Recommended)

```bash
# Set up proper data persistence (run once)
./setup_chroma_persistence.sh

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Validate data persistence
./validate_chroma_persistence.sh

# Stop services (data will persist)
docker-compose down
```

## Document Counting

The system now accurately tracks two different counts for each repository:

- **`original_files_count`**: The actual number of files in the repository (e.g., 50 Python files)
- **`documents_count`**: The number of chunks created after processing (e.g., 200 chunks)

This distinction is important because:
- **Files** represent the actual source code structure
- **Chunks** represent how the content is split for vector search
- The web interface displays the file count for better user understanding
- The chunk count is used internally for vector store operations

For example, a repository with 25 source files might be chunked into 120 chunks for optimal search performance.

**Note**: The Chroma data persistence fix ensures that your knowledge base data survives container restarts and rebuilds.

### Running Locally

```bash
# Start Chroma vector database (optional, will use local persistence if not available)
docker run -p 8001:8000 chromadb/chroma:latest

# Start the API server
python main.py
```

## Usage

### Web Interface

Open http://localhost:3000 in your browser to access the web UI.

1. Add GitHub repositories using the sidebar
2. Wait for indexing to complete
3. Ask questions about your code!

### API Usage

#### Index a Repository
```bash
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_urls": ["https://github.com/user/repo"],
    "branch": "main"
  }'
```

#### Ask a Question
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How does the authentication work?",
    "max_results": 5
  }'
```

#### Check Health
```bash
curl http://localhost:8000/health
```

### Environment Configuration

Key environment variables in `.env`:

```bash
# Required: At least one LLM provider
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key

# Required: GitHub access
GITHUB_TOKEN=your_github_token

# Optional: Vector database (defaults to local Chroma)
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Optional: Processing settings
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TEMPERATURE=0.7
```

## Configuration

### Model Configuration

The Knowledge Base Agent supports multiple LLM and embedding providers. See [MODEL_CONFIGURATION.md](docs/MODEL_CONFIGURATION.md) for detailed configuration instructions.

**Quick Configuration Examples:**

```bash
# OpenAI Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
OPENAI_API_KEY=your-openai-key

# Ollama Configuration (Local)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b
EMBEDDING_MODEL=nomic-embed-text
LLM_API_BASE_URL=http://localhost:11434/v1

# Gemini Configuration
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
EMBEDDING_MODEL=models/embedding-001
GEMINI_API_KEY=your-gemini-key
```

### Configuration Utilities

```bash
# Test your configuration
python test_configuration.py

# Switch models easily
python switch_models.py switch ollama --llm-model llama3.1:8b

# Get model recommendations
python switch_models.py recommendations
```

### API Configuration Endpoints

```bash
# Check configuration status
curl http://localhost:8000/config

# Validate configuration
curl http://localhost:8000/config/validate

# Get model recommendations
curl http://localhost:8000/config/models
```

## Architecture

The system consists of:

- **Document Loaders**: Extract content from GitHub repositories
- **Text Processors**: Clean and chunk documents for better retrieval
- **Vector Store**: Store document embeddings (Chroma)
- **LLM Interface**: Handle queries using OpenAI or Gemini
- **RAG Pipeline**: Combine retrieval and generation
- **API Layer**: FastAPI-based REST endpoints
- **Web UI**: Simple HTML/JS interface

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Supported File Types

- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.ts`, `.jsx`, `.tsx`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`, `.h`)
- C# (`.cs`)
- PHP (`.php`)
- Ruby (`.rb`)
- Go (`.go`)
- Rust (`.rs`)
- Swift (`.swift`)
- Kotlin (`.kt`)
- Scala (`.scala`)
- Documentation (`.md`, `.txt`, `.rst`)
- Configuration (`.yml`, `.yaml`, `.json`, `.xml`, `.sql`)

## MVP Limitations

This is an MVP implementation with the following limitations:

- No user authentication
- No persistent storage for indexed repository metadata
- Limited error handling for edge cases
- Basic web UI without advanced features
- No repository deletion functionality
- Single-tenant only

## Development

### Project Structure

```
knowledge-base-agent/
├── src/
│   ├── agents/         # RAG agent implementation
│   ├── api/           # FastAPI routes and models
│   ├── config/        # Configuration management
│   ├── llm/           # LLM provider implementations
│   ├── loaders/       # Document loaders
│   ├── processors/    # Text processing
│   ├── utils/         # Utility functions
│   └── vectorstores/  # Vector database implementations
├── ui/                # Web interface
├── tests/             # Test files
├── main.py           # Application entry point
└── docker-compose.yml # Docker services
```

### Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're in the virtual environment and have installed dependencies
2. **API key errors**: Verify your API keys are correctly set in `.env`
3. **Port conflicts**: Change ports in `docker-compose.yml` if needed
4. **Memory issues**: Reduce `CHUNK_SIZE` for large repositories

### Getting Help

- Check the logs: `docker-compose logs -f`
- Verify health: `curl http://localhost:8000/health`
- Check API docs: http://localhost:8000/docs