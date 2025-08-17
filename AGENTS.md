<general_rules>
Follow strict Python coding standards:
- Adhere to PEP 8 style guidelines with 79 character line limit
- Use 4-space indentation consistently
- Include comprehensive type hints for all function parameters and return values
- Write detailed docstrings following PEP 257 conventions for all classes and functions
- Prioritize code readability and maintainability over brevity

Enhanced chunking system usage:
- Before creating new chunkers, always search `src/processors/chunking/` directory to check if a suitable chunker already exists
- When extending chunking functionality, inherit from `BaseChunker` in `src/processors/chunking/base_chunker.py`
- Register new chunkers with the `ChunkingFactory` in `src/processors/chunking/chunking_factory.py`
- Respect language-specific semantic boundaries (classes, methods, functions) rather than arbitrary character limits

Model configuration and switching:
- Use `switch_models.py` script for changing LLM and embedding models rather than manually editing configuration files
- Test model switches with the validation utilities before deploying to production
- Ensure compatibility between LLM providers and embedding models when switching

Docker-first deployment approach:
- Prioritize Docker Compose setup for development and production environments
- Use `docker-helper.sh` for diagnosing Docker-related issues
- Ensure all services (ollama, chroma, web UI) are properly configured in docker-compose.yml
- Test containerized deployments with `verify_startup.py` health checks

Code quality and formatting:
- Run code quality tools from requirements-dev.txt before committing:
  * `black src/` for code formatting
  * `isort src/` for import sorting
  * `flake8 src/` for linting
  * `mypy src/` for type checking
- Install pre-commit hooks if available to automate quality checks
- Handle edge cases and write comprehensive exception handling
- Include meaningful error messages and logging statements
</general_rules>

<repository_structure>
The repository follows a modular architecture centered around the `src/` directory:

Core application modules:
- `src/agents/`: RAG agent implementations and routing logic
- `src/api/`: FastAPI routes, models, and REST API endpoints
- `src/config/`: Configuration management including model settings, chunking strategies, and application settings
- `src/llm/`: LLM provider implementations (OpenAI, Gemini, Azure OpenAI, Ollama) and embedding factories
- `src/loaders/`: Document loaders for GitHub repositories and other data sources
- `src/processors/`: Text processing and enhanced chunking system with language-specific parsers
- `src/utils/`: Utility functions for logging, model migration, and common operations
- `src/vectorstores/`: Vector database implementations (Chroma, pgvector) and base abstractions

