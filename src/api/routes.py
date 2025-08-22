from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
from typing import Dict, Any, List, Optional

from .models import (
    QueryRequest, QueryResponse, IndexRequest, IndexResponse, 
    RepositoryInfo, HealthResponse
)
from ..config.settings import settings
from ..config.model_config import ModelConfiguration
from ..utils.logging import setup_logging, get_logger
from ..llm.llm_factory import LLMFactory
from ..llm.embedding_factory import EmbeddingFactory
from ..vectorstores.chroma_store import ChromaStore
from ..loaders.github_loader import GitHubLoader
from ..processors.text_processor import TextProcessor
from ..agents.rag_agent import RAGAgent
from langchain.docstore.document import Document

# Setup logging
setup_logging(settings.log_level)
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Base Agent API",
    description="API for indexing GitHub repositories and querying knowledge base",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
rag_agent = None
agent_router = None
github_loader = None
text_processor = None
indexed_repositories: Dict[str, RepositoryInfo] = {}

async def restore_indexed_repositories():
    """Restore indexed repositories information from the database"""
    global indexed_repositories
    try:
        if not rag_agent or not rag_agent.vectorstore:
            logger.warning("RAG agent not initialized, skipping restore")
            return
            
        logger.info("Restoring indexed repositories from database...")
        
        # Access the ChromaDB client through the vector store
        try:
            # For ChromaStore, we need to access the client differently
            if hasattr(rag_agent.vectorstore, 'client'):
                chroma_client = rag_agent.vectorstore.client
            elif hasattr(rag_agent.vectorstore, 'vector_store') and hasattr(rag_agent.vectorstore.vector_store, '_client'):
                chroma_client = rag_agent.vectorstore.vector_store._client
            else:
                logger.error("Cannot access ChromaDB client")
                return
        except Exception as e:
            logger.error(f"Failed to access ChromaDB client: {str(e)}")
            return
        
        # Get all unique repositories from the database
        collections = chroma_client.list_collections()
        
        if not collections:
            logger.info("No collections found in database")
            return
            
        logger.info(f"Found {len(collections)} collections in database")
        
        for collection in collections:
            try:
                # Get the collection
                coll = chroma_client.get_collection(collection.name)
                
                # Get all documents with metadata
                results = coll.get()
                
                if not results.get("documents") or not results.get("metadatas"):
                    continue
                    
                # Extract repositories from metadata
                repositories_in_collection = set()
                metadatas = results.get("metadatas", [])
                if metadatas:
                    for metadata in metadatas:
                        if metadata and "repository" in metadata:
                            repositories_in_collection.add(metadata["repository"])
                
                # For each repository, create a RepositoryInfo entry
                for repo_url in repositories_in_collection:
                    repo_id = repo_url.split("/")[-1]  # Extract repo name
                    
                    # Count documents for this repository
                    metadatas = results.get("metadatas", [])
                    repo_docs = [i for i, meta in enumerate(metadatas) 
                               if meta and meta.get("repository") == repo_url] if metadatas else []
                    
                    # Try to extract additional metadata from the first document
                    branch = "main"  # Default branch
                    last_indexed = datetime.now().isoformat()  # Default to now
                    original_files_count = len(repo_docs)  # Fallback to chunk count if original file count is unavailable
                    
                    if repo_docs and metadatas:
                        first_doc_meta = metadatas[repo_docs[0]]
                        if first_doc_meta:
                            branch = first_doc_meta.get("branch", "main")
                            last_indexed = first_doc_meta.get("indexed_at", datetime.now().isoformat())
                            # Try to get original file count from metadata
                            if "original_file_count" in first_doc_meta:
                                original_files_count = first_doc_meta["original_file_count"]
                    
                    indexed_repositories[repo_id] = RepositoryInfo(
                        id=repo_id,
                        url=repo_url,
                        name=repo_id,
                        description=f"Repository: {repo_url}",
                        branch=branch,
                        status="indexed",
                        documents_count=len(repo_docs),
                        original_files_count=original_files_count,
                        file_patterns=[f"*{ext}" for ext in settings.github_supported_file_extensions],
                        last_indexed=last_indexed,
                        error=None
                    )
                    
                    logger.info(f"Restored repository: {repo_url} with {len(repo_docs)} chunks")
                    
            except Exception as e:
                logger.error(f"Error processing collection {collection.name}: {str(e)}")
                continue
        
        logger.info(f"Successfully restored {len(indexed_repositories)} repositories")
        
    except Exception as e:
        logger.error(f"Error restoring indexed repositories: {str(e)}")

