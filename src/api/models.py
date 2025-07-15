from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class QueryRequest(BaseModel):
    question: str
    max_results: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    source_documents: List[Dict[str, Any]]
    status: str
    num_sources: int
    error: Optional[str] = None

class IndexRequest(BaseModel):
    repository_urls: List[str]
    branch: Optional[str] = "main"

class IndexResponse(BaseModel):
    message: str
    status: str
    repositories_processed: int
    documents_indexed: int
    task_id: Optional[str] = None

class RepositoryInfo(BaseModel):
    url: str
    status: str
    documents_count: int
    last_indexed: Optional[str] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    components: Dict[str, str]
