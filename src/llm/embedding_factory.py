"""
Embedding Factory - Manages different embedding providers with configuration support
"""

from typing import Optional, Any, List
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
    def create_embedding(provider: Optional[str] = None, model: Optional[str] = None, file_type: Optional[str] = None) -> Any:
        """
        Create an embedding instance based on the provider, model, and file type
        
        Args:
            provider: The embedding provider (if None, uses auto-detection)
            model: The embedding model name (if None, uses file-type-aware selection)
            file_type: The file type (e.g., '.md', '.py', '.js') for model selection
        
        Returns:
            An embedding instance
        """
        # Use file-type-aware model selection if no explicit model provided
        if model is None:
            model = EmbeddingFactory._select_model_for_file_type(file_type)
        
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
            api_key=settings.embedding_api_key,
            base_url=settings.embedding_api_base_url,
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

    @staticmethod
    def _select_model_for_file_type(file_type: Optional[str] = None) -> str:
        """Select the best embedding model based on file type"""
        if not file_type:
            return settings.embedding_model
        
        file_type_lower = file_type.lower()
        
        # For markdown files (especially those with diagrams), use larger models
        if file_type_lower in ['.md', '.markdown']:
            # Prioritize larger models for better semantic understanding of diagrams
            if settings.openai_api_key:
                return "text-embedding-3-large"  # 3072 dimensions, best for complex text
            elif settings.gemini_api_key:
                return "models/embedding-001"  # 768 dimensions, good for text
            elif settings.embedding_api_base_url:
                return "nomic-embed-text-v2"  # Improved version for text
            else:
                return "sentence-transformers/all-mpnet-base-v2"  # Local, good for text
        
        # For code files, use optimized models
        elif file_type_lower in ['.py', '.js', '.ts', '.jsx', '.tsx', '.cs', '.java']:
            if settings.openai_api_key:
                return "text-embedding-3-small"  # 1536 dimensions, good for code
            elif settings.embedding_api_base_url:
                return "nomic-embed-text"  # Good for code
            else:
                return "sentence-transformers/all-MiniLM-L6-v2"  # Local, good for code
        
        # For configuration and other files
        elif file_type_lower in ['.json', '.yml', '.yaml', '.xml', '.toml']:
            if settings.openai_api_key:
                return "text-embedding-3-small"  # 1536 dimensions
            else:
                return "sentence-transformers/all-MiniLM-L6-v2"  # Local
        
        # Default fallback
        return settings.embedding_model

# Convenience function for easy import
def get_embedding_function(provider: Optional[str] = None, model: Optional[str] = None, file_type: Optional[str] = None) -> Any:
    """Get embedding function with specified provider, model, and file type"""
    return EmbeddingFactory.create_embedding(provider, model, file_type)

class MultiModelEmbeddingWrapper:
    """Wrapper class that routes to different embedding models based on file type"""
    
    def __init__(self, default_embedding=None):
        self.default_embedding = default_embedding
        self._model_cache = {}  # Cache for created embedding models
        
        # Get configuration from settings
        from ..config.settings import settings
        
        # Use main embedding model for all file types to ensure consistency
        self._file_type_models = {
            '.md': settings.embedding_model,  # Use main model for markdown
            '.markdown': settings.embedding_model,
            '.py': settings.embedding_model,  # Use main model for code
            '.js': settings.embedding_model,
            '.ts': settings.embedding_model,
            '.jsx': settings.embedding_model,
            '.tsx': settings.embedding_model,
            '.cs': settings.embedding_model,
            '.java': settings.embedding_model,
            '.json': settings.embedding_model,
            '.yml': settings.embedding_model,
            '.yaml': settings.embedding_model
        }
    
    def _get_embedding_for_file_type(self, file_type: str) -> Any:
        """Get or create embedding model for a specific file type"""
        if file_type not in self._model_cache:
            try:
                # Create embedding for this file type
                model_name = self._file_type_models.get(file_type, 'text-embedding-3-small')
                embedding = EmbeddingFactory.create_embedding(model=model_name)
                self._model_cache[file_type] = embedding
                logger.info(f"Created embedding model for {file_type}: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to create embedding for {file_type}: {e}, using default")
                self._model_cache[file_type] = self.default_embedding
        
        return self._model_cache[file_type]
    
    def _detect_file_type_from_text(self, text: str) -> str:
        """Detect file type from text content (fallback when file path not available)"""
        # Look for markdown indicators
        if any(marker in text for marker in ['```mermaid', 'sequenceDiagram', 'participant', 'Note over']):
            return '.md'
        # Look for code indicators
        elif any(marker in text for marker in ['def ', 'class ', 'function ', 'import ', 'using ']):
            return '.py'  # Default to Python for code
        else:
            return '.txt'  # Default to text
    
    def embed_documents(self, texts: List[str], file_types: Optional[List[str]] = None) -> List[List[float]]:
        """Embed documents using appropriate models for each file type"""
        embeddings = []
        
        for i, text in enumerate(texts):
            # Determine file type
            file_type = None
            if file_types and i < len(file_types):
                file_type = file_types[i]
            else:
                # Fallback: detect from text content
                file_type = self._detect_file_type_from_text(text)
            
            # Get appropriate embedding model
            embedding_model = self._get_embedding_for_file_type(file_type)
            
            # Generate embedding
            try:
                if hasattr(embedding_model, 'embed_documents'):
                    # Batch embedding
                    doc_embedding = embedding_model.embed_documents([text])
                    embeddings.append(doc_embedding[0])
                elif hasattr(embedding_model, 'embed_query'):
                    # Single document embedding
                    doc_embedding = embedding_model.embed_query(text)
                    embeddings.append(doc_embedding)
                else:
                    # Fallback to default
                    logger.warning(f"Unknown embedding model type for {file_type}, using default")
                    if hasattr(self.default_embedding, 'embed_documents'):
                        doc_embedding = self.default_embedding.embed_documents([text])
                        embeddings.append(doc_embedding[0])
                    else:
                        raise ValueError(f"Invalid embedding model for {file_type}")
                        
            except Exception as e:
                logger.error(f"Failed to embed document with {file_type} model: {e}, using default")
                # Fallback to default embedding
                if hasattr(self.default_embedding, 'embed_documents'):
                    doc_embedding = self.default_embedding.embed_documents([text])
                    embeddings.append(doc_embedding[0])
                else:
                    raise
        
        return embeddings
    
    def embed_query(self, text: str, file_type: str = None) -> List[float]:
        """Embed a single query using appropriate model"""
        if not file_type:
            file_type = self._detect_file_type_from_text(text)
        
        embedding_model = self._get_embedding_for_file_type(file_type)
        
        try:
            if hasattr(embedding_model, 'embed_query'):
                return embedding_model.embed_query(text)
            elif hasattr(embedding_model, 'embed_documents'):
                return embedding_model.embed_documents([text])[0]
            else:
                raise ValueError(f"Invalid embedding model for {file_type}")
        except Exception as e:
            logger.error(f"Failed to embed query with {file_type} model: {e}, using default")
            # Fallback to default
            if hasattr(self.default_embedding, 'embed_query'):
                return self.default_embedding.embed_query(text)
            else:
                raise
