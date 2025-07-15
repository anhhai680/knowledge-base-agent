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
from ..utils.logging import setup_logging, get_logger
from ..llm.llm_factory import LLMFactory
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
    """Initialize components on startup"""
    global rag_agent, github_loader, text_processor
    
    logger.info("Starting Knowledge Base Agent API...")
    
    try:
        # Initialize vector store
        vector_store = ChromaStore(
            collection_name=settings.chroma_collection_name,
            host=settings.chroma_host,
            port=settings.chroma_port
        )
        
        # Initialize LLM
        llm_config = {
            "openai_api_key": settings.openai_api_key,
            "gemini_api_key": settings.gemini_api_key,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens
        }
        
        provider = LLMFactory.get_available_provider(llm_config)
        if not provider:
            raise ValueError("No LLM provider available. Please configure API keys.")
        
        llm = LLMFactory.create_llm(provider, llm_config)
        logger.info(f"Using LLM provider: {provider}")
        
        # Initialize RAG agent
        rag_agent = RAGAgent(llm, vector_store)
        
        # Initialize other components
        github_loader = GitHubLoader(settings.github_token)
        text_processor = TextProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
        
        logger.info("Knowledge Base Agent API started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize API: {str(e)}")
        raise

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
            request.branch,
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
    logger.info(f"Starting indexing task {task_id} for {len(repository_urls)} repositories")
    
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
    """Health check endpoint"""
    components = {}
    
    try:
        # Check vector store
        if rag_agent:
            collection_info = rag_agent.get_collection_info()
            components["vector_store"] = "healthy" if "error" not in collection_info else "unhealthy"
        else:
            components["vector_store"] = "not_initialized"
        
        # Check LLM (basic check)
        components["llm"] = "healthy" if rag_agent else "not_initialized"
        
        # Check GitHub loader
        components["github_loader"] = "healthy" if github_loader else "not_initialized"
        
        overall_status = "healthy" if all(status == "healthy" for status in components.values()) else "unhealthy"
        
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