async def initialize_components():
    """Initialize components on startup with proper error handling"""
    global rag_agent, agent_router, github_loader, text_processor
    
    print("STARTUP DEBUG: Starting Knowledge Base Agent API...")
    logger.info("Starting Knowledge Base Agent API...")
    
    try:
        # Validate configuration first
        from ..config.model_config import ModelConfiguration
        
        print("STARTUP DEBUG: Validating configuration...")
        logger.info("Validating configuration...")
        llm_config = ModelConfiguration.validate_llm_config()
        embedding_config = ModelConfiguration.validate_embedding_config()
        
        if not llm_config["is_valid"]:
            logger.error(f"Invalid LLM configuration: {llm_config['error_message']}")
            raise ValueError(f"Invalid LLM configuration: {llm_config['error_message']}")
        
        if not embedding_config["is_valid"]:
            logger.error(f"Invalid embedding configuration: {embedding_config['error_message']}")
            raise ValueError(f"Invalid embedding configuration: {embedding_config['error_message']}")
        
        print("STARTUP DEBUG: Configuration validation passed")
        logger.info("Configuration validation passed")
        
        # Initialize embedding function with retry logic
        logger.info("Initializing embedding function...")
        embedding_provider = EmbeddingFactory._detect_provider_from_model(settings.embedding_model)
        if embedding_provider == "auto":
            embedding_provider = None  # Will use auto-detection
        
        max_retries = 3
        embedding_function = None
        for attempt in range(max_retries):
            try:
                embedding_function = EmbeddingFactory.create_embedding(
                    provider=embedding_provider, 
                    model=settings.embedding_model
                )
                logger.info(f"Embedding function initialized successfully on attempt {attempt + 1}")
                break
            except Exception as e:
                logger.warning(f"Embedding initialization attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Initialize vector store with retry logic
        logger.info("Initializing vector store...")
        vector_store = None
        for attempt in range(max_retries):
            try:
                vector_store = ChromaStore(
                    collection_name=settings.chroma_collection_name,
                    host=settings.chroma_host,
                    port=settings.chroma_port,
                    embedding_function=embedding_function
                )
                logger.info(f"Vector store initialized successfully on attempt {attempt + 1}")
                break
            except Exception as e:
                logger.warning(f"Vector store initialization attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    # Fallback to persistent store
                    logger.info("Falling back to persistent vector store...")
                    vector_store = ChromaStore(
                        collection_name=settings.chroma_collection_name,
                        host="localhost",  # This will trigger fallback to persistent client
                        port=8000,
                        embedding_function=embedding_function,
                        persist_directory="/app/chroma_db"  # Explicit persistent directory
                    )
                    break
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Initialize LLM with retry logic
        logger.info("Initializing LLM...")
        llm = None
        for attempt in range(max_retries):
            try:
                llm = LLMFactory.create_llm()
                logger.info(f"LLM initialized successfully on attempt {attempt + 1}")
                logger.info(f"Using LLM provider: {settings.llm_provider} with model: {settings.llm_model}")
                break
            except Exception as e:
                logger.warning(f"LLM initialization attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Initialize RAG agent
        logger.info("Initializing RAG agent...")
        rag_agent = RAGAgent(llm, vector_store)
        
        # Initialize diagram handler and agent router with dual agent support
        logger.info("Initializing diagram agents and router...")
        from ..processors.diagram_handler import DiagramHandler
        from ..agents.diagram_agent import DiagramAgent
        from ..agents.agent_router import AgentRouter
        from ..config.agent_config import AgentConfig, AGENT_CONFIG_PRESETS
        from ..agents.query_optimizer import AdvancedQueryOptimizer
        from ..agents.response_quality_enhancer import EnhancedResponseQualityEnhancer
        from ..config.query_optimization_config import DEFAULT_QUERY_OPTIMIZATION_CONFIG
        from ..config.response_quality_config import DEFAULT_RESPONSE_QUALITY_CONFIG
        
        # Initialize diagram handler (legacy support)
        diagram_handler = DiagramHandler(vector_store, llm)
        
        # Initialize agent configuration (use hybrid preset for backward compatibility)
        agent_config = AGENT_CONFIG_PRESETS.get("hybrid", AgentConfig())
        
        # Initialize enhanced components for DiagramAgent
        diagram_agent = None
        if agent_config.initialize_diagram_agent:
            try:
                logger.info("Initializing enhanced DiagramAgent...")
                
                # Initialize optional components safely
                query_optimizer = None
                response_enhancer = None
                
                try:
                    query_optimizer = AdvancedQueryOptimizer(llm, DEFAULT_QUERY_OPTIMIZATION_CONFIG.dict())
                    logger.debug("Query optimizer initialized")
                except Exception as e:
                    logger.warning(f"Query optimizer initialization failed: {str(e)}")
                
                try:
                    response_enhancer = EnhancedResponseQualityEnhancer(llm, DEFAULT_RESPONSE_QUALITY_CONFIG.dict())
                    logger.debug("Response enhancer initialized") 
                except Exception as e:
                    logger.warning(f"Response enhancer initialization failed: {str(e)}")
                
                # Initialize DiagramAgent with enhanced capabilities
                diagram_agent = DiagramAgent(
                    vectorstore=vector_store,
                    llm=llm,
                    query_optimizer=query_optimizer,
                    response_enhancer=response_enhancer
                )
                logger.info("DiagramAgent initialized successfully")
                
            except Exception as e:
                logger.warning(f"Failed to initialize DiagramAgent: {str(e)}")
                logger.warning("Continuing with DiagramHandler only")
                diagram_agent = None
        
        # Initialize agent router with dual agent support
        agent_router = AgentRouter(
            rag_agent=rag_agent,
            diagram_handler=diagram_handler,
            diagram_agent=diagram_agent,
            agent_config=agent_config
        )
        
        # Initialize other components
        logger.info("Initializing other components...")
        github_loader = GitHubLoader(settings.github_token or "")
        text_processor = TextProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            use_enhanced_chunking=settings.use_enhanced_chunking,
            chunking_config_path=settings.chunking_config_path
        )
        
        logger.info("Knowledge Base Agent API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize API: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        # Don't raise here - let the app start in a degraded state
        # The health check will reflect the actual status

# Add the startup event handler
@app.on_event("startup")
async def startup_event():
    """Handle startup event"""
    await initialize_components()
    await restore_indexed_repositories()

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Enhanced query endpoint with intelligent agent routing"""
    try:
        if not agent_router:
            raise HTTPException(status_code=500, detail="Agent router not initialized")
        
        # Use agent router to handle all query types
        result = agent_router.route_query(request.question)
        
        # Convert AgentResponse to QueryResponse format
        return QueryResponse(
            answer=result.answer,
            source_documents=result.source_documents,
            status=result.status.value,
            num_sources=result.num_sources,
            error=result.error,
            # Include extended fields if present (for diagram responses)
            mermaid_code=result.mermaid_code,
            diagram_type=result.diagram_type,
            # Include new enhancement fields for advanced RAG
            reasoning_steps=result.reasoning_steps,
            query_analysis=result.query_analysis,
            context_quality_score=result.context_quality_score,
            enhancement_iterations=result.enhancement_iterations
        )
    except Exception as e:
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index", response_model=IndexResponse)
async def index_repository(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index GitHub repositories"""
    try:
        if not rag_agent:
            raise HTTPException(status_code=500, detail="RAG agent not initialized")
        
        if not github_loader:
            raise HTTPException(status_code=500, detail="GitHub loader not initialized")
        
        if not text_processor:
            raise HTTPException(status_code=500, detail="Text processor not initialized")
        
        # Check if any repositories are already indexed
        already_indexed = []
        to_index = []
        
        for repo_url in request.repository_urls:
            repo_name = repo_url.split("/")[-1]
            if repo_name in indexed_repositories:
                already_indexed.append(repo_name)
            else:
                to_index.append(repo_url)
        
        if not to_index:
            return IndexResponse(
                message=f"All {len(already_indexed)} repositories are already indexed",
                status="already_indexed",
                repositories_processed=len(already_indexed),
                documents_indexed=0
            )
        
        # Generate task ID for tracking
        import uuid
        task_id = str(uuid.uuid4())
        
        # Start indexing in the background
        background_tasks.add_task(
            index_repositories_task,
            to_index,
            request.branch or "main",
            request.file_patterns,
            task_id
        )
        
        message = f"Started indexing {len(to_index)} repositories"
        if already_indexed:
            message += f" ({len(already_indexed)} already indexed)"
        
        return IndexResponse(
            message=message,
            status="indexing_started",
            repositories_processed=0,  # Will be updated when complete
            documents_indexed=0,       # Will be updated when complete
            task_id=task_id
        )
    except Exception as e:
        logger.error(f"Error starting repository indexing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def index_repositories_task(repo_urls: List[str], branch: str = "main", file_patterns: Optional[List[str]] = None, task_id: Optional[str] = None):
    """Background task to index multiple repositories"""
    total_documents = 0
    processed_repos = 0
    
    # Use comprehensive file patterns if none provided
    if not file_patterns:
        file_patterns = [f"*{ext}" for ext in settings.github_supported_file_extensions]
    
    for repo_url in repo_urls:
        try:
            await index_single_repository_task(repo_url, branch or "main", file_patterns)
            processed_repos += 1
            
            # Get document count for this repository
            repo_name = repo_url.split("/")[-1]
            if repo_name in indexed_repositories:
                total_documents += indexed_repositories[repo_name].documents_count
                
        except Exception as e:
            logger.error(f"Failed to index repository {repo_url}: {str(e)}")
            continue
    
    logger.info(f"Batch indexing completed: {processed_repos}/{len(repo_urls)} repositories, {total_documents} total documents")

async def index_single_repository_task(repo_url: str, branch: str = "main", file_patterns: Optional[List[str]] = None):
    """Background task to index a single repository"""
    repo_name = repo_url.split("/")[-1]
    
    try:
        # Create repository info entry
        indexed_repositories[repo_name] = RepositoryInfo(
            id=repo_name,
            url=repo_url,
            name=repo_name,
            description=f"Repository: {repo_url}",
            branch=branch,
            last_indexed=datetime.now().isoformat(),
            documents_count=0,
            original_files_count=0,
            file_patterns=[f"*{ext}" for ext in settings.github_supported_file_extensions],
            status="indexing"
        )
        
        logger.info(f"Starting indexing of repository: {repo_url}")
        
        # Load repository content
        if not github_loader:
            raise Exception("GitHub loader not initialized")
            
        # Convert settings extensions to file patterns
        default_patterns = [f"*{ext}" for ext in settings.github_supported_file_extensions]
        
        # Log the file patterns being used
        patterns_to_use = file_patterns or default_patterns
        logger.info(f"Using file patterns: {patterns_to_use}")
        
        documents = github_loader.load_repository(
            repo_url=repo_url,
            branch=branch,
            file_patterns=patterns_to_use
        )
        
        if not documents:
            indexed_repositories[repo_name].status = "failed"
            indexed_repositories[repo_name].error = "No documents found in repository"
            logger.error(f"No documents found in repository: {repo_url}")
            return
        
        # Log file type distribution for debugging
        file_types = {}
        for doc in documents:
            file_ext = doc.metadata.get("file_type", "unknown")
            file_types[file_ext] = file_types.get(file_ext, 0) + 1
        
        logger.info(f"File type distribution in {repo_url}: {file_types}")
        
        # Process documents
        if not text_processor:
            raise Exception("Text processor not initialized")
            
        # Add metadata to documents before processing
        for doc in documents:
            doc.metadata.update({
                "repository": repo_url,
                "branch": branch,
                "indexed_at": datetime.now().isoformat(),
                "original_file_count": len(documents)  # Store original file count
            })
        
        # Process and chunk the documents
        processed_docs = text_processor.process_documents(documents)
        
        # Add to vector store
        if not rag_agent:
            raise Exception("RAG agent not initialized")
            
        rag_agent.add_documents(processed_docs)
        
        # Update repository info
        indexed_repositories[repo_name].documents_count = len(processed_docs)  # Number of chunks
        indexed_repositories[repo_name].original_files_count = len(documents)  # Number of original files
        indexed_repositories[repo_name].status = "indexed"
        indexed_repositories[repo_name].last_indexed = datetime.now().isoformat()
        
        logger.info(f"Successfully indexed {len(processed_docs)} chunks from {len(documents)} files in {repo_url}")
        
    except Exception as e:
        logger.error(f"Error indexing repository {repo_url}: {str(e)}")
        if repo_name in indexed_repositories:
            indexed_repositories[repo_name].status = "failed"
            indexed_repositories[repo_name].error = str(e)

# Keep the old function for backward compatibility
async def index_repository_task(repo_url: str, branch: str = "main", file_patterns: Optional[List[str]] = None):
    """Background task to index a repository (legacy)"""
    return await index_single_repository_task(repo_url, branch, file_patterns)

@app.get("/repositories")
async def get_repositories():
    """Get all indexed repositories"""
    # If empty, try to restore from database
    if not indexed_repositories:
        await restore_indexed_repositories()
    
    # Add summary statistics
    total_files = sum(repo.original_files_count for repo in indexed_repositories.values())
    total_chunks = sum(repo.documents_count for repo in indexed_repositories.values())
    
    logger.info(f"Repository summary: {len(indexed_repositories)} repos, {total_files} files, {total_chunks} chunks")
    
    return list(indexed_repositories.values())

@app.delete("/repositories/{repository_id}")
async def delete_repository(repository_id: str):
    """Delete a repository from the index"""
    # This would require implementing document deletion by repository
    # For MVP, we'll return a simple response
    return {"message": f"Repository deletion not implemented in MVP", "repository_id": repository_id}


@app.post("/repositories/{repository_id}/reindex")
async def reindex_repository(repository_id: str):
    """Re-index a specific repository to update counts and metadata"""
    try:
        # Find the repository
        if repository_id not in indexed_repositories:
            return {"error": f"Repository {repository_id} not found"}
        
        repo_info = indexed_repositories[repository_id]
        repo_url = repo_info.url
        branch = repo_info.branch
        
        logger.info(f"Re-indexing repository: {repo_url}")
        
        # Start re-indexing in background
        await index_single_repository_task(repo_url, branch, repo_info.file_patterns)
        
        return {
            "message": f"Repository {repository_id} re-indexing started",
            "repository_id": repository_id,
            "status": "reindexing"
        }
        
    except Exception as e:
        logger.error(f"Failed to start re-indexing for {repository_id}: {str(e)}")
        return {"error": f"Failed to start re-indexing: {str(e)}"}


@app.post("/repositories/reindex-all")
async def reindex_all_repositories():
    """Re-index all repositories to update counts and metadata"""
    try:
        if not indexed_repositories:
            return {"error": "No repositories found to re-index"}
        
        repo_count = len(indexed_repositories)
        logger.info(f"Starting re-index of {repo_count} repositories")
        
        # Start re-indexing all repositories in background
        for repo_id, repo_info in indexed_repositories.items():
            try:
                await index_single_repository_task(repo_info.url, repo_info.branch, repo_info.file_patterns)
            except Exception as e:
                logger.error(f"Failed to re-index {repo_id}: {str(e)}")
                continue
        
        return {
            "message": f"Re-indexing started for {repo_count} repositories",
            "repositories_count": repo_count,
            "status": "reindexing"
        }
        
    except Exception as e:
        logger.error(f"Failed to start bulk re-indexing: {str(e)}")
        return {"error": f"Failed to start bulk re-indexing: {str(e)}"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with detailed component status"""
    try:
        components = {}
        
        # Check API status
        components["api"] = "healthy"
        
        # Check vector store
        if rag_agent and rag_agent.vectorstore:
            try:
                # Try to access the vector store
                collections = rag_agent.vectorstore.vector_store._client.list_collections()
                components["vector_store"] = "healthy"
            except Exception as e:
                components["vector_store"] = f"unhealthy: {str(e)}"
        else:
            components["vector_store"] = "not_initialized"
        
        # Check LLM
        if rag_agent and rag_agent.llm:
            components["llm"] = "healthy"
        else:
            components["llm"] = "not_initialized"
        
        # Check other components
        components["github_loader"] = "healthy" if github_loader else "not_initialized"
        components["text_processor"] = "healthy" if text_processor else "not_initialized"
        
        # Check configuration
        try:
            llm_config = ModelConfiguration.validate_llm_config()
            embedding_config = ModelConfiguration.validate_embedding_config()
            if llm_config["is_valid"] and embedding_config["is_valid"]:
                components["configuration"] = "healthy"
            else:
                components["configuration"] = "invalid"
        except Exception as e:
            components["configuration"] = f"error: {str(e)}"
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            components=components
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            version="1.0.0",
            components={"error": str(e)}
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Knowledge Base Agent API", "version": "1.0.0"}

@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "chroma_host": settings.chroma_host,
        "chroma_port": settings.chroma_port,
        "app_env": settings.app_env
    }

@app.get("/config/models")
async def get_available_models():
    """Get available models for current provider"""
    try:
        from ..config.model_config import ModelConfiguration
        
        llm_models = ModelConfiguration.get_llm_recommendations()
        embedding_models = ModelConfiguration.get_model_recommendations()
        
        return {
            "llm_models": llm_models,
            "embedding_models": embedding_models
        }
    except Exception as e:
        logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config/validate")
async def validate_config():
    """Validate current configuration"""
    try:
        from ..config.model_config import ModelConfiguration
        
        llm_config = ModelConfiguration.validate_llm_config()
        embedding_config = ModelConfiguration.validate_embedding_config()
        
        return {
            "llm_config": llm_config,
            "embedding_config": embedding_config,
            "overall_valid": llm_config["is_valid"] and embedding_config["is_valid"]
        }
    except Exception as e:
        logger.error(f"Error validating configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
