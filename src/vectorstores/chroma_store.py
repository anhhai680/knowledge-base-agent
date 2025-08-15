from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain.schema import Document
from typing import List, Dict, Any, Optional
import chromadb
import os
import shutil
import time
import subprocess
from .base_store import BaseVectorStore
from ..llm.embedding_factory import get_embedding_function, MultiModelEmbeddingWrapper
from ..config.model_config import ModelConfiguration
from ..utils.logging import get_logger

logger = get_logger(__name__)

class ChromaStore(BaseVectorStore):
    """Simplified Chroma vector store implementation with robust error handling"""
    
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
        
        # Use single embedding function for consistency
        self.embedding_function = self.default_embedding_function
        logger.info("Using single embedding model for consistency")
        
        # Initialize Chroma with simplified approach
        self._initialize_chroma_simple()
    
    def _initialize_chroma_simple(self):
        """Initialize Chroma with a simple, robust approach"""
        try:
            # Use persistent client for reliability
            logger.info("Initializing Chroma with persistent client")
            
            # Only clean directory if it's corrupted or empty
            if not self._is_persist_directory_valid():
                logger.info("Persist directory needs cleanup, performing maintenance")
                self._ensure_clean_persist_directory()
            else:
                logger.info("Persist directory is valid, skipping cleanup")
            
            # Create the vector store
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
                persist_directory=self.persist_directory
            )
            
            logger.info(f"ChromaStore initialized successfully in: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaStore: {str(e)}")
            # Try to create in a completely different location
            self._initialize_in_alternative_location()
    
    def _is_persist_directory_valid(self):
        """Check if the persist directory is valid and contains data"""
        try:
            if not os.path.exists(self.persist_directory):
                logger.info("Persist directory does not exist, needs creation")
                return False
            
            # Check if directory contains ChromaDB files
            chroma_files = []
            for root, dirs, files in os.walk(self.persist_directory):
                for file in files:
                    if file.endswith(('.sqlite', '.db', '.parquet')) or 'chroma' in file.lower():
                        chroma_files.append(os.path.join(root, file))
            
            if chroma_files:
                logger.info(f"Found {len(chroma_files)} ChromaDB files in persist directory")
                return True
            else:
                logger.info("Persist directory exists but contains no ChromaDB files")
                return False
                
        except Exception as e:
            logger.warning(f"Error checking persist directory validity: {e}")
            return False
    
    def _is_directory_corrupted(self):
        """Check if the persist directory is corrupted and needs cleanup"""
        try:
            if not os.path.exists(self.persist_directory):
                return False  # Not corrupted, just doesn't exist
            
            # Check for common corruption indicators
            corruption_indicators = [
                # Check for broken symlinks
                any(os.path.islink(os.path.join(self.persist_directory, item)) and 
                    not os.path.exists(os.path.join(self.persist_directory, item)) 
                    for item in os.listdir(self.persist_directory)),
                # Check for permission issues
                not os.access(self.persist_directory, os.R_OK | os.W_OK)
            ]
            
            if any(corruption_indicators):
                logger.warning("Directory corruption detected")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking directory corruption: {e}")
            return True  # Assume corrupted if we can't check
    
    def _ensure_clean_persist_directory(self):
        """Ensure the persist directory is clean and ready for use"""
        try:
            if os.path.exists(self.persist_directory):
                logger.info(f"Cleaning up existing directory: {self.persist_directory}")
                
                # Check if directory is actually corrupted before cleaning
                if self._is_directory_corrupted():
                    logger.warning("Directory appears corrupted, performing cleanup")
                    # Try to remove the directory
                    try:
                        shutil.rmtree(self.persist_directory)
                        logger.info("Successfully removed corrupted directory")
                    except OSError as e:
                        if "Device or resource busy" in str(e):
                            logger.warning("Resource busy, trying alternative cleanup")
                            self._force_cleanup_directory()
                        else:
                            raise e
                else:
                    logger.info("Directory appears healthy, skipping cleanup")
                    return
            
            # Create directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            logger.info(f"Ensured directory exists: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to ensure clean persist directory: {e}")
            raise
    
    def _force_cleanup_directory(self):
        """Force cleanup a directory that's busy"""
        try:
            logger.info("Performing force cleanup of busy directory")
            
            # Wait a bit
            time.sleep(2)
            
            # Try system commands
            if os.name != 'nt':  # Unix-like
                try:
                    subprocess.run(['rm', '-rf', self.persist_directory], check=False)
                    if not os.path.exists(self.persist_directory):
                        logger.info("System command cleanup successful")
                        return
                except:
                    pass
            
            # Try individual file removal
            if os.path.exists(self.persist_directory):
                for root, dirs, files in os.walk(self.persist_directory, topdown=False):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except:
                            pass
                    for dir in dirs:
                        try:
                            os.rmdir(os.path.join(root, dir))
                        except:
                            pass
                
                try:
                    os.rmdir(self.persist_directory)
                    logger.info("Individual file cleanup successful")
                except:
                    logger.warning("Individual cleanup failed, will use alternative location")
                    raise Exception("Directory cleanup failed")
                    
        except Exception as e:
            logger.error(f"Force cleanup failed: {e}")
            raise
    
    def _initialize_in_alternative_location(self):
        """Initialize Chroma in an alternative location"""
        try:
            logger.info("Initializing in alternative location")
            
            # Create timestamped alternative directory
            timestamp = int(time.time())
            alternative_dir = f"./chroma_db_alt_{timestamp}"
            
            # Ensure it's clean
            if os.path.exists(alternative_dir):
                shutil.rmtree(alternative_dir)
            
            os.makedirs(alternative_dir, exist_ok=True)
            
            # Update persist directory
            self.persist_directory = alternative_dir
            
            # Create vector store
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embedding_function,
                persist_directory=self.persist_directory
            )
            
            logger.info(f"ChromaStore initialized in alternative location: {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize in alternative location: {e}")
            raise Exception(f"All Chroma initialization methods failed: {e}")
    
    def _filter_document_metadata(self, documents: List[Document]) -> List[Document]:
        """Filter complex metadata from documents to ensure ChromaDB compatibility"""
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
        """Add documents to Chroma vector store with simplified error handling"""
        try:
            # Filter complex metadata from documents before adding to Chroma
            filtered_documents = self._filter_document_metadata(documents)
            
            # Add documents in batches to avoid token limits
            all_ids = []
            batch_size = 50  # Conservative batch size
            
            logger.info(f"Processing {len(filtered_documents)} documents in batches of {batch_size}")
            
            for i in range(0, len(filtered_documents), batch_size):
                batch = filtered_documents[i:i + batch_size]
                
                try:
                    # Add batch to vector store
                    batch_ids = self.vector_store.add_documents(batch)
                    all_ids.extend(batch_ids)
                    logger.debug(f"Successfully added batch {i//batch_size + 1}")
                    
                except Exception as batch_e:
                    logger.warning(f"Batch {i//batch_size + 1} failed: {batch_e}")
                    
                    # If it's a dimension mismatch, try to recreate the store
                    if "dimension" in str(batch_e).lower() or "inconsistent dimensions" in str(batch_e).lower():
                        logger.info("Dimension mismatch detected, recreating Chroma store")
                        self._recreate_chroma_store()
                        
                        # Retry the failed batch
                        try:
                            batch_ids = self.vector_store.add_documents(batch)
                            all_ids.extend(batch_ids)
                            logger.info("Successfully added batch after recreation")
                        except Exception as retry_e:
                            logger.error(f"Failed to add batch after recreation: {retry_e}")
                            raise retry_e
                    else:
                        # Re-raise other errors
                        raise batch_e
            
            # Persist the data to disk
            try:
                self.vector_store.persist()
                logger.info("Successfully persisted ChromaDB data to disk")
            except Exception as persist_e:
                logger.warning(f"Failed to persist data: {persist_e}")
            
            logger.info(f"Successfully added {len(all_ids)} documents to ChromaStore")
            return all_ids
            
        except Exception as e:
            error_msg = f"Failed to add documents to Chroma: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def _recreate_chroma_store(self):
        """Recreate the Chroma store to resolve dimension mismatches"""
        try:
            logger.info("Recreating Chroma store")
            
            # Close existing store if possible
            if hasattr(self, 'vector_store') and self.vector_store:
                try:
                    if hasattr(self.vector_store, 'close'):
                        self.vector_store.close()
                except:
                    pass
            
            # Remove the current directory
            if os.path.exists(self.persist_directory):
                try:
                    shutil.rmtree(self.persist_directory)
                except OSError as e:
                    if "Device or resource busy" in str(e):
                        logger.warning("Resource busy, using alternative location")
                        self._initialize_in_alternative_location()
                        return
                    else:
                        raise e
            
            # Reinitialize
            self._initialize_chroma_simple()
            
            # Ensure the new store is persisted
            try:
                if hasattr(self, 'vector_store') and self.vector_store:
                    self.vector_store.persist()
                    logger.info("Successfully persisted recreated Chroma store")
            except Exception as persist_e:
                logger.warning(f"Failed to persist recreated store: {persist_e}")
            
        except Exception as e:
            logger.error(f"Failed to recreate Chroma store: {e}")
            # Try alternative location as last resort
            self._initialize_in_alternative_location()
    
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
            
            # Persist the changes to disk
            try:
                self.vector_store.persist()
                logger.info("Successfully persisted deletion to disk")
            except Exception as persist_e:
                logger.warning(f"Failed to persist deletion: {persist_e}")
            
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
    
    def as_retriever(self, **kwargs):
        """Get retriever interface"""
        return self.vector_store.as_retriever(**kwargs)
