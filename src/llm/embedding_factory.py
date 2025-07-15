"""
Embedding Factory - Manages different embedding providers with fallback support
"""

from typing import Optional, Any
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

class EmbeddingFactory:
    """Factory class for creating embedding instances with fallback support"""
    
    @staticmethod
    def create_embedding(provider: str = "auto") -> Any:
        """
        Create an embedding instance based on the provider
        
        Args:
            provider: The embedding provider ("openai", "gemini", "huggingface", "auto")
                     "auto" will try providers in order of preference
        
        Returns:
            An embedding instance
        """
        if provider == "auto":
            return EmbeddingFactory._create_with_fallback()
        
        if provider == "openai":
            return EmbeddingFactory._create_openai_embedding()
        elif provider == "gemini":
            return EmbeddingFactory._create_gemini_embedding()
        elif provider == "huggingface":
            return EmbeddingFactory._create_huggingface_embedding()
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    @staticmethod
    def _create_with_fallback() -> Any:
        """Create embedding with automatic fallback"""
        
        # Try OpenAI first if API key is available
        if settings.openai_api_key:
            try:
                embedding = EmbeddingFactory._create_openai_embedding()
                logger.info("Using OpenAI embeddings")
                return embedding
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
        
        # Try Gemini if API key is available
        if settings.gemini_api_key:
            try:
                embedding = EmbeddingFactory._create_gemini_embedding()
                logger.info("Using Gemini embeddings")
                return embedding
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini embeddings: {e}")
        
        # Fallback to HuggingFace (no API key required)
        try:
            embedding = EmbeddingFactory._create_huggingface_embedding()
            logger.info("Using HuggingFace embeddings (local)")
            return embedding
        except Exception as e:
            logger.error(f"Failed to initialize any embedding provider: {e}")
            raise Exception("No embedding provider could be initialized")
    
    @staticmethod
    def _create_openai_embedding() -> OpenAIEmbeddings:
        """Create OpenAI embedding instance"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        return OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-ada-002",
            max_retries=3,
            request_timeout=30
        )
    
    @staticmethod
    def _create_gemini_embedding() -> GoogleGenerativeAIEmbeddings:
        """Create Gemini embedding instance"""
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured")
        
        return GoogleGenerativeAIEmbeddings(
            google_api_key=settings.gemini_api_key,
            model="models/embedding-001"
        )
    
    @staticmethod
    def _create_huggingface_embedding() -> HuggingFaceEmbeddings:
        """Create HuggingFace embedding instance (local, no API key required)"""
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

# Convenience function for easy import
def get_embedding_function(provider: str = "auto") -> Any:
    """Get embedding function with specified provider"""
    return EmbeddingFactory.create_embedding(provider)
