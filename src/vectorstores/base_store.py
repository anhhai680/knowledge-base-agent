from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain.schema import Document

class BaseVectorStore(ABC):
    """Abstract base class for vector stores"""
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store"""
        pass
    
    @abstractmethod
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Perform similarity search"""
        pass
    
    @abstractmethod
    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents from the vector store"""
        pass
    
    @abstractmethod
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        pass
