from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain.schema import Document
from typing import List, Dict, Any, Optional
import chromadb
import os
import shutil
from .base_store import BaseVectorStore
from ..llm.embedding_factory import get_embedding_function, MultiModelEmbeddingWrapper
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
        
        # Set up default embedding function (for backward compatibility)
        self.default_embedding_function = embedding_function or get_embedding_function()
        
        # Check if file-type-aware embeddings are enabled
        from ..config.settings import settings
        if settings.use_file_type_aware_embeddings:
            # Create multi-model wrapper for file-type-aware embeddings
            self.embedding_function = MultiModelEmbeddingWrapper(self.default_embedding_function)
            logger.info("File-type-aware embeddings enabled")
        else:
            # Use default embedding function
            self.embedding_function = self.default_embedding_function
            logger.info("File-type-aware embeddings disabled, using default")
        
        # Initialize Chroma with dimension compatibility checking
        self._initialize_chroma_with_compatibility_check()
    
    def _get_embedding_for_document(self, document: Document) -> Any:
        """Get the appropriate embedding function for a specific document based on file type"""
        try:
            # Extract file type from document metadata
            file_path = document.metadata.get('file_path', '')
            file_type = None
            
            if file_path:
                # Extract file extension
                if '.' in file_path:
                    file_type = '.' + file_path.split('.')[-1]
                else:
                    # Check if it's a markdown file without extension
                    if 'README' in file_path or 'readme' in file_path:
                        file_type = '.md'
            
            # If we have a file type, create a file-type-aware embedding
            if file_type:
                logger.debug(f"Creating file-type-aware embedding for {file_type}")
                return get_embedding_function(file_type=file_type)
            
            # Fallback to default embedding
            return self.default_embedding_function
            
        except Exception as e:
            logger.warning(f"Failed to create file-type-aware embedding: {e}, using default")
            return self.default_embedding_function
    
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
    
    def _filter_document_metadata(self, documents: List[Document]) -> List[Document]:
        """
        Filter complex metadata from documents to ensure ChromaDB compatibility.
        
        Args:
            documents: List of documents to filter
            
        Returns:
            List of documents with filtered metadata
        """
        filtered_documents = []
        
        for doc in documents:
            try:
                # Use LangChain's built-in metadata filtering first
                filtered_docs = filter_complex_metadata([doc])
                if filtered_docs:
                    filtered_documents.extend(filtered_docs)
                    continue
            except Exception as filter_error:
                logger.debug(f"filter_complex_metadata failed: {str(filter_error)}")
            
            # Fallback: manually filter known complex types
            filtered_metadata = {}
            for key, value in doc.metadata.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    filtered_metadata[key] = value
                elif isinstance(value, list):
                    # Convert lists to strings for ChromaDB compatibility
                    if all(isinstance(item, str) for item in value):
                        filtered_metadata[key] = ", ".join(value)
                    else:
                        filtered_metadata[key] = str(value)
                elif isinstance(value, dict):
                    # Convert dicts to strings
                    filtered_metadata[key] = str(value)
                else:
                    # Convert other complex types to strings
                    filtered_metadata[key] = str(value)
            
            filtered_doc = Document(
                page_content=doc.page_content,
                metadata=filtered_metadata
            )
            filtered_documents.append(filtered_doc)
        
        return filtered_documents

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to Chroma vector store with batch processing to avoid token limits"""
        try:
            # Ensure collection metadata is up to date
            self._update_collection_metadata()
            
            # Filter complex metadata from documents before adding to Chroma
            filtered_documents = self._filter_document_metadata(documents)
            
            # Implement batch processing to avoid token limits
            all_ids = []
            batch_size = self._calculate_optimal_batch_size(filtered_documents)
            
            logger.info(f"Processing {len(filtered_documents)} documents in batches of {batch_size}")
            
            for i in range(0, len(filtered_documents), batch_size):
                batch = filtered_documents[i:i + batch_size]
                
                try:
                    # Estimate tokens for this batch
                    batch_tokens = self._estimate_batch_tokens(batch)
                    logger.debug(f"Batch {i//batch_size + 1}: {len(batch)} documents, ~{batch_tokens} tokens")
                    
                    # Add batch to vector store
                    batch_ids = self.vector_store.add_documents(batch)
                    all_ids.extend(batch_ids)
                    
                except Exception as batch_e:
                    # Check if it's a token limit error and reduce batch size
                    if "max_tokens_per_request" in str(batch_e).lower() or "413" in str(batch_e):
                        logger.warning(f"Token limit exceeded for batch, reducing batch size and retrying")
                        # Recursively process with smaller batches
                        smaller_batch_ids = self._process_with_reduced_batch_size(batch)
                        all_ids.extend(smaller_batch_ids)
                    else:
                        # Re-raise other errors
                        raise batch_e
            
            logger.info(f"Added {len(all_ids)} documents to ChromaStore in {(len(filtered_documents) + batch_size - 1) // batch_size} batches")
            return all_ids
            
        except Exception as e:
            error_msg = f"Failed to add documents to Chroma: {str(e)}"
            logger.error(error_msg)
            
            # Check if it's a dimension mismatch error
            if "dimension" in str(e).lower():
                logger.warning("Dimension mismatch detected. Attempting to recreate collection.")
                try:
                    self._handle_dimension_mismatch()
                    # Retry adding documents with filtered metadata and batching
                    retry_filtered_documents = self._filter_document_metadata(documents)
                    ids = self.add_documents(retry_filtered_documents)  # Recursive call with batching
                    logger.info(f"Successfully added {len(ids)} documents after collection recreation")
                    return ids
                except Exception as retry_e:
                    error_msg = f"Failed to add documents after collection recreation: {str(retry_e)}"
                    logger.error(error_msg)
            
            raise Exception(error_msg)
    
    def _calculate_optimal_batch_size(self, documents: List[Document]) -> int:
        """
        Calculate optimal batch size based on document content and token limits.
        
        Args:
            documents: List of documents to analyze
            
        Returns:
            Optimal batch size to stay under token limits
        """
        from ..config.settings import settings
        
        if not documents:
            return settings.embedding_batch_size  # Use configured default
        
        # Sample a few documents to estimate average token count
        sample_size = min(5, len(documents))
        sample_documents = documents[:sample_size]
        
        total_tokens = 0
        for doc in sample_documents:
            # Rough estimate: 1 token ~= 4 characters for English text
            estimated_tokens = len(doc.page_content) // 4
            total_tokens += estimated_tokens
        
        avg_tokens_per_doc = total_tokens / sample_size if sample_size > 0 else 1000
        
        # Use configured token limit
        safe_token_limit = settings.max_tokens_per_batch
        
        # Calculate batch size
        optimal_batch_size = max(1, int(safe_token_limit / avg_tokens_per_doc))
        
        # Cap at configured batch size and reasonable maximum
        optimal_batch_size = min(optimal_batch_size, settings.embedding_batch_size, 100)
        
        logger.debug(f"Calculated optimal batch size: {optimal_batch_size} (avg tokens per doc: {avg_tokens_per_doc:.0f})")
        
        return optimal_batch_size
    
    def _estimate_batch_tokens(self, batch: List[Document]) -> int:
        """
        Estimate total tokens for a batch of documents.
        
        Args:
            batch: List of documents to estimate
            
        Returns:
            Estimated token count for the batch
        """
        total_tokens = 0
        for doc in batch:
            # Rough estimate: 1 token ~= 4 characters for English text
            # Add some overhead for metadata
            content_tokens = len(doc.page_content) // 4
            metadata_tokens = len(str(doc.metadata)) // 4
            total_tokens += content_tokens + metadata_tokens + 10  # Small buffer per document
        
        return total_tokens
    
    def _process_with_reduced_batch_size(self, failed_batch: List[Document]) -> List[str]:
        """
        Process a failed batch with progressively smaller batch sizes.
        
        Args:
            failed_batch: Batch that failed due to token limits
            
        Returns:
            List of document IDs that were successfully added
        """
        all_ids = []
        current_batch_size = max(1, len(failed_batch) // 2)  # Start with half the original size
        
        logger.info(f"Retrying failed batch of {len(failed_batch)} documents with reduced batch size: {current_batch_size}")
        
        for i in range(0, len(failed_batch), current_batch_size):
            batch = failed_batch[i:i + current_batch_size]
            
            try:
                batch_ids = self.vector_store.add_documents(batch)
                all_ids.extend(batch_ids)
                logger.debug(f"Successfully processed reduced batch: {len(batch)} documents")
                
            except Exception as e:
                if "max_tokens_per_request" in str(e).lower() or "413" in str(e):
                    # If still too large, process documents individually
                    if len(batch) == 1:
                        # Single document is too large - log warning and skip
                        logger.warning(f"Skipping document that is too large: {batch[0].metadata.get('file_path', 'unknown')}")
                        continue
                    else:
                        # Recursively reduce batch size further
                        recursive_ids = self._process_with_reduced_batch_size(batch)
                        all_ids.extend(recursive_ids)
                else:
                    # Other error, re-raise
                    raise e
        
        return all_ids
    
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
    
    def similarity_search(self, query: str, k: int = 5, filter: Optional[Dict[str, str]] = None) -> List[Document]:
        """Perform similarity search in Chroma with optional metadata filtering"""
        try:
            if filter:
                logger.info(f"FILTER DEBUG: Searching with filter: {filter}")
                results = self.vector_store.similarity_search(query, k=k, filter=filter)
                logger.info(f"FILTER DEBUG: Found {len(results)} similar documents for query with filter {filter}")
                # Log first few results to debug
                for i, doc in enumerate(results[:3]):
                    repo = doc.metadata.get('repository', 'unknown')
                    logger.info(f"FILTER DEBUG: Result {i+1} repository: {repo}")
            else:
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
