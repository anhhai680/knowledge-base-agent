from pydantic_settings import BaseSettings
from pydantic import validator, Field
from typing import List, Optional
import os
import json

def parse_github_repos(value: str) -> List[str]:
    """Parse GITHUB_REPOS value, supporting both JSON and comma-separated formats"""
    if not value:
        return []
    
    try:
        # Try to parse as JSON first
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Fall back to comma-separated format
    if ',' in value:
        return [repo.strip() for repo in value.split(',') if repo.strip()]
    elif value.strip():
        return [value.strip()]
    else:
        return []

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = "openai"  # Options: openai, gemini, azure_openai, ollama
    llm_model: str = "gpt-3.5-turbo"  # Model name for the chosen provider
    llm_api_base_url: Optional[str] = None  # Base URL for LLM API (useful for ollama)
    
    # Embedding Configuration
    embedding_model: str = "text-embedding-ada-002"  # Embedding model name
    embedding_api_base_url: Optional[str] = None  # Base URL for embedding API
    embedding_api_key: Optional[str] = None
    
    # API Keys
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    
    # Vector Database Settings
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection_name: str = "knowledge-base-collection"
    
    # PostgreSQL Settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "knowledge_base"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    
    # GitHub Settings
    github_token: Optional[str] = None
    github_repos: List[str] = Field(default_factory=list, description="GitHub repositories to index")
    github_branch: List[str] = ["main", "master"]
    github_supported_file_extensions: List[str] = [
        ".cs", ".py", ".sh", ".js", ".jsx", ".ts", ".tsx", ".md", 
        ".txt", ".json", ".yml", ".yaml"
    ]
    
    # Processing Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # Embedding Batch Processing Settings
    embedding_batch_size: int = 50  # Default batch size for embedding requests
    max_tokens_per_batch: int = 250000  # Conservative token limit per batch
    
    # Enhanced Chunking Settings
    use_enhanced_chunking: bool = True
    use_advanced_parsing: bool = True
    chunking_config_path: Optional[str] = None
    
    # File-Type-Aware Embedding Settings
    use_file_type_aware_embeddings: bool = False  # Disabled to prevent dimension mismatches
    # Removed redundant model settings - using main embedding_model for all file types
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Application Settings
    app_env: str = "development"
    log_level: str = "INFO"
    
    @validator('llm_provider', 'llm_model', 'embedding_model', pre=True)
    def strip_comments(cls, v):
        """Strip inline comments from string values"""
        if isinstance(v, str):
            # Split on # and take the first part, then strip whitespace
            return v.split('#')[0].strip()
        return v
    
    @validator('github_repos', pre=True)
    def parse_github_repos_validator(cls, v):
        """Parse GITHUB_REPOS from environment variable, supporting both JSON and comma-separated formats"""
        if isinstance(v, str):
            return parse_github_repos(v)
        return v
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()
