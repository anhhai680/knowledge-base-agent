# Knowledge Base Agent Development Instructions

**ALWAYS follow these instructions first. Only search for additional information or use other exploration methods if the instructions here are incomplete or found to be incorrect.**

## Overview

Knowledge Base Agent is a Python-based AI RAG (Retrieval-Augmented Generation) system that indexes GitHub repositories and answers questions about codebases. Built with FastAPI, LangChain, and multiple LLM providers (OpenAI, Gemini, Ollama, Azure OpenAI), deployed via Docker Compose.

## Working Effectively

### Prerequisites and Setup
- Install Python 3.11+ and Docker with Docker Compose v2
- Clone repository: `git clone <repository-url> && cd knowledge-base-agent`
- Set up environment: `cp .env.example .env` and edit with your API keys
- **CRITICAL**: At least one LLM provider API key required (OPENAI_API_KEY or GEMINI_API_KEY)
- GITHUB_TOKEN required for private repositories

### Docker Compose Deployment (Recommended)
```bash
# Set up data persistence (run once)
./setup_chroma_persistence.sh

# Build and start all services - NEVER CANCEL: Takes 10-15 minutes for initial build
docker compose up --build -d

# TIMEOUT WARNING: Set timeout to 30+ minutes for initial build. Build includes:
# - Python 3.11 base image download
# - System dependencies installation
# - pip install of 50+ packages including PyTorch, LangChain, transformers
# - Ollama and Chroma service startup

# Check service status
docker compose ps
docker compose logs -f kb-agent

# Validate data persistence
./validate_chroma_persistence.sh

# Stop services (data persists)
docker compose down
```

### Local Python Development
```bash
# Create virtual environment - takes ~5 seconds
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies - NEVER CANCEL: Takes 5-10 minutes
# TIMEOUT WARNING: Set timeout to 20+ minutes. Network issues may cause timeouts.
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Start application locally
python main.py
```

### Build Time Expectations
- **Initial Docker build**: 10-15 minutes (NEVER CANCEL - wait for completion)
- **pip install requirements.txt**: 5-10 minutes (NEVER CANCEL - network dependent)
- **Docker compose up** (after build): 3-5 minutes for services to start
- **pytest test suite**: 2-5 minutes (NEVER CANCEL - comprehensive testing)

## Validation and Testing

### Manual Validation After Changes
**ALWAYS perform these validation steps after making code changes:**

1. **Health Check**
   ```bash
   curl http://localhost:8000/health
   # Expected: {"status": "healthy", "version": "..."}
   ```

2. **API Documentation**
   - Navigate to http://localhost:8000/docs
   - Verify interactive API documentation loads
   - Test at least one endpoint (e.g., /config)

3. **Web Interface**
   - Navigate to http://localhost:3000
   - Verify the web UI loads with sidebar and chat interface
   - Test adding a repository URL in the sidebar
   - **CRITICAL**: Always test complete user workflow - don't just start/stop

4. **Repository Indexing Workflow** (End-to-End Test)
   ```bash
   # Index a small public repository
   curl -X POST "http://localhost:8000/index" \
        -H "Content-Type: application/json" \
        -d '{"repository_urls": ["https://github.com/octocat/Hello-World"], "branch": "main"}'
   
   # Query the indexed repository
   curl -X POST "http://localhost:8000/query" \
        -H "Content-Type: application/json" \
        -d '{"question": "What does this repository do?", "max_results": 3}'
   ```

### Code Quality and Testing
```bash
# ALWAYS run these before committing changes:

# Format code
black src/
isort src/

# Lint code  
flake8 src/
mypy src/

# Run tests - NEVER CANCEL: Takes 2-5 minutes for full suite
pytest tests/ --timeout=300

# Run with coverage
pytest --cov=src tests/

# Run specific test categories
pytest tests/test_config.py
pytest tests/test_diagram_features.py
```

## Common Development Tasks

### Model Configuration
```bash
# Note: switch_models.py requires dependencies to be installed
# Check current model configuration (after pip install)
python switch_models.py show

# Switch to Ollama (local, no API key required)
python switch_models.py switch ollama --llm-model llama3.1:8b --embedding-model nomic-embed-text

# Switch to OpenAI
python switch_models.py switch openai --llm-model gpt-4o-mini --llm-api-key your-key

# Test configuration (when services are running)
curl http://localhost:8000/config/validate
```

