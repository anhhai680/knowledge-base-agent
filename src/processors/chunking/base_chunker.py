"""
Base abstract chunker class defining the interface for file-specific chunking strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain.docstore.document import Document


class ChunkMetadata:
    """Enhanced metadata structure for chunks with semantic information."""
    
    def __init__(
        self,
        source: str,
        file_path: str,
        file_type: str,
        chunk_type: str = "content",
        symbol_name: Optional[str] = None,
        parent_symbol: Optional[str] = None,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        language: Optional[str] = None,
        contains_documentation: bool = False,
        **kwargs
    ):
        self.source = source
        self.file_path = file_path
        self.file_type = file_type
        self.chunk_type = chunk_type
        self.symbol_name = symbol_name
        self.parent_symbol = parent_symbol
        self.line_start = line_start
        self.line_end = line_end
        self.language = language
        self.contains_documentation = contains_documentation
        self.extra = kwargs
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format."""
        metadata = {
            "source": self.source,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "chunk_type": self.chunk_type,
            "language": self.language,
            "contains_documentation": self.contains_documentation
        }
        
        # Add optional fields if they exist
        if self.symbol_name:
            metadata["symbol_name"] = self.symbol_name
        if self.parent_symbol:
            metadata["parent_symbol"] = self.parent_symbol
        if self.line_start is not None:
            metadata["line_start"] = self.line_start
        if self.line_end is not None:
            metadata["line_end"] = self.line_end
            
        # Add any extra metadata
        metadata.update(self.extra)
        
        return metadata


class BaseChunker(ABC):
    """
    Abstract base class for all chunking strategies.
    
    Each concrete chunker implements language or file-type specific chunking logic
    that preserves semantic boundaries appropriate for that content type.
    """
    
    def __init__(self, max_chunk_size: int = 1500, chunk_overlap: int = 100):
        """
        Initialize chunker with configuration.
        
        Args:
            max_chunk_size: Maximum size for chunks in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Return list of file extensions this chunker supports.
        
        Returns:
            List of file extensions (e.g., ['.py', '.pyx'])
        """
        pass
    
    @abstractmethod
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Chunk a single document according to the chunking strategy.
        
        Args:
            document: The document to chunk
            
        Returns:
            List of chunked documents with enhanced metadata
        """
        pass
    
    def can_handle(self, file_extension: str) -> bool:
        """
        Check if this chunker can handle the given file extension.
        
        Args:
            file_extension: File extension to check (e.g., '.py')
            
        Returns:
            True if this chunker supports the extension
        """
        return file_extension.lower() in [ext.lower() for ext in self.get_supported_extensions()]
    
    def _create_chunk_document(
        self,
        content: str,
        original_metadata: Dict[str, Any],
        chunk_metadata: ChunkMetadata,
        chunk_index: int,
        total_chunks: int
    ) -> Document:
        """
        Create a new Document with enhanced metadata.
        
        Args:
            content: The chunk content
            original_metadata: Original document metadata
            chunk_metadata: Enhanced semantic metadata
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks
            
        Returns:
            Document with combined metadata
        """
        # Start with original metadata
        metadata = dict(original_metadata)
        
        # Add chunking information
        metadata.update({
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "chunk_size": len(content)
        })
        
        # Add semantic metadata
        metadata.update(chunk_metadata.to_dict())
        
        return Document(page_content=content, metadata=metadata)
    
    def _clean_content(self, content: str) -> str:
        """
        Clean content by removing problematic characters and normalizing whitespace.
        
        Args:
            content: Content to clean
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
        
        # Log content details for debugging
        from ...utils.logging import get_logger
        logger = get_logger(__name__)
        
        original_length = len(content)
        logger.info(f"Cleaning content: original length={original_length}")
        
        # Remove null bytes and normalize line endings
        content = content.replace('\x00', '')
        content = content.replace('\r\n', '\n')
        content = content.replace('\r', '\n')
        
        # Remove trailing whitespace from lines but preserve indentation
        lines = content.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        
        cleaned_content = '\n'.join(cleaned_lines).strip()
        cleaned_length = len(cleaned_content)
        
        logger.info(f"Content cleaned: {original_length} -> {cleaned_length} chars")
        if cleaned_length < original_length * 0.8:  # If we lost more than 20% of content
            logger.warning(f"Significant content loss during cleaning: {original_length} -> {cleaned_length} chars")
        
        return cleaned_content
    
    def _split_oversized_chunk(self, content: str, metadata: ChunkMetadata) -> List[str]:
        """
        Split content that exceeds max_chunk_size using fallback strategy.
        
        Args:
            content: Content to split
            metadata: Metadata for the content
            
        Returns:
            List of content chunks
        """
        if len(content) <= self.max_chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.max_chunk_size
            
            # If this isn't the last chunk, try to break at a natural boundary
            if end < len(content):
                # Look for line breaks near the end
                break_point = content.rfind('\n', start + self.max_chunk_size - self.chunk_overlap, end)
                if break_point > start:
                    end = break_point + 1
            
            chunk_content = content[start:end]
            if chunk_content.strip():
                chunks.append(chunk_content)
            
            # Calculate next start position with overlap
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
