# Knowledge Base Agent

An advanced AI-powered knowledge base agent that can index GitHub repositories and answer questions about your code using RAG (Retrieval-Augmented Generation) with intelligent diagram generation capabilities.

## Features

### Core Capabilities
- **GitHub Repository Indexing**: Automatically index code from GitHub repositories
- **Intelligent Q&A**: Ask questions about your codebase and get accurate answers
- **Advanced Diagram Generation**: Create sequence diagrams, flowcharts, class diagrams, ER diagrams, and component diagrams from your code
- **Agent Router Pattern**: Intelligent query routing between knowledge-based Q&A and diagram generation
- **Enhanced Chunking**: Advanced code parsing with Tree-sitter for C#, JavaScript, and TypeScript

### LLM & Embedding Support
- **Multiple LLM Support**: Works with OpenAI GPT, Google Gemini, Azure OpenAI, and Ollama
- **Multiple Embedding Models**: Support for OpenAI, Gemini, Ollama, and HuggingFace embeddings
- **Easy Model Switching**: Simple configuration system for changing models with validation
- **Configuration Management**: Comprehensive model configuration and validation tools

### Technical Features
- **Vector Search**: Uses Chroma for efficient semantic search with persistent data
- **Advanced Parsing**: Tree-sitter integration for accurate semantic chunking
- **Document Counting**: Tracks both original files and processed chunks separately
- **REST API**: Full-featured API with health checks and configuration endpoints
- **Web UI**: Interactive web interface with Mermaid diagram rendering

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

## Diagram Generation

The Knowledge Base Agent includes advanced diagram generation capabilities that automatically detect diagram requests and generate interactive Mermaid diagrams:

### Supported Diagram Types
- **Sequence Diagrams**: Visualize interaction flows and API call sequences
- **Flowcharts**: Show process flows and decision points in your code
- **Class Diagrams**: Display class relationships and inheritance structures
- **Entity-Relationship Diagrams**: Visualize database schemas and data models
- **Component Diagrams**: Show system architecture and component relationships

### Diagram Features
- **Intelligent Detection**: Automatic detection of diagram requests from natural language
- **Multi-Language Support**: Works with Python, JavaScript, TypeScript, C#, and more
- **Interactive Rendering**: Mermaid.js integration for interactive diagrams in web UI
- **Code Analysis**: Deep analysis of repository code to generate accurate diagrams
- **Source Attribution**: Links generated diagrams back to source code files

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
docker compose up -d

# Check logs
docker compose logs -f

# Validate data persistence
./validate_chroma_persistence.sh

# Stop services (data will persist)
docker compose down
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

Open http://localhost:3000 in your browser to access the interactive web UI.

**Features:**
1. **Repository Management**: Add GitHub repositories using the sidebar
2. **Intelligent Chat**: Ask questions about your code or request diagrams
3. **Diagram Generation**: Request diagrams with natural language (e.g., "Show me a sequence diagram for user authentication")
4. **Interactive Diagrams**: Mermaid diagrams render directly in the chat interface
5. **Source References**: View source code files used to generate responses
6. **Repository Status**: Monitor indexing progress and re-index repositories as needed

### Example Queries

**Knowledge-based Questions:**
- "How does the authentication system work?"
- "What are the available API endpoints?"
- "Show me the database connection logic"

**Diagram Generation:**
- "Generate a sequence diagram for user login"
- "Create a flowchart for the order processing"
- "Show me a class diagram for the user management system"
- "Display the component architecture"

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

#### Generate a Diagram
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Generate a sequence diagram for user login",
    "max_results": 5
  }'
```

#### Check Health
```bash
curl http://localhost:8000/health
```

#### Configuration Management
```bash
# Get current configuration
curl http://localhost:8000/config

# Validate configuration
curl http://localhost:8000/config/validate

# Get available models
curl http://localhost:8000/config/models
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

- **Agent Router**: Intelligent query routing between knowledge-based Q&A and diagram generation
- **RAG Agent**: Handles traditional knowledge base queries with retrieval-augmented generation
- **Diagram Agent**: Specialized agent for generating various types of Mermaid diagrams
- **Document Loaders**: Extract content from GitHub repositories with enhanced parsing
- **Text Processors**: Advanced chunking with Tree-sitter for semantic boundary detection
- **Vector Store**: Store and retrieve document embeddings using Chroma
- **LLM Interface**: Multi-provider support for OpenAI, Gemini, Ollama, and Azure OpenAI
- **Enhanced Parsing**: Tree-sitter integration for C#, JavaScript, TypeScript, and Python
- **API Layer**: FastAPI-based REST endpoints with health checks and configuration management
- **Web UI**: Interactive interface with Mermaid diagram rendering

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

