# Knowledge Base Agent Implementation Guide

## Overview
This document outlines the implementation of an AI Agent with RAG (Retrieval-Augmented Generation) capabilities to index and query codebases from GitHub repositories, Microsoft SharePoint, and Lucid Chart diagrams. The agent will provide intelligent responses based on the indexed knowledge base.

## Requirements
- Load all settings from environment file (.env)
- Index all documents and files in GitHub Repository based on list of URLs provided
- Using Python language for AI Agent
- Using LangChain framework to build AI Agent
- Support multiple LLM models (OpenAI, Bedrock, Azure OpenAI...)
- Using vector database with Pinecone for local environment and pgvector for cloud

## Architecture Overview

### System Components
1. **Document Loaders**: Extract content from various sources (GitHub, SharePoint, Lucid Chart)
2. **Text Processors**: Clean, chunk, and prepare documents for vectorization
3. **Vector Store**: Store and retrieve document embeddings
4. **LLM Interface**: Handle queries and generate responses
5. **RAG Pipeline**: Orchestrate retrieval and generation processes
6. **API Layer**: Provide REST endpoints for interaction

### Data Flow
```
Data Sources → Document Loaders → Text Processing → Chunking → Embeddings → Vector Store
                                                                                    ↓
Query → Query Processing → Vector Retrieval → Context Assembly → LLM → Response
```

## Implementation Details

### 1. Project Structure
```
knowledge-base-agent/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   └── rag_agent.py
│   ├── loaders/
│   │   ├── __init__.py
│   │   ├── github_loader.py
│   │   ├── sharepoint_loader.py
│   │   └── lucid_chart_loader.py
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── text_processor.py
│   │   └── chunking_strategy.py
│   ├── vectorstores/
│   │   ├── __init__.py
│   │   ├── pinecone_store.py
│   │   └── pgvector_store.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── llm_factory.py
│   │   ├── openai_llm.py
│   │   ├── bedrock_llm.py
│   │   └── azure_openai_llm.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   └── api/
│       ├── __init__.py
│       ├── routes.py
│       └── models.py
├── tests/
├── docs/
├── requirements.txt
├── .env.example
├── .env
├── docker-compose.yml
└── main.py
```

### 2. Environment Configuration

#### .env Configuration
```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
BEDROCK_ACCESS_KEY=your_bedrock_access_key
BEDROCK_SECRET_KEY=your_bedrock_secret_key
BEDROCK_REGION=us-east-1

# Vector Database Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=knowledge-base-index

# PostgreSQL Configuration (for pgvector)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=knowledge_base
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# GitHub Configuration
GITHUB_TOKEN=your_github_token
GITHUB_REPOS=["https://github.com/user/repo1", "https://github.com/user/repo2"]

# SharePoint Configuration
SHAREPOINT_CLIENT_ID=your_sharepoint_client_id
SHAREPOINT_CLIENT_SECRET=your_sharepoint_client_secret
SHAREPOINT_TENANT_ID=your_tenant_id
SHAREPOINT_SITE_URL=https://yourcompany.sharepoint.com/sites/yoursite

# Lucid Chart Configuration
LUCID_CHART_API_KEY=your_lucid_chart_api_key
LUCID_CHART_CLIENT_ID=your_lucid_chart_client_id

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_TOKENS=4000
TEMPERATURE=0.7
```

### 3. Core Components Implementation

#### 3.1 Configuration Management
```python
# src/config/settings.py
from pydantic import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # LLM Settings
    openai_api_key: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    bedrock_access_key: Optional[str] = None
    bedrock_secret_key: Optional[str] = None
    bedrock_region: str = "us-east-1"
    
    # Vector Database Settings
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    pinecone_index_name: str = "knowledge-base-index"
    
    # PostgreSQL Settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "knowledge_base"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    
    # GitHub Settings
    github_token: Optional[str] = None
    github_repos: List[str] = []
    
    # SharePoint Settings
    sharepoint_client_id: Optional[str] = None
    sharepoint_client_secret: Optional[str] = None
    sharepoint_tenant_id: Optional[str] = None
    sharepoint_site_url: Optional[str] = None
    
    # Processing Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens: int = 4000
    temperature: float = 0.7
    
    class Config:
        env_file = ".env"
```

#### 3.2 Document Loaders
```python
# src/loaders/github_loader.py
from langchain.document_loaders import GitHubIssuesLoader
from langchain.document_loaders.generic import GenericLoader
from langchain.document_loaders.parsers import LanguageParser
from langchain.text_splitter import Language
from typing import List, Dict
import os

class GitHubLoader:
    def __init__(self, github_token: str):
        self.github_token = github_token
        
    def load_repository(self, repo_url: str) -> List[Dict]:
        """Load documents from GitHub repository"""
        # Clone repository temporarily
        clone_path = f"/tmp/{repo_url.split('/')[-1]}"
        os.system(f"git clone {repo_url} {clone_path}")
        
        # Load code files
        loader = GenericLoader.from_filesystem(
            clone_path,
            glob="**/*",
            suffixes=[".py", ".js", ".ts", ".java", ".cpp", ".c", ".h"],
            parser=LanguageParser(language=Language.PYTHON, parser_threshold=500)
        )
        
        documents = loader.load()
        
        # Clean up
        os.system(f"rm -rf {clone_path}")
        
        return documents
```

