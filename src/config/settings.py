from pydantic_settings import BaseSettings
from pydantic import validator
from typing import List, Optional
import os
from pathlib import Path

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
    github_repos: List[str] = []
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

    # LangGraph Configuration
    enable_langgraph: bool = False  # Will be overridden by ENABLE_LANGGRAPH env var
    langgraph_default_system: str = "auto"  # Options: langchain, langgraph, auto
    langgraph_migration_rollout: float = 0.0  # Percentage of traffic to route to LangGraph (0.0 to 1.0)
    langgraph_enable_ab_testing: bool = False  # Enable A/B testing between systems
    
    @validator('llm_provider', 'llm_model', 'embedding_model', pre=True)
    def strip_comments(cls, v):
        """Strip inline comments from string values"""
        if isinstance(v, str):
            # Split on # and take the first part, then strip whitespace
            return v.split('#')[0].strip()
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = Settings()

# Debug: Print environment variable values after loading
print(f"🔧 Settings loaded - ENABLE_LANGGRAPH: {os.getenv('ENABLE_LANGGRAPH', 'NOT_SET')}")
print(f"🔧 Settings loaded - settings.enable_langgraph: {settings.enable_langgraph}")

# Container-specific environment variable handling
def get_container_env_var(var_name: str, default: str = None) -> str:
    """Get environment variable with container-specific fallbacks"""
    # Try direct environment variable first
    value = os.getenv(var_name)
    if value is not None:
        return value
    
    # Try with different casing (some containers are case-sensitive)
    value = os.getenv(var_name.upper())
    if value is not None:
        return value
    
    # Try with different casing
    value = os.getenv(var_name.lower())
    if value is not None:
        return value
    
    # Return default if nothing found
    return default

# Override settings if environment variables are set
if get_container_env_var('ENABLE_LANGGRAPH'):
    settings.enable_langgraph = get_container_env_var('ENABLE_LANGGRAPH', 'false').lower() == 'true'
    print(f"🔧 Override: settings.enable_langgraph = {settings.enable_langgraph}")

if get_container_env_var('LANGGRAPH_DEFAULT_SYSTEM'):
    settings.langgraph_default_system = get_container_env_var('LANGGRAPH_DEFAULT_SYSTEM', 'auto')
    print(f"🔧 Override: settings.langgraph_default_system = {settings.langgraph_default_system}")

if get_container_env_var('LANGGRAPH_MIGRATION_ROLLOUT'):
    try:
        settings.langgraph_migration_rollout = float(get_container_env_var('LANGGRAPH_MIGRATION_ROLLOUT', '0.0'))
        print(f"🔧 Override: settings.langgraph_migration_rollout = {settings.langgraph_migration_rollout}")
    except ValueError:
        print(f"⚠️ Invalid LANGGRAPH_MIGRATION_ROLLOUT value: {get_container_env_var('LANGGRAPH_MIGRATION_ROLLOUT')}")

if get_container_env_var('LANGGRAPH_ENABLE_AB_TESTING'):
    settings.langgraph_enable_ab_testing = get_container_env_var('LANGGRAPH_ENABLE_AB_TESTING', 'false').lower() == 'true'
    print(f"🔧 Override: settings.langgraph_enable_ab_testing = {settings.langgraph_enable_ab_testing}")