## Supported File Types

The system includes advanced parsing support for:

### Enhanced Parsing (Tree-sitter)
- **C#** (`.cs`): Classes, methods, namespaces, attributes, XML documentation
- **JavaScript** (`.js`, `.mjs`, `.jsx`): ES6 modules, classes, functions, JSX components
- **TypeScript** (`.ts`, `.tsx`): TypeScript-specific features, interfaces, type definitions

### Standard Parsing
- **Python** (`.py`): AST-based parsing for classes, functions, imports
- **Documentation** (`.md`, `.txt`): Markdown and text file processing
- **Configuration** (`.yml`, `.yaml`, `.json`): Configuration file analysis
- **PHP** (`.php`): Basic PHP file processing

### Language-Specific Features
- **Semantic Chunking**: Maintains code structure and boundaries
- **Documentation Extraction**: Preserves comments and documentation
- **Import/Export Tracking**: Maintains module relationships
- **Class and Function Boundaries**: Accurate extraction of code units

## Development Status

### Current Implementation Status
- **✅ Core RAG System**: Fully implemented with multi-provider LLM support
- **✅ Diagram Generation**: Complete with 5 diagram types and intelligent routing
- **✅ Enhanced Chunking**: Tree-sitter integration for C#, JavaScript, TypeScript
- **✅ Agent Router**: Intelligent query classification and routing
- **✅ Web Interface**: Interactive UI with Mermaid diagram rendering
- **✅ API Layer**: Complete REST API with configuration management
- **✅ Configuration System**: Model switching and validation tools
- **✅ Data Persistence**: Robust Chroma data persistence across restarts

### Advanced Features
- **Multi-Diagram Support**: Sequence, flowchart, class, ER, and component diagrams
- **Intelligent Query Routing**: Automatic detection of diagram vs knowledge requests
- **Enhanced Code Analysis**: Deep semantic analysis for accurate diagram generation
- **Configuration Validation**: Real-time model and API key validation
- **Health Monitoring**: Comprehensive health checks and component status tracking

### Known Limitations
- No user authentication (single-tenant)
- Limited error recovery for malformed code
- Basic web UI without advanced collaboration features
- No real-time repository synchronization
- Limited export formats (Mermaid only)

## Development

### Project Structure

```
knowledge-base-agent/
├── src/
│   ├── agents/            # RAG and Diagram agents with router
│   ├── api/              # FastAPI routes and models
│   ├── config/           # Configuration management
│   ├── llm/              # Multi-provider LLM implementations
│   ├── loaders/          # Document loaders (GitHub, etc.)
│   ├── processors/       # Enhanced text processing and chunking
│   │   ├── chunking/     # Language-specific chunkers
│   │   └── parsers/      # Tree-sitter and AST parsers
│   ├── utils/            # Utility functions and diagram generators
│   ├── vectorstores/     # Vector database implementations
│   └── workflows/        # Advanced workflow patterns
├── tests/                # Comprehensive test suite
├── web/                  # Interactive web interface
├── docs/                 # Documentation and implementation guides
├── memory-bank/          # Project memory and task tracking
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Multi-service deployment
└── .env.example         # Environment configuration template
```

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test categories
pytest tests/test_config.py
pytest tests/test_diagram_features.py
pytest tests/test_enhanced_rag.py
pytest tests/test_chunking/
```

### Code Quality

```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/

# Pre-commit hooks (optional)
pre-commit install
pre-commit run --all-files
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
3. **Port conflicts**: Change ports in `docker-compose.yml` if needed (8000, 8001, 11434, 3000)
4. **Memory issues**: Reduce `CHUNK_SIZE` for large repositories
5. **Diagram generation failures**: Ensure code contains clear interaction patterns
6. **Tree-sitter parsing errors**: System falls back to regex parsing automatically
7. **Docker build failures**: Clear Docker cache with `docker system prune -f`

### Performance Tips

- **Use Docker Compose**: Recommended for optimal performance and persistence
- **Configure chunk sizes**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` for your use case
- **Choose appropriate models**: Balance speed vs accuracy based on your needs
- **Enable enhanced chunking**: Set `USE_ENHANCED_CHUNKING=true` for better code understanding

### Getting Help

- **Logs**: Check logs with `docker compose logs -f kb-agent`
- **Health status**: Verify health at `curl http://localhost:8000/health`
- **API documentation**: Interactive docs at http://localhost:8000/docs
- **Configuration**: Validate config with `python switch_models.py show`
- **Memory bank**: Check `memory-bank/` folder for implementation details