from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from typing import List, Dict, Any, Optional
import chromadb
from .base_store import BaseVectorStore
from ..utils.logging import get_logger

logger = get_logger(__name__)

class ChromaStore(BaseVectorStore):
    """Chroma vector store implementation"""
    
    def __init__(self, 
                 collection_name: str = "knowledge-base-collection",
                 host: str = "localhost",
                 port: int = 8000,
                 embedding_function = None):
        self.collection_name = collection_name
        self.host = host
        self.port = port
        
        # Set up embedding function
        self.embedding_function = embedding_function or OpenAIEmbeddings()
        
        try:
            # Initialize Chroma client
            self.client = chromadb.HttpClient(
                host=host,
                port=port
            )
            
            # Initialize Chroma vector store
            self.vector_store = Chroma(
                client=self.client,
                collection_name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"ChromaStore initialized successfully for collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaStore: {str(e)}")
            # Fallback to persistent client for local development
            self.vector_store = Chroma(
                collection_name=collection_name,
                embedding_function=self.embedding_function,
                persist_directory="./chroma_db"
            )
            logger.info("Fallback to persistent ChromaStore")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to Chroma vector store"""
        try:
            ids = self.vector_store.add_documents(documents)
            logger.info(f"Added {len(ids)} documents to ChromaStore")
            return ids
        except Exception as e:
            logger.error(f"Failed to add documents to Chroma: {str(e)}")
            raise Exception(f"Failed to add documents to Chroma: {str(e)}")
    
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
                return {
                    "name": collection.name,
                    "count": collection.count(),
                    "metadata": getattr(collection, 'metadata', {})
                }
            else:
                return {
                    "name": self.collection_name,
                    "count": 0,
                    "metadata": {}
                }
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            return {"error": f"Failed to get collection info: {str(e)}"}
    
    def as_retriever(self, **kwargs):
        """Get retriever interface"""
        return self.vector_store.as_retriever(**kwargs)
