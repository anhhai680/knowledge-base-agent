# Technical Context: Knowledge Base Agent

## Technology Stack

### Core Technologies

**Programming Language & Framework**
- **Python 3.11+**: Core application language with modern type hints and async support
- **LangChain 0.1.0+**: RAG framework for LLM orchestration and document processing
- **FastAPI**: Modern async web framework for REST API development
- **Pydantic 2.5+**: Data validation and settings management with type safety

**AI & Machine Learning**
- **OpenAI API**: GPT models for text generation and embeddings
- **Google Gemini**: Alternative LLM provider with competitive performance
- **Azure OpenAI**: Enterprise OpenAI deployment for corporate environments
- **Ollama**: Local LLM deployment for privacy and cost optimization
- **HuggingFace Transformers**: Fallback embedding models and tokenization

**Vector Database & Storage**
- **ChromaDB 0.4.0+**: Primary vector database for semantic search
- **SQLite**: Embedded database for ChromaDB persistence
- **Docker Volumes**: Data persistence across container restarts

**Development & Deployment**
- **Docker & Docker Compose**: Containerized deployment and development
- **Uvicorn**: ASGI server for FastAPI applications
- **Git & GitHub API**: Source code integration and repository management

## Development Environment

### Local Development Setup

**Prerequisites:**
```bash
# System requirements
Python 3.11+
Docker Desktop
Git
```

**Environment Configuration:**
```bash
# Core environment variables
LLM_PROVIDER=ollama|openai|gemini|azure_openai
LLM_MODEL=<model_name>
EMBEDDING_MODEL=<embedding_model_name>

# API credentials (configure as needed)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...

# Service configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
API_HOST=0.0.0.0
API_PORT=8000

# GitHub integration
GITHUB_TOKEN=ghp_...
```

**Development Workflow:**
1. **Setup**: `python -m venv venv && source venv/bin/activate`
2. **Dependencies**: `pip install -r requirements-dev.txt`
3. **Configuration**: Copy `.env.example` to `.env` and configure
4. **Services**: `docker-compose up -d chroma ollama` (background services)
5. **Application**: `python main.py` (local development)
6. **Testing**: `pytest tests/` (unit and integration tests)

### Docker Development Environment

**Full Stack Deployment:**
```bash
# Start all services with persistence
./setup_chroma_persistence.sh
docker-compose up -d

# Validate data persistence
./validate_chroma_persistence.sh

# View logs
docker-compose logs -f knowledge-base-agent
```

**Service Architecture in Docker:**
- **knowledge-base-agent**: Main application container (port 8000)
- **chroma**: Vector database service (port 8001 → 8000)
- **ollama**: Local LLM service (port 11434)

## Technical Constraints

### Performance Requirements
- **Indexing Speed**: Process 1000+ files in under 5 minutes
- **Query Response**: Average response time < 3 seconds
- **Concurrent Users**: Support 10+ simultaneous users
- **Memory Usage**: Reasonable memory footprint for local development

### Compatibility Requirements
- **Python Version**: 3.11+ (required for modern async features)
- **Docker Version**: Docker Compose v2 (for modern compose features)
- **Platform Support**: Linux, macOS, Windows (via Docker)
- **Architecture**: x86_64 and ARM64 (Apple Silicon) support

### Resource Constraints
- **Memory**: Minimum 8GB RAM for local development with Ollama
- **Storage**: Variable based on indexed repositories (1-10GB typical)
- **Network**: Internet access required for external LLM APIs
- **Compute**: CPU-intensive during initial indexing phase

## Dependencies & Integrations

### Core Python Dependencies

**LangChain Ecosystem:**
```python
langchain>=0.1.0              # Core RAG framework
langchain-openai>=0.1.0       # OpenAI integration
langchain-google-genai>=1.0.0 # Gemini integration
langchain-community>=0.0.20   # Community extensions
langchain-ollama>=0.1.0       # Ollama integration
```

**LLM Provider SDKs:**
```python
openai>=1.0.0                 # OpenAI API client
google-generativeai>=0.3.0    # Gemini API client
ollama>=0.2.0                 # Ollama client
```

**Vector Storage:**
```python
chromadb>=0.4.0               # Vector database
pgvector>=0.1.0               # PostgreSQL vector extension (future)
psycopg2-binary>=2.9.0        # PostgreSQL adapter
```

**Document Processing:**
```python
pypdf>=3.17.0                 # PDF processing
python-docx>=0.8.11           # Word document processing
beautifulsoup4>=4.12.0        # HTML parsing
lxml>=4.9.0                   # XML processing
```

