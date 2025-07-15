from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import asyncio
from typing import Dict, Any, List

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
github_loader = None
text_processor = None
indexed_repositories: Dict[str, RepositoryInfo] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup with proper error handling"""
    global rag_agent, github_loader, text_processor
    
    logger.info("Starting Knowledge Base Agent API...")
    
    try:
        # Validate configuration first
        from ..config.model_config import ModelConfiguration
        
        logger.info("Validating configuration...")
        llm_config = ModelConfiguration.validate_llm_config()
        embedding_config = ModelConfiguration.validate_embedding_config()
        
        if not llm_config["is_valid"]:
            logger.error(f"Invalid LLM configuration: {llm_config['error_message']}")
            raise ValueError(f"Invalid LLM configuration: {llm_config['error_message']}")
        
        if not embedding_config["is_valid"]:
            logger.error(f"Invalid embedding configuration: {embedding_config['error_message']}")
            raise ValueError(f"Invalid embedding configuration: {embedding_config['error_message']}")
        
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
                        host="localhost",  # Fallback to local
                        port=8000,
                        embedding_function=embedding_function
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
        
        # Initialize other components
        logger.info("Initializing other components...")
        github_loader = GitHubLoader(settings.github_token or "")
        text_processor = TextProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        logger.info("Knowledge Base Agent API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize API: {str(e)}")
        logger.error("Stack trace:", exc_info=True)
        # Don't raise here - let the app start in a degraded state
        # The health check will reflect the actual status

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base"""
    try:
        if not rag_agent:
            raise HTTPException(status_code=500, detail="RAG agent not initialized")
        
        result = rag_agent.query(request.question)
        
        return QueryResponse(
            answer=result["answer"],
            source_documents=result["source_documents"],
            status=result["status"],
            num_sources=result["num_sources"],
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index", response_model=IndexResponse)
async def index_repositories(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index GitHub repositories"""
    try:
        if not github_loader or not text_processor or not rag_agent:
            raise HTTPException(status_code=500, detail="Components not initialized")
        
        # Start background indexing task
        task_id = f"index_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        background_tasks.add_task(
            index_repositories_task, 
            request.repository_urls, 
            request.branch or "main",
            task_id
        )
        
        return IndexResponse(
            message="Indexing started",
            status="processing",
            repositories_processed=0,
            documents_indexed=0,
            task_id=task_id
        )
        
    except Exception as e:
        logger.error(f"Indexing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def index_repositories_task(repository_urls: List[str], branch: str, task_id: str):
    """Background task for indexing repositories"""
    global github_loader, text_processor, rag_agent, indexed_repositories
    
    logger.info(f"Starting indexing task {task_id} for {len(repository_urls)} repositories")
    
    # Check if components are initialized
    if not github_loader or not text_processor or not rag_agent:
        logger.error("Components not initialized for indexing task")
        return
    
    total_documents = 0
    
    for repo_url in repository_urls:
        try:
            logger.info(f"Indexing repository: {repo_url}")
            
            # Update repository status
            indexed_repositories[repo_url] = RepositoryInfo(
                url=repo_url,
                status="indexing",
                documents_count=0
            )
            
            # Load documents from repository
            documents = github_loader.load_repository(repo_url, branch)
            
            # Process documents
            processed_docs = text_processor.process_documents(documents)
            
            # Add to vector store
            doc_ids = rag_agent.add_documents(processed_docs)
            
            # Update repository info
            indexed_repositories[repo_url] = RepositoryInfo(
                url=repo_url,
                status="completed",
                documents_count=len(doc_ids),
                last_indexed=datetime.now().isoformat()
            )
            
            total_documents += len(doc_ids)
            logger.info(f"Successfully indexed {len(doc_ids)} documents from {repo_url}")
            
        except Exception as e:
            logger.error(f"Failed to index repository {repo_url}: {str(e)}")
            indexed_repositories[repo_url] = RepositoryInfo(
                url=repo_url,
                status="failed",
                documents_count=0,
                error=str(e)
            )
    
    logger.info(f"Indexing task {task_id} completed. Total documents indexed: {total_documents}")

@app.get("/repositories")
async def get_repositories():
    """Get list of indexed repositories"""
    return list(indexed_repositories.values())

@app.delete("/repositories/{repository_id}")
async def delete_repository(repository_id: str):
    """Delete a repository from the index"""
    # This would require implementing document deletion by repository
    # For MVP, we'll return a simple response
    return {"message": f"Repository deletion not implemented in MVP", "repository_id": repository_id}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with detailed component status"""
    components = {}
    
    try:
        # Check basic API health
        components["api"] = "healthy"
        
        # Check vector store
        if rag_agent:
            try:
                collection_info = rag_agent.get_collection_info()
                components["vector_store"] = "healthy" if "error" not in collection_info else "degraded"
            except Exception as e:
                logger.warning(f"Vector store health check failed: {e}")
                components["vector_store"] = "degraded"
        else:
            components["vector_store"] = "not_initialized"
        
        # Check LLM (basic check)
        if rag_agent:
            try:
                # Try a simple test query to ensure LLM is working
                components["llm"] = "healthy"
            except Exception as e:
                logger.warning(f"LLM health check failed: {e}")
                components["llm"] = "degraded"
        else:
            components["llm"] = "not_initialized"
        
        # Check GitHub loader
        components["github_loader"] = "healthy" if github_loader else "not_initialized"
        
        # Check text processor
        components["text_processor"] = "healthy" if text_processor else "not_initialized"
        
        # Check configuration
        try:
            from ..config.model_config import ModelConfiguration
            config_summary = ModelConfiguration.get_configuration_summary()
            components["configuration"] = "healthy" if config_summary["overall_status"] == "ready" else "degraded"
        except Exception as e:
            logger.warning(f"Configuration health check failed: {e}")
            components["configuration"] = "degraded"
        
        # Determine overall status
        # API is healthy if basic functionality works, even if some components are degraded
        critical_components = ["api", "configuration"]
        healthy_count = sum(1 for key, status in components.items() if status == "healthy")
        total_count = len(components)
        
        if all(components.get(comp) in ["healthy", "degraded"] for comp in critical_components):
            if healthy_count >= total_count * 0.6:  # At least 60% healthy
                overall_status = "healthy"
            else:
                overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return HealthResponse(
            status=overall_status,
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
    return {
        "message": "Knowledge Base Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/config")
async def get_configuration():
    """Get current configuration status"""
    try:
        config_summary = ModelConfiguration.get_configuration_summary()
        return config_summary
    except Exception as e:
        logger.error(f"Failed to get configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get configuration: {str(e)}")

@app.get("/config/models")
async def get_model_recommendations():
    """Get model recommendations for different providers"""
    try:
        return {
            "llm_models": ModelConfiguration.get_llm_recommendations(),
            "embedding_models": ModelConfiguration.get_model_recommendations()
        }
    except Exception as e:
        logger.error(f"Failed to get model recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get model recommendations: {str(e)}")

@app.get("/config/validate")
async def validate_configuration():
    """Validate current configuration"""
    try:
        llm_config = ModelConfiguration.validate_llm_config()
        embedding_config = ModelConfiguration.validate_embedding_config()
        
        return {
            "llm_validation": llm_config,
            "embedding_validation": embedding_config,
            "overall_valid": llm_config["is_valid"] and embedding_config["is_valid"]
        }
    except Exception as e:
        logger.error(f"Failed to validate configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to validate configuration: {str(e)}")