Enhanced chunking system:
- `src/processors/chunking/`: Contains language-aware semantic chunkers (Python, C#, JavaScript, TypeScript)
- Includes fallback mechanisms and AST-based parsing for intelligent code segmentation
- Supports configurable chunking strategies per file type

Project context and documentation:
- `memory-bank/`: Project context storage including active context, progress tracking, and task management
- `docs/`: Technical documentation, implementation guides, and system architecture

Testing infrastructure:
- `tests/test_chunking/`: Comprehensive tests for the enhanced chunking system
- `tests/test_config.py`: Configuration validation tests
- `tests/test_diagram_features.py`: Agent routing and diagram generation tests

Key operational scripts:
- `setup.sh`: Environment initialization and dependency installation
- `switch_models.py`: Model configuration switching with validation and migration support
- `docker-helper.sh`: Docker deployment diagnostics and troubleshooting
- `verify_startup.py`: System health checks and startup validation
- `main.py`: Application entry point with FastAPI server configuration

Docker and deployment:
- `docker-compose.yml`: Multi-service setup with ollama, chroma, and web UI
- `Dockerfile`: Production-ready container configuration
- `entrypoint.sh`: Container startup script with health checks
</repository_structure>

<dependencies_and_installation>
Python environment requirements:
- Python 3.11+ is required for optimal compatibility
- Use pip for dependency management with two requirement files:
  * `requirements.txt`: Core application dependencies
  * `requirements-dev.txt`: Development tools (pytest, black, isort, flake8, mypy)

Installation methods:
- **Automated setup**: Run `./setup.sh` for complete environment initialization including virtual environment creation, dependency installation, and configuration file setup
- **Manual setup**: Create virtual environment, install from requirements.txt, and copy .env.example to .env
- **Docker setup**: Use `docker-compose up --build` for containerized deployment with all services

Service dependencies:
- **Chroma**: Vector database service running on port 8001 (mapped from container port 8000)
- **Ollama**: Local LLM service on port 11434 for open-source model support
- **Web UI**: Simple web interface on port 3000 for development and testing

Environment configuration:
- Copy `.env.example` to `.env` and configure API keys for chosen LLM providers
- Set `USE_ENHANCED_CHUNKING=true` to enable advanced semantic chunking
- Configure `GITHUB_TOKEN` for private repository access
- Adjust `CHUNK_SIZE`, `CHUNK_OVERLAP`, and model-specific settings as needed

Dependency management:
- Core dependencies include LangChain, FastAPI, ChromaDB, and provider-specific libraries
- Development dependencies focus on code quality (black, isort, flake8, mypy) and testing (pytest)
- Tree-sitter dependencies for advanced code parsing in the enhanced chunking system
</dependencies_and_installation>

<testing_instructions>
Testing framework and execution:
- Uses pytest as the primary testing framework
- Run all tests with `pytest tests/` from the repository root
- Install development dependencies with `pip install -r requirements-dev.txt` before running tests
- Use `pytest tests/ --verbose` for detailed test output

Primary testing focus areas:
- **Chunking system validation**: Comprehensive tests in `tests/test_chunking/` directory
  * `test_chunking_factory.py`: Factory pattern and chunker registration
  * `test_enhanced_validation.py`: Semantic chunking accuracy and metadata validation
  * `test_javascript_typescript_chunkers.py`: Language-specific chunker functionality
  * `test_parser_performance.py`: Performance benchmarks for AST parsing
- **Configuration validation**: Tests in `tests/test_config.py` for settings initialization and environment handling
- **Diagram features**: Tests in `tests/test_diagram_features.py` for agent routing and diagram generation

Testing best practices:
- Write unit tests for new chunkers, processors, and utility functions
- Include edge case testing for empty inputs, large files, and malformed data
- Test both successful operations and error handling paths
- Use meaningful test names that describe the expected behavior
- Include docstrings in test functions explaining the test scenario

Test environment setup:
- Tests may require environment variables for API keys (use test/mock values)
- Some tests require Docker services to be running (chroma, ollama)
- Use `verify_startup.py` to ensure all services are healthy before running integration tests
- Set `NO_COLOR=1` environment variable when running tests to avoid formatting issues in CI/CD
</testing_instructions>

<pull_request_formatting>
Use the structured template from `.github/pull_request_template.md` with the following required sections:

**Summary**: Brief description of the changes in this PR

**Type of Change** (check all that apply):
- [ ] Bug fix
- [ ] New feature
- [ ] Performance improvement
- [ ] Documentation/Tests

**Objective**: For new features and performance improvements, clearly describe the objective and rationale for this change

**Testing** (check all that apply):
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All existing tests pass

**Breaking Changes**:
- [ ] This PR contains breaking changes

If this is a breaking change, describe:
- What functionality is affected
- Migration path for existing users

**Checklist** (all items must be checked):
- [ ] Code follows project style guidelines (`make lint` passes)
- [ ] Self-review completed
- [ ] Documentation updated where necessary
- [ ] No secrets or sensitive information committed

**Related Issues**: Reference any related issues with "Closes #[issue number]"

Ensure all checklist items are completed before requesting review. The `make lint` reference should be interpreted as running the code quality tools (black, isort, flake8, mypy) mentioned in the general rules section.
</pull_request_formatting>
