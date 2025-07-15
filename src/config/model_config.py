"""
Configuration utility for LLM and embedding models
"""

from typing import Dict, Any, Optional, List
from ..config.settings import settings
from ..llm.llm_factory import LLMFactory
from ..llm.embedding_factory import EmbeddingFactory
from ..utils.logging import get_logger

logger = get_logger(__name__)

class ModelConfiguration:
    """Utility class for managing model configurations"""
    
    # Known embedding dimensions for different models
    EMBEDDING_DIMENSIONS = {
        # OpenAI
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        
        # Gemini
        "models/embedding-001": 768,
        
        # Ollama common models
        "nomic-embed-text": 768,
        "all-minilm": 384,
        "mxbai-embed-large": 1024,
        
        # HuggingFace
        "sentence-transformers/all-MiniLM-L6-v2": 384,
        "sentence-transformers/all-mpnet-base-v2": 768,
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": 384,
    }
    
    @staticmethod
    def get_embedding_dimension(model_name: str) -> Optional[int]:
        """
        Get the embedding dimension for a model
        
        Args:
            model_name: Name of the embedding model
            
        Returns:
            Integer dimension or None if unknown
        """
        return ModelConfiguration.EMBEDDING_DIMENSIONS.get(model_name)
    
    @staticmethod
    def detect_embedding_dimension(embedding_function=None) -> Optional[int]:
        """
        Detect embedding dimension by running a test embedding
        
        Args:
            embedding_function: Optional embedding function to test
            
        Returns:
            Integer dimension or None if detection fails
        """
        try:
            if embedding_function is None:
                embedding_function = EmbeddingFactory.create_embedding()
            
            # Test with a simple text
            test_embedding = embedding_function.embed_query("test")
            dimension = len(test_embedding)
            logger.info(f"Detected embedding dimension: {dimension}")
            return dimension
            
        except Exception as e:
            logger.error(f"Failed to detect embedding dimension: {e}")
            return None
    
    @staticmethod
    def check_dimension_compatibility(current_model: str, new_model: str) -> bool:
        """
        Check if two models have compatible embedding dimensions
        
        Args:
            current_model: Current embedding model
            new_model: New embedding model to switch to
            
        Returns:
            True if compatible, False otherwise
        """
        current_dim = ModelConfiguration.get_embedding_dimension(current_model)
        new_dim = ModelConfiguration.get_embedding_dimension(new_model)
        
        if current_dim is None or new_dim is None:
            # If we can't determine dimensions, assume incompatible for safety
            logger.warning(f"Cannot determine dimensions for {current_model} and/or {new_model}")
            return False
            
        return current_dim == new_dim
    
    @staticmethod
    def get_collection_metadata(embedding_model: str) -> Dict[str, Any]:
        """
        Get metadata for a collection based on embedding model
        
        Args:
            embedding_model: Name of the embedding model
            
        Returns:
            Dictionary with collection metadata
        """
        provider = EmbeddingFactory._detect_provider_from_model(embedding_model)
        dimension = ModelConfiguration.get_embedding_dimension(embedding_model)
        
        return {
            "embedding_model": embedding_model,
            "embedding_provider": provider,
            "embedding_dimension": dimension,
            "created_at": str(settings.app_env),
            "version": "1.0"
        }
    
    @staticmethod
    def validate_llm_config() -> Dict[str, Any]:
        """
        Validate and return LLM configuration
        
        Returns:
            Dict containing validation results and configuration
        """
        config = {
            "provider": settings.llm_provider,
            "model": settings.llm_model,
            "api_base_url": settings.llm_api_base_url,
            "is_valid": False,
            "error_message": None,
            "available_providers": LLMFactory.get_supported_providers()
        }
        
        try:
            # Check if required credentials are available
            if settings.llm_provider == "openai" and not settings.openai_api_key:
                config["error_message"] = "OpenAI API key is required for OpenAI provider"
            elif settings.llm_provider == "gemini" and not settings.gemini_api_key:
                config["error_message"] = "Gemini API key is required for Gemini provider"
            elif settings.llm_provider == "azure_openai" and (not settings.azure_openai_api_key or not settings.azure_openai_endpoint):
                config["error_message"] = "Azure OpenAI API key and endpoint are required for Azure OpenAI provider"
            elif settings.llm_provider == "ollama":
                # Ollama doesn't require API key, just validate base URL if provided
                if settings.llm_api_base_url:
                    config["api_base_url"] = settings.llm_api_base_url
                else:
                    config["api_base_url"] = "http://localhost:11434/v1"
                config["is_valid"] = True
            else:
                # Try to get available provider as fallback
                available_provider = LLMFactory.get_available_provider()
                if available_provider:
                    config["provider"] = available_provider
                    config["is_valid"] = True
                    config["error_message"] = f"Using available provider: {available_provider}"
                else:
                    config["error_message"] = "No valid LLM provider configuration found"
            
            if not config["error_message"]:
                config["is_valid"] = True
                
        except Exception as e:
            config["error_message"] = f"Configuration validation failed: {str(e)}"
            logger.error(f"LLM configuration validation error: {e}")
        
        return config
    
    @staticmethod
    def validate_embedding_config() -> Dict[str, Any]:
        """
        Validate and return embedding configuration
        
        Returns:
            Dict containing validation results and configuration
        """
        config = {
            "model": settings.embedding_model,
            "api_base_url": settings.embedding_api_base_url,
            "detected_provider": None,
            "is_valid": False,
            "error_message": None,
            "dimension": ModelConfiguration.get_embedding_dimension(settings.embedding_model)
        }
        
        try:
            # Detect provider from model name
            provider = EmbeddingFactory._detect_provider_from_model(settings.embedding_model)
            config["detected_provider"] = provider
            
            # Validate based on detected provider
            if provider == "openai" and not settings.openai_api_key:
                config["error_message"] = "OpenAI API key is required for OpenAI embedding models"
            elif provider == "gemini" and not settings.gemini_api_key:
                config["error_message"] = "Gemini API key is required for Gemini embedding models"
            elif provider == "ollama":
                if settings.embedding_api_base_url:
                    config["api_base_url"] = settings.embedding_api_base_url
                else:
                    config["api_base_url"] = "http://localhost:11434/v1/embeddings"
                config["is_valid"] = True
            else:
                # For auto-detection or huggingface, it should work
                config["is_valid"] = True
                
        except Exception as e:
            config["error_message"] = f"Embedding configuration validation failed: {str(e)}"
            logger.error(f"Embedding configuration validation error: {e}")
        
        return config
    
    @staticmethod
    def get_configuration_summary() -> Dict[str, Any]:
        """
        Get a comprehensive configuration summary
        
        Returns:
            Dict containing complete configuration status
        """
        llm_config = ModelConfiguration.validate_llm_config()
        embedding_config = ModelConfiguration.validate_embedding_config()
        
        return {
            "llm": llm_config,
            "embedding": embedding_config,
            "overall_status": "ready" if llm_config["is_valid"] and embedding_config["is_valid"] else "error",
            "environment": settings.app_env,
            "api_settings": {
                "host": settings.api_host,
                "port": settings.api_port
            },
            "processing_settings": {
                "chunk_size": settings.chunk_size,
                "chunk_overlap": settings.chunk_overlap,
                "max_tokens": settings.max_tokens,
                "temperature": settings.temperature
            }
        }
    
    @staticmethod
    def get_model_recommendations() -> Dict[str, List[str]]:
        """
        Get model recommendations for different providers
        
        Returns:
            Dict with provider-specific model recommendations
        """
        return {
            "openai": [
                "text-embedding-ada-002",
                "text-embedding-3-small",
                "text-embedding-3-large"
            ],
            "gemini": [
                "models/embedding-001"
            ],
            "ollama": [
                "nomic-embed-text",
                "all-minilm",
                "mxbai-embed-large"
            ],
            "huggingface": [
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
            ]
        }
    
    @staticmethod
    def get_llm_recommendations() -> Dict[str, List[str]]:
        """
        Get LLM model recommendations for different providers
        
        Returns:
            Dict with provider-specific LLM model recommendations
        """
        return {
            "openai": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-3.5-turbo",
                "gpt-4-turbo"
            ],
            "gemini": [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-pro"
            ],
            "ollama": [
                "llama3.1:8b",
                "llama3.1:70b",
                "mistral:7b",
                "codellama:7b",
                "gemma:7b"
            ],
            "azure_openai": [
                "gpt-4o",
                "gpt-4-turbo",
                "gpt-35-turbo",
                "gpt-4"
            ]
        }
