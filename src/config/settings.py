from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = "openai"  # Options: openai, gemini, azure_openai, ollama
    llm_model: str = "gpt-3.5-turbo"  # Model name for the chosen provider
    llm_api_base_url: Optional[str] = None  # Base URL for LLM API (useful for ollama)
    
    # Embedding Configuration
    embedding_model: str = "text-embedding-ada-002"  # Embedding model name
    embedding_api_base_url: Optional[str] = None  # Base URL for embedding API
    
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
    github_repos: List[str] = []
    
    # Processing Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_tokens: int = 4000
    temperature: float = 0.7
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Application Settings
    app_env: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

# Global settings instance
settings = Settings()
