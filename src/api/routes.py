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
                    
                    indexed_repositories[repo_id] = RepositoryInfo(
                        url=repo_url,
                        status="indexed",
                        documents_count=len(repo_docs),
                        last_indexed=datetime.now().isoformat(),
                        error=None
                    )
                    
                    logger.info(f"Restored repository: {repo_url} with {len(repo_docs)} documents")
                    
            except Exception as e:
                logger.error(f"Error processing collection {collection.name}: {str(e)}")
                continue
        
        logger.info(f"Successfully restored {len(indexed_repositories)} repositories")
        
    except Exception as e:
        logger.error(f"Error restoring indexed repositories: {str(e)}")

async def initialize_components():
    """Initialize components on startup with proper error handling"""
    global rag_agent, github_loader, text_processor
    
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

# Add the startup event handler
@app.on_event("startup")
async def startup_event():
    """Handle startup event"""
    await initialize_components()
    await restore_indexed_repositories()

@app.get("/manual-restore")
async def manual_restore():
    """Manual endpoint to trigger repository restoration"""
    try:
        await restore_indexed_repositories()
        return {
            "message": "Repository restoration completed",
            "repositories_found": len(indexed_repositories),
            "repositories": list(indexed_repositories.keys())
        }
    except Exception as e:
        return {"error": str(e)}

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
        logger.error(f"Error querying knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index", response_model=IndexResponse)
async def index_repository(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index a GitHub repository"""
    try:
        if not rag_agent:
            raise HTTPException(status_code=500, detail="RAG agent not initialized")
        
        if not github_loader:
            raise HTTPException(status_code=500, detail="GitHub loader not initialized")
        
        if not text_processor:
            raise HTTPException(status_code=500, detail="Text processor not initialized")
        
        # Check if repository is already indexed
        repo_name = request.repo_url.split("/")[-1]
        if repo_name in indexed_repositories:
            return IndexResponse(
                message=f"Repository '{repo_name}' is already indexed",
                status="already_indexed",
                repository_id=repo_name
            )
        
        # Start indexing in the background
        background_tasks.add_task(
            index_repository_task,
            request.repo_url,
            request.branch,
            request.file_patterns
        )
        
        return IndexResponse(
            message=f"Started indexing repository: {request.repo_url}",
            status="indexing_started",
            repository_id=repo_name
        )
    except Exception as e:
        logger.error(f"Error starting repository indexing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def index_repository_task(repo_url: str, branch: str = "main", file_patterns: List[str] = None):
    """Background task to index a repository"""
    repo_name = repo_url.split("/")[-1]
    
    try:
        # Create repository info entry
        indexed_repositories[repo_name] = RepositoryInfo(
            id=repo_name,
            url=repo_url,
            name=repo_name,
            description=f"Repository: {repo_url}",
            branch=branch,
            last_indexed=datetime.now(),
            document_count=0,
            status="indexing"
        )
        
        logger.info(f"Starting indexing of repository: {repo_url}")
        
        # Load repository content
        documents = await github_loader.load_repository(
            repo_url=repo_url,
            branch=branch,
            file_patterns=file_patterns or ["*.py", "*.js", "*.ts", "*.md", "*.txt"]
        )
        
        if not documents:
            indexed_repositories[repo_name].status = "failed"
            logger.error(f"No documents found in repository: {repo_url}")
            return
        
        # Process documents
        processed_docs = []
        for doc in documents:
            # Add metadata
            doc.metadata.update({
                "repository": repo_url,
                "branch": branch,
                "indexed_at": datetime.now().isoformat()
            })
            
            # Process and chunk the document
            chunks = text_processor.process_document(doc)
            processed_docs.extend(chunks)
        
        # Add to vector store
        await rag_agent.add_documents(processed_docs)
        
        # Update repository info
        indexed_repositories[repo_name].document_count = len(processed_docs)
        indexed_repositories[repo_name].status = "indexed"
        indexed_repositories[repo_name].last_indexed = datetime.now()
        
        logger.info(f"Successfully indexed {len(processed_docs)} documents from {repo_url}")
        
    except Exception as e:
        logger.error(f"Error indexing repository {repo_url}: {str(e)}")
        if repo_name in indexed_repositories:
            indexed_repositories[repo_name].status = "failed"

@app.get("/repositories")
async def get_repositories():
    """Get all indexed repositories"""
    # If empty, try to restore from database
    if not indexed_repositories:
        await restore_indexed_repositories()
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
        
        available_models = ModelConfiguration.get_available_models()
        return {
            "llm_models": available_models["llm"],
            "embedding_models": available_models["embedding"]
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
