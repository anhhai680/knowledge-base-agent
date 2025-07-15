"""
Embedding Factory - Manages different embedding providers with configuration support
"""

from typing import Optional, Any
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
try:
    from langchain_community.embeddings import OllamaEmbeddings
except ImportError:
    OllamaEmbeddings = None
from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

class EmbeddingFactory:
    """Factory class for creating embedding instances with configuration support"""
    
    @staticmethod
    def create_embedding(provider: Optional[str] = None, model: Optional[str] = None) -> Any:
        """
        Create an embedding instance based on the provider and model
        
        Args:
            provider: The embedding provider (if None, uses auto-detection)
            model: The embedding model name (if None, uses settings.embedding_model)
        
        Returns:
            An embedding instance
        """
        # Use settings if no explicit model provided
        if model is None:
            model = settings.embedding_model
        
        if provider is None:
            return EmbeddingFactory._create_with_auto_detection(model)
        
        provider = provider.lower()
        
        if provider == "openai":
            return EmbeddingFactory._create_openai_embedding(model)
        elif provider == "gemini":
            return EmbeddingFactory._create_gemini_embedding(model)
        elif provider == "ollama":
            return EmbeddingFactory._create_ollama_embedding(model)
        elif provider == "huggingface":
            return EmbeddingFactory._create_huggingface_embedding(model)
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")
    
    @staticmethod
    def _create_with_auto_detection(model: str) -> Any:
        """Create embedding with automatic provider detection based on model name"""
        
        # Try to determine provider from model name
        provider = EmbeddingFactory._detect_provider_from_model(model)
        
        if provider == "openai":
            return EmbeddingFactory._create_openai_embedding(model)
        elif provider == "gemini":
            return EmbeddingFactory._create_gemini_embedding(model)
        elif provider == "ollama":
            return EmbeddingFactory._create_ollama_embedding(model)
        else:
            # Fallback to auto-detection with API key availability
            return EmbeddingFactory._create_with_fallback(model)
    
    @staticmethod
    def _detect_provider_from_model(model: str) -> str:
        """Detect provider from model name"""
        model_lower = model.lower()
        
        if any(keyword in model_lower for keyword in ["text-embedding", "ada", "davinci"]):
            return "openai"
        elif any(keyword in model_lower for keyword in ["embedding-001", "gemini"]):
            return "gemini"
        elif any(keyword in model_lower for keyword in ["nomic", "llama", "mistral", "codellama"]):
            return "ollama"
        else:
            return "auto"  # Will trigger fallback logic
    
    @staticmethod
    def _create_with_fallback(model: str) -> Any:
        """Create embedding with automatic fallback"""
        
        # Try OpenAI first if API key is available
        if settings.openai_api_key:
            try:
                embedding = EmbeddingFactory._create_openai_embedding(model)
                logger.info(f"Using OpenAI embeddings with model: {model}")
                return embedding
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
        
        # Try Gemini if API key is available
        if settings.gemini_api_key:
            try:
                embedding = EmbeddingFactory._create_gemini_embedding(model)
                logger.info(f"Using Gemini embeddings with model: {model}")
                return embedding
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini embeddings: {e}")
        
        # Try Ollama if available
        if OllamaEmbeddings and settings.embedding_api_base_url:
            try:
                embedding = EmbeddingFactory._create_ollama_embedding(model)
                logger.info(f"Using Ollama embeddings with model: {model}")
                return embedding
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama embeddings: {e}")
        
        # Fallback to HuggingFace (no API key required)
        try:
            embedding = EmbeddingFactory._create_huggingface_embedding(model)
            logger.info(f"Using HuggingFace embeddings with model: {model}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to initialize any embedding provider: {e}")
            raise Exception("No embedding provider could be initialized")
    
    @staticmethod
    def _create_openai_embedding(model: str) -> OpenAIEmbeddings:
        """Create OpenAI embedding instance"""
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        # Use provided model or default
        embedding_model = model if model else "text-embedding-ada-002"
        
        return OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=embedding_model,
            max_retries=3,
            request_timeout=30
        )
    
    @staticmethod
    def _create_gemini_embedding(model: str) -> GoogleGenerativeAIEmbeddings:
        """Create Gemini embedding instance"""
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured")
        
        # Use provided model or default
        embedding_model = model if model else "models/embedding-001"
        
        return GoogleGenerativeAIEmbeddings(
            google_api_key=settings.gemini_api_key,
            model=embedding_model
        )
    
    @staticmethod
    def _create_ollama_embedding(model: str) -> Any:
        """Create Ollama embedding instance"""
        if not OllamaEmbeddings:
            raise ValueError("Ollama embeddings not available. Install required dependencies.")
        
        base_url = settings.embedding_api_base_url or "http://localhost:11434"
        # Use provided model or default
        embedding_model = model if model else "nomic-embed-text"
        
        return OllamaEmbeddings(
            model=embedding_model,
            base_url=base_url
        )
    
    @staticmethod
    def _create_huggingface_embedding(model: str) -> HuggingFaceEmbeddings:
        """Create HuggingFace embedding instance (local, no API key required)"""
        # Use provided model or default
        embedding_model = model if model else "sentence-transformers/all-MiniLM-L6-v2"
        
        return HuggingFaceEmbeddings(
            model_name=embedding_model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

# Convenience function for easy import
def get_embedding_function(provider: Optional[str] = None, model: Optional[str] = None) -> Any:
    """Get embedding function with specified provider and model"""
    return EmbeddingFactory.create_embedding(provider, model)