### Docker Helper Utilities
```bash
# Show service status
./docker-helper.sh status

# Clean environment (removes all data)
./docker-helper.sh clean

# Check service health
./docker-helper.sh health

# Monitor services
docker compose logs -f
docker compose ps

# Validate Docker Compose configuration
docker compose config --quiet
```

### Service Ports and URLs
- **Main Application**: http://localhost:8000 (FastAPI + API docs at /docs)
- **Web Interface**: http://localhost:3000 (HTML/JS frontend)
- **Chroma Vector DB**: http://localhost:8001 (Internal service)
- **Ollama LLM Service**: http://localhost:11434 (Local LLM server)

## Repository Structure
```
knowledge-base-agent/
├── src/                    # Main source code
│   ├── agents/            # RAG agent implementation  
│   ├── api/               # FastAPI routes and models
│   ├── config/            # Configuration management
│   ├── llm/               # LLM provider implementations
│   ├── loaders/           # Document loaders (GitHub, etc.)
│   ├── processors/        # Text processing and chunking
│   ├── utils/             # Utility functions
│   └── vectorstores/      # Vector database implementations
├── tests/                 # Test files (pytest)
├── web/                   # Web interface (HTML/JS)
├── docs/                  # Documentation
├── main.py               # Application entry point
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Multi-service deployment
└── .env.example          # Environment configuration template
```

## Critical Warnings and Known Issues

### Build and Deployment
- **NEVER CANCEL long-running builds or installs** - they may take 15+ minutes
- **Network timeouts**: pip install may fail due to network issues - retry with longer timeouts
- **SSL certificate issues**: Docker builds may encounter SSL errors - documented as known issue
- **Port conflicts**: Ensure ports 8000, 8001, 11434, 3000 are available

### Environment Configuration
- **API Keys**: At least one LLM provider key (OpenAI/Gemini) required for functionality
- **GitHub Token**: Required for private repositories, optional for public
- **Memory Usage**: Large models (especially with torch/transformers) require 4GB+ RAM
- **Docker Volumes**: Always run `./setup_chroma_persistence.sh` before first Docker run

### Common Failures and Solutions
- **"pip install fails"**: Use `pip install --timeout=300` and retry. Network/SSL issues are common.
- **"Docker build fails"**: Clear Docker cache with `docker system prune -f` and rebuild
- **"Application won't start"**: Check .env file has required API keys and run `./setup_chroma_persistence.sh`
- **"Tests fail"**: Ensure all dependencies installed with `pip install -r requirements-dev.txt`
- **"switch_models.py fails"**: Install dependencies first with `pip install -r requirements.txt`
- **"docker-helper.sh errors"**: Script expects `docker-compose` but system has `docker compose` - use docker compose commands directly

## Development Workflow
1. **Start services**: Use Docker Compose for full-stack development
2. **Make changes**: Edit files in `src/` directory  
3. **Test changes**: Run specific tests, then full test suite
4. **Code quality**: Run black, isort, flake8, mypy
5. **Manual validation**: Test API health, web UI, and end-to-end workflows
6. **Before committing**: Ensure all tests pass and code quality checks pass

## Comprehensive Functional Validation

**CRITICAL**: After any significant changes, perform this complete validation sequence:

```bash
# 1. Ensure services are running
docker compose ps
# All services should show "Up" status

# 2. Health checks
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

# 3. API documentation check
curl -s http://localhost:8000/docs | grep -q "swagger" && echo "API docs OK" || echo "API docs FAILED"

# 4. Web interface check (manual)
# Navigate to http://localhost:3000 and verify:
# - Page loads without errors
# - Sidebar is visible
# - Chat interface is functional
# - Repository URL input works

# 5. End-to-end repository processing
# Test with a small public repository:
curl -X POST "http://localhost:8000/index" \
     -H "Content-Type: application/json" \
     -d '{"repository_urls": ["https://github.com/octocat/Hello-World"], "branch": "main"}'

# Wait for indexing to complete, then query:
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"question": "What is this repository about?", "max_results": 3}'

# 6. Verify response quality
# Check that query returns meaningful results with relevant context
```

Always validate changes work end-to-end before considering them complete.

