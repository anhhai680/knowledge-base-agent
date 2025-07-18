from langchain_community.vectorstores import Chroma
from langchain.schema import Document
from typing import List, Dict, Any, Optional
import chromadb
import os
import shutil
from .base_store import BaseVectorStore
from ..llm.embedding_factory import get_embedding_function
from ..config.model_config import ModelConfiguration
from ..utils.logging import get_logger

logger = get_logger(__name__)

class ChromaStore(BaseVectorStore):
    """Chroma vector store implementation with dimension compatibility checking"""
    
    def __init__(self, 
                 collection_name: str = "knowledge-base-collection",
                 host: str = "localhost",
                 port: int = 8000,
                 embedding_function = None,
                 persist_directory: str = "./chroma_db"):
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.persist_directory = persist_directory
        
        # Set up embedding function
        self.embedding_function = embedding_function or get_embedding_function()
        
        # Initialize Chroma with dimension compatibility checking
        self._initialize_chroma_with_compatibility_check()
        
    def _initialize_chroma_with_compatibility_check(self):
        """Initialize Chroma with dimension compatibility checking"""
        try:
            # For Docker environment, always use persistent client to ensure data persistence
            # The HTTP client creates separate in-memory collections that don't persist
            if os.getenv("DOCKER_CONTAINER"):
                logger.info("Docker environment detected, using persistent client for data consistency")
                self._initialize_persistent_client()
                return
            
            # First, try to connect to existing collection
            self.client = chromadb.HttpClient(host=self.host, port=self.port)
            
            # Check if collection exists and if dimensions are compatible
            if self._collection_exists():
                if not self._check_dimension_compatibility():
                    logger.warning(f"Dimension mismatch detected for collection {self.collection_name}. Recreating collection.")
                    self._recreate_collection()
                else:
                    logger.info(f"Using existing collection {self.collection_name} with compatible dimensions")
            
            # Initialize Chroma vector store
            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"ChromaStore initialized successfully for collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaStore with HTTP client: {str(e)}")
            # Fallback to persistent client for local development
            self._initialize_persistent_client()
    
    def _initialize_persistent_client(self):
        """Initialize persistent client as fallback"""
        try:
            # Check if persistent collection exists and if dimensions are compatible
            if self._persistent_collection_exists():
                if not self._check_dimension_compatibility_persistent():
                    logger.warning(f"Dimension mismatch detected for persistent collection {self.collection_name}. Recreating collection.")
                    self._recreate_persistent_collection()
                else:
                    logger.info(f"Using existing persistent collection {self.collection_name} with compatible dimensions")
            
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
                persist_directory=self.persist_directory
            )
            logger.info("Fallback to persistent ChromaStore initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize persistent ChromaStore: {str(e)}")
            raise
    
    def _collection_exists(self) -> bool:
        """Check if collection exists in HTTP client"""
        try:
            collections = self.client.list_collections()
            return any(col.name == self.collection_name for col in collections)
        except Exception as e:
            logger.error(f"Failed to check collection existence: {str(e)}")
            return False
    
    def _persistent_collection_exists(self) -> bool:
        """Check if persistent collection exists"""
        try:
            persistent_client = chromadb.PersistentClient(path=self.persist_directory)
            collections = persistent_client.list_collections()
            return any(col.name == self.collection_name for col in collections)
        except Exception as e:
            logger.error(f"Failed to check persistent collection existence: {str(e)}")
            return False
    
    def _check_dimension_compatibility(self) -> bool:
        """Check if existing collection has compatible embedding dimensions"""
        try:
            collection = self.client.get_collection(self.collection_name)
            
            # Get collection metadata
            metadata = collection.metadata or {}
            stored_model = metadata.get("embedding_model")
            stored_dimension = metadata.get("embedding_dimension")
            
            # Get current embedding model and dimension
            from ..config.settings import settings
            current_model = settings.embedding_model
            current_dimension = ModelConfiguration.get_embedding_dimension(current_model)
            
            # If we can't determine dimensions, detect them
            if current_dimension is None:
                current_dimension = ModelConfiguration.detect_embedding_dimension(self.embedding_function)
            
            # Compare dimensions
            if stored_dimension and current_dimension:
                is_compatible = stored_dimension == current_dimension
                logger.info(f"Dimension compatibility check: stored={stored_dimension}, current={current_dimension}, compatible={is_compatible}")
                return is_compatible
            
            # If metadata is missing, assume incompatible for safety
            logger.warning(f"Missing dimension metadata for collection {self.collection_name}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to check dimension compatibility: {str(e)}")
            return False
    
    def _check_dimension_compatibility_persistent(self) -> bool:
        """Check dimension compatibility for persistent collection"""
        try:
            persistent_client = chromadb.PersistentClient(path=self.persist_directory)
            collection = persistent_client.get_collection(self.collection_name)
            
            # Get collection metadata
            metadata = collection.metadata or {}
            stored_model = metadata.get("embedding_model")
            stored_dimension = metadata.get("embedding_dimension")
            
            # Get current embedding model and dimension
            from ..config.settings import settings
            current_model = settings.embedding_model
            current_dimension = ModelConfiguration.get_embedding_dimension(current_model)
            
            # If we can't determine dimensions, detect them
            if current_dimension is None:
                current_dimension = ModelConfiguration.detect_embedding_dimension(self.embedding_function)
            
            # Compare dimensions
            if stored_dimension and current_dimension:
                is_compatible = stored_dimension == current_dimension
                logger.info(f"Persistent dimension compatibility check: stored={stored_dimension}, current={current_dimension}, compatible={is_compatible}")
                return is_compatible
            
            # If metadata is missing, assume incompatible for safety
            logger.warning(f"Missing dimension metadata for persistent collection {self.collection_name}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to check persistent dimension compatibility: {str(e)}")
            return False
    
    def _recreate_collection(self):
        """Recreate collection with new embedding dimensions"""
        try:
            # Delete existing collection
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted existing collection: {self.collection_name}")
            
            # Create new collection with metadata
            from ..config.settings import settings
            metadata = ModelConfiguration.get_collection_metadata(settings.embedding_model)
            
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata=metadata
            )
            logger.info(f"Created new collection: {self.collection_name} with metadata: {metadata}")
            
        except Exception as e:
            logger.error(f"Failed to recreate collection: {str(e)}")
            raise
    
    def _recreate_persistent_collection(self):
        """Recreate persistent collection with new embedding dimensions"""
        try:
            # Remove persistent directory
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                logger.info(f"Removed persistent directory: {self.persist_directory}")
            
            # Create new persistent client and collection
            persistent_client = chromadb.PersistentClient(path=self.persist_directory)
            from ..config.settings import settings
            metadata = ModelConfiguration.get_collection_metadata(settings.embedding_model)
            
            collection = persistent_client.create_collection(
                name=self.collection_name,
                metadata=metadata
            )
            logger.info(f"Created new persistent collection: {self.collection_name} with metadata: {metadata}")
            
        except Exception as e:
            logger.error(f"Failed to recreate persistent collection: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to Chroma vector store"""
        try:
            # Ensure collection metadata is up to date
            self._update_collection_metadata()
            
            ids = self.vector_store.add_documents(documents)
            logger.info(f"Added {len(ids)} documents to ChromaStore")
            return ids
        except Exception as e:
            error_msg = f"Failed to add documents to Chroma: {str(e)}"
            logger.error(error_msg)
            
            # Check if it's a dimension mismatch error
            if "dimension" in str(e).lower():
                logger.warning("Dimension mismatch detected. Attempting to recreate collection.")
                try:
                    self._handle_dimension_mismatch()
                    # Retry adding documents
                    ids = self.vector_store.add_documents(documents)
                    logger.info(f"Successfully added {len(ids)} documents after collection recreation")
                    return ids
                except Exception as retry_e:
                    error_msg = f"Failed to add documents after collection recreation: {str(retry_e)}"
                    logger.error(error_msg)
            
            raise Exception(error_msg)
    
    def _update_collection_metadata(self):
        """Update collection metadata with current embedding model info"""
        try:
            from ..config.settings import settings
            metadata = ModelConfiguration.get_collection_metadata(settings.embedding_model)
            
            # Update metadata if we have access to the collection
            if hasattr(self.vector_store, '_collection') and self.vector_store._collection:
                current_metadata = self.vector_store._collection.metadata or {}
                if current_metadata.get("embedding_model") != metadata["embedding_model"]:
                    logger.info(f"Updating collection metadata for model change: {current_metadata.get('embedding_model')} -> {metadata['embedding_model']}")
                    self.vector_store._collection.modify(metadata=metadata)
            
        except Exception as e:
            logger.warning(f"Failed to update collection metadata: {str(e)}")
    
    def _handle_dimension_mismatch(self):
        """Handle dimension mismatch by recreating the collection"""
        try:
            if hasattr(self, 'client') and self.client:
                # HTTP client mode
                self._recreate_collection()
            else:
                # Persistent client mode
                self._recreate_persistent_collection()
            
            # Reinitialize the vector store
            self._initialize_chroma_with_compatibility_check()
            
        except Exception as e:
            logger.error(f"Failed to handle dimension mismatch: {str(e)}")
            raise
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Perform similarity search in Chroma"""
        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.debug(f"Found {len(results)} similar documents for query")
            return results
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {str(e)}")
            raise Exception(f"Failed to perform similarity search: {str(e)}")
    
    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents from Chroma"""
        try:
            self.vector_store.delete(ids)
            logger.info(f"Deleted {len(ids)} documents from ChromaStore")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        try:
            if hasattr(self.vector_store, '_collection'):
                collection = self.vector_store._collection
                metadata = collection.metadata or {}
                
                return {
                    "name": collection.name,
                    "count": collection.count(),
                    "metadata": metadata,
                    "embedding_model": metadata.get("embedding_model", "unknown"),
                    "embedding_dimension": metadata.get("embedding_dimension", "unknown"),
                    "embedding_provider": metadata.get("embedding_provider", "unknown")
                }
            else:
                return {
                    "name": self.collection_name,
                    "count": 0,
                    "metadata": {},
                    "embedding_model": "unknown",
                    "embedding_dimension": "unknown",
                    "embedding_provider": "unknown"
                }
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return {"error": f"Failed to get collection info: {str(e)}"}
    
    def validate_embedding_compatibility(self, embedding_model: str) -> bool:
        """
        Validate if the given embedding model is compatible with the existing collection
        
        Args:
            embedding_model: Name of the embedding model to validate
            
        Returns:
            True if compatible, False otherwise
        """
        try:
            collection_info = self.get_collection_info()
            current_model = collection_info.get("embedding_model")
            
            if current_model == "unknown" or current_model is None:
                # No existing model info, assume compatible
                return True
                
            return ModelConfiguration.check_dimension_compatibility(current_model, embedding_model)
            
        except Exception as e:
            logger.error(f"Failed to validate embedding compatibility: {str(e)}")
            return False
    
    def migrate_to_new_embedding_model(self, new_embedding_model: str, new_embedding_function) -> bool:
        """
        Migrate collection to use a new embedding model
        
        Args:
            new_embedding_model: Name of the new embedding model
            new_embedding_function: New embedding function instance
            
        Returns:
            True if migration successful, False otherwise
        """
        try:
            logger.info(f"Migrating collection to new embedding model: {new_embedding_model}")
            
            # Check if migration is needed
            if self.validate_embedding_compatibility(new_embedding_model):
                logger.info("New embedding model is compatible. No migration needed.")
                return True
            
            # Store existing documents if any
            existing_docs = []
            try:
                # Get all documents (this is a simplified approach)
                # In a real scenario, you might want to implement pagination
                existing_docs = self.vector_store.similarity_search("", k=10000)
                logger.info(f"Found {len(existing_docs)} existing documents to migrate")
            except Exception as e:
                logger.warning(f"Could not retrieve existing documents: {str(e)}")
            
            # Update embedding function
            self.embedding_function = new_embedding_function
            
            # Recreate collection
            self._handle_dimension_mismatch()
            
            # Re-add documents if any were found
            if existing_docs:
                logger.info(f"Re-adding {len(existing_docs)} documents with new embedding model")
                self.add_documents(existing_docs)
            
            logger.info(f"Successfully migrated collection to {new_embedding_model}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to migrate to new embedding model: {str(e)}")
            return False
    
    def as_retriever(self, **kwargs):
        """Get retriever interface"""
        return self.vector_store.as_retriever(**kwargs)