#### 3.3 Text Processing
```python
# src/processors/text_processor.py
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List

class TextProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Process and chunk documents"""
        processed_docs = []
        
        for doc in documents:
            # Clean text
            cleaned_text = self._clean_text(doc.page_content)
            doc.page_content = cleaned_text
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([doc])
            processed_docs.extend(chunks)
        
        return processed_docs
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove special characters that might interfere
        text = text.replace('\x00', '')
        
        return text
```

#### 3.4 Vector Store Interface
```python
# src/vectorstores/base_store.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain.schema import Document

class BaseVectorStore(ABC):
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        pass
    
    @abstractmethod
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        pass
    
    @abstractmethod
    def delete_documents(self, ids: List[str]) -> bool:
        pass
```

#### 3.5 RAG Agent
```python
# src/agents/rag_agent.py
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from typing import Dict, Any
import logging

class RAGAgent:
    def __init__(self, llm, vectorstore, retriever_kwargs=None):
        self.llm = llm
        self.vectorstore = vectorstore
        self.retriever_kwargs = retriever_kwargs or {"k": 5}
        self.qa_chain = self._create_qa_chain()
        
    def _create_qa_chain(self):
        """Create the QA chain with custom prompt"""
        prompt_template = """
        You are a helpful AI assistant that answers questions based on the provided context from code repositories, documentation, and diagrams.
        
        Context: {context}
        
        Question: {question}
        
        Please provide a detailed and accurate answer based on the context. If you cannot find the answer in the context, please say so.
        
        Answer:
        """
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        return RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(**self.retriever_kwargs),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt}
        )
    
    def query(self, question: str) -> Dict[str, Any]:
        """Query the knowledge base"""
        try:
            result = self.qa_chain({"query": question})
            return {
                "answer": result["result"],
                "source_documents": result["source_documents"],
                "status": "success"
            }
        except Exception as e:
            logging.error(f"Query failed: {e}")
            return {
                "answer": "I encountered an error while processing your query.",
                "source_documents": [],
                "status": "error",
                "error": str(e)
            }
```

### 4. API Layer
```python
# src/api/routes.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

app = FastAPI(title="Knowledge Base Agent API")

class QueryRequest(BaseModel):
    question: str
    max_results: Optional[int] = 5

class IndexRequest(BaseModel):
    sources: List[str]
    source_type: str  # "github", "sharepoint", "lucid_chart"

@app.post("/query")
async def query_knowledge_base(request: QueryRequest):
    """Query the knowledge base"""
    try:
        result = rag_agent.query(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
async def index_documents(request: IndexRequest, background_tasks: BackgroundTasks):
    """Index documents from specified sources"""
    background_tasks.add_task(index_documents_task, request.sources, request.source_type)
    return {"message": "Indexing started", "status": "processing"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
```

### 5. Deployment Configuration

#### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY main.py .

EXPOSE 8000

CMD ["python", "main.py"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  knowledge-base-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
    env_file:
      - .env
    depends_on:
      - postgres
      - redis

  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: knowledge_base
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### 6. Testing Strategy

#### Unit Tests
```python
# tests/test_rag_agent.py
import pytest
from unittest.mock import Mock, patch
from src.agents.rag_agent import RAGAgent

class TestRAGAgent:
    def test_query_success(self):
        # Mock dependencies
        mock_llm = Mock()
        mock_vectorstore = Mock()
        
        agent = RAGAgent(mock_llm, mock_vectorstore)
        
        # Test query
        result = agent.query("What is the main function?")
        
        assert result["status"] == "success"
        assert "answer" in result
```

#### Integration Tests
```python
# tests/test_integration.py
import pytest
from src.agents.rag_agent import RAGAgent
from src.vectorstores.pinecone_store import PineconeStore
from src.llm.openai_llm import OpenAILLM

class TestIntegration:
    @pytest.mark.integration
    def test_end_to_end_flow(self):
        # Test complete flow from document loading to querying
        pass
```

### 7. Monitoring and Logging

#### Logging Configuration
```python
# src/utils/logging.py
import logging
import sys
from datetime import datetime

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('knowledge_base_agent.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
```

### 8. Security Best Practices

#### API Security
- Implement API key authentication
- Rate limiting for API endpoints
- Input validation and sanitization
- HTTPS encryption in production

#### Data Security
- Encrypt sensitive data at rest
- Secure API key management
- Regular security audits
- Access control and permissions

### 9. Performance Optimization

#### Caching Strategy
- Cache frequent queries using Redis
- Implement vector similarity caching
- Document-level caching for large repositories

#### Scaling Considerations
- Horizontal scaling with load balancers
- Database connection pooling
- Async processing for document indexing
- Memory management for large documents

### 10. Maintenance and Updates

#### Regular Tasks
- Update vector embeddings for changed documents
- Monitor index performance and optimize
- Update LLM models and embeddings
- Clean up obsolete documents

#### Version Management
- Semantic versioning for API changes
- Database migration scripts
- Configuration versioning
- Rollback procedures

## Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd knowledge-base-agent
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Index your first repository**
   ```bash
   curl -X POST "http://localhost:8000/index" \
        -H "Content-Type: application/json" \
        -d '{"sources": ["https://github.com/user/repo"], "source_type": "github"}'
   ```

6. **Query the knowledge base**
   ```bash
   curl -X POST "http://localhost:8000/query" \
        -H "Content-Type: application/json" \
        -d '{"question": "What is the main function of this codebase?"}'
   ```

This implementation provides a robust, scalable, and maintainable AI Agent with RAG capabilities that can index and query multiple knowledge sources effectively.
