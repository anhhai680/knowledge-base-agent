# Knowledge Base Agent

An AI-powered knowledge base agent that can index GitHub repositories and answer questions about your code using RAG (Retrieval-Augmented Generation).

## Features

- **GitHub Repository Indexing**: Automatically index code from GitHub repositories
- **Intelligent Q&A**: Ask questions about your codebase and get accurate answers
- **Multiple LLM Support**: Works with OpenAI GPT and Google Gemini
- **Vector Search**: Uses Chroma for efficient semantic search
- **REST API**: Full-featured API for integration
- **Web UI**: Simple web interface for chatting with your code

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

3. **Install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Running with Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

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