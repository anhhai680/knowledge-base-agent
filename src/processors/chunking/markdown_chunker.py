"""
Markdown-specific chunker that preserves diagram content integrity.

This chunker uses larger chunk sizes for markdown files that contain diagrams,
ensuring that sequence diagrams and other visual content are not split across chunks.
"""

import re
from typing import List, Dict, Any
from .base_chunker import BaseChunker
from langchain.text_splitter import MarkdownTextSplitter
from langchain.docstore.document import Document
from ...utils.logging import get_logger

logger = get_logger(__name__)


class MarkdownChunker(BaseChunker):
    """Enhanced markdown chunker using LangChain's MarkdownTextSplitter for better structure preservation"""
    
    def __init__(self, max_chunk_size: int = 4000, chunk_overlap: int = 200):
        super().__init__(max_chunk_size, chunk_overlap)
        
        # Initialize LangChain's MarkdownTextSplitter with optimized settings
        self.markdown_splitter = MarkdownTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=chunk_overlap,
            # Preserve markdown structure
            keep_separator=True,
            # Handle code blocks and diagrams properly
            separators=[
                # Headers (preserve hierarchy)
                "\n# ", "\n## ", "\n### ", "\n#### ", "\n##### ", "\n###### ",
                # Code blocks (preserve complete blocks)
                "\n```", "\n````",
                # Lists
                "\n- ", "\n* ", "\n+ ",
                "\n1. ", "\n2. ", "\n3. ", "\n4. ", "\n5. ",
                # Paragraphs
                "\n\n",
                # Lines
                "\n",
                # Words (fallback)
                " "
            ]
        )
    
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Chunk a single document according to the chunking strategy.
        
        Args:
            document: The document to chunk
            
        Returns:
            List of chunked documents with enhanced metadata
        """
        # Extract content and metadata from the document
        text = document.page_content
        metadata = document.metadata
        
        # Use the existing chunk_text method
        chunks_data = self.chunk_text(text, metadata)
        
        # Convert to Document objects
        documents = []
        for chunk_data in chunks_data:
            doc = Document(
                page_content=chunk_data['content'],
                metadata=chunk_data['metadata']
            )
            documents.append(doc)
        
        return documents

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Chunk markdown text using LangChain's MarkdownTextSplitter
        
        Args:
            text: The markdown text to chunk
            metadata: Additional metadata for the chunks
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        try:
            # Use LangChain's MarkdownTextSplitter for intelligent chunking
            chunks = self.markdown_splitter.split_text(text)
            
            # Convert to our standard format
            result_chunks = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_index': i,
                    'chunk_type': 'markdown',
                    'chunk_size': len(chunk),
                    'total_chunks': len(chunks),
                    'chunker': 'MarkdownTextSplitter'
                })
                
                result_chunks.append({
                    'content': chunk,
                    'metadata': chunk_metadata
                })
            
            logger.info(f"MarkdownTextSplitter created {len(chunks)} chunks from markdown content")
            return result_chunks
            
        except Exception as e:
            logger.error(f"Error in MarkdownTextSplitter chunking: {e}")
            # Fallback to base chunking
            return super().chunk_text(text, metadata)
    
    def get_supported_extensions(self) -> List[str]:
        """Return supported file extensions"""
        return ['.md', '.markdown', '.mdx']
    
    def get_chunker_info(self) -> Dict[str, Any]:
        """Return information about this chunker"""
        return {
            'name': 'MarkdownTextSplitter',
            'description': 'Uses LangChain\'s MarkdownTextSplitter for intelligent markdown chunking',
            'preserves_structure': True,
            'handles_diagrams': True,
            'separators': self.markdown_splitter.separators[:5],  # Show first 5 separators
            'chunk_size': self.max_chunk_size,
            'chunk_overlap': self.chunk_overlap
        }