**Text Processing & ML:**
```python
tiktoken>=0.5.0               # OpenAI tokenization
sentence-transformers>=2.2.0  # Local embeddings
transformers>=4.21.0          # HuggingFace models
torch>=1.11.0                 # PyTorch for local models
```

**Web Framework:**
```python
fastapi>=0.104.0              # REST API framework
uvicorn>=0.24.0               # ASGI server
pydantic>=2.5.0,<3.0.0        # Data validation
pydantic-settings>=2.4.0      # Settings management
```

**GitHub Integration:**
```python
pygithub>=1.59.0              # GitHub API client
gitpython>=3.1.0              # Git repository handling
```

### External Service Dependencies

**LLM Providers:**
- **OpenAI API**: GPT models and embeddings
- **Google Gemini API**: Alternative LLM with competitive pricing
- **Azure OpenAI**: Enterprise deployment option
- **Ollama**: Local model deployment (self-hosted)

**Version Control:**
- **GitHub API**: Repository access and content retrieval
- **Git**: Version control and change tracking

**Optional Integrations:**
- **Redis**: Future caching layer for performance optimization
- **PostgreSQL**: Alternative vector store backend with pgvector

## Configuration Management

### Environment-Based Configuration

**Configuration Hierarchy:**
1. **Environment Variables**: Highest priority (production settings)
2. **`.env` File**: Development configuration
3. **Default Values**: Fallback configuration in `settings.py`

**Configuration Categories:**

**LLM Configuration:**
```python
llm_provider: str = "openai"        # Provider selection
llm_model: str = "gpt-3.5-turbo"    # Model specification
llm_api_base_url: Optional[str]     # Custom API endpoints
temperature: float = 0.7            # Response creativity
max_tokens: int = 4000              # Response length limit
```

**Embedding Configuration:**
```python
embedding_model: str = "text-embedding-ada-002"  # Embedding model
embedding_api_base_url: Optional[str]            # Custom embedding endpoint
```

**Processing Configuration:**
```python
chunk_size: int = 1000              # Document chunk size
chunk_overlap: int = 200            # Chunk overlap for context
```

**Storage Configuration:**
```python
chroma_host: str = "localhost"      # Vector DB host
chroma_port: int = 8000             # Vector DB port
chroma_collection_name: str         # Collection identifier
```

### Model Switching Utility

**Automated Model Configuration:**
```bash
# Switch to different providers
python switch_models.py switch ollama --llm-model llama3.1:8b
python switch_models.py switch openai --llm-model gpt-4o-mini
python switch_models.py switch gemini --llm-model gemini-1.5-flash

# Check current configuration
python switch_models.py show

# Validate configuration
python switch_models.py validate
```

## Development Tools & Practices

### Code Quality Tools

**Formatting & Linting:**
```bash
black .                     # Code formatting
isort .                     # Import sorting
flake8 .                    # Style checking
mypy .                      # Type checking
```

**Testing Framework:**
```python
pytest>=7.0.0              # Testing framework
pytest-asyncio>=0.20.0     # Async test support
pytest-cov>=4.0.0          # Coverage reporting
```

**Development Dependencies:**
```python
# Development tools
black>=23.0.0               # Code formatter
isort>=5.12.0               # Import sorter
flake8>=6.0.0               # Linter
mypy>=1.0.0                 # Type checker
```

### Logging & Monitoring

**Structured Logging:**
```python
# JSON-formatted logs for production
# Console-formatted logs for development
# Configurable log levels (DEBUG, INFO, WARNING, ERROR)
# Request tracking and performance metrics
```

**Health Monitoring:**
```python
# API health endpoints
# Component status checking
# Dependency validation
# Performance metrics collection
```

### Docker Configuration

**Multi-Stage Dockerfile:**
```dockerfile
# Optimized container builds
# Separate development and production stages
# Minimal production image size
# Security best practices
```

**Docker Compose Services:**
```yaml
# Application service with volume mounts
# ChromaDB service with data persistence
# Ollama service for local LLM deployment
# Health checks and restart policies
```

## Future Technical Considerations

### Scalability Improvements
- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Caching Layer**: Redis for query result caching
- **Database Scaling**: PostgreSQL with pgvector for larger deployments

### Security Enhancements
- **Authentication**: JWT-based API authentication
- **Authorization**: Role-based access control for repositories
- **Encryption**: At-rest encryption for sensitive data

### Performance Optimizations
- **Embedding Caching**: Cache embeddings for frequently accessed content
- **Query Optimization**: Smart retrieval strategies based on query type
- **Model Optimization**: Quantized models for faster inference

### Integration Opportunities
- **IDE Plugins**: VS Code and IntelliJ integrations
- **CLI Tools**: Command-line interface for developer workflows
- **Webhook Integration**: Automatic re-indexing on repository changes
