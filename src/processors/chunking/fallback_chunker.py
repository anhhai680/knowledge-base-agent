"""
Fallback chunker for unsupported file types.

This chunker uses a simple recursive character-based splitting strategy
similar to the current implementation, for files that don't have
specialized chunking strategies.
"""

from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

from .base_chunker import BaseChunker, ChunkMetadata
from ...utils.logging import get_logger

logger = get_logger(__name__)


class FallbackChunker(BaseChunker):
    """
    Fallback chunker for unsupported file types.
    
    Uses RecursiveCharacterTextSplitter with sensible defaults for
    general text content that doesn't have specialized parsing rules.
    """
    
    def __init__(self, max_chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize fallback chunker.
        
        Args:
            max_chunk_size: Maximum size for chunks in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        super().__init__(max_chunk_size, chunk_overlap)
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def get_supported_extensions(self) -> List[str]:
        """
        Fallback chunker supports all file types.
        
        Returns:
            Empty list since this is a fallback for any extension
        """
        return []
    
    def can_handle(self, file_extension: str) -> bool:
        """
        Fallback chunker can handle any file extension.
        
        Args:
            file_extension: File extension to check
            
        Returns:
            Always True for fallback chunker
        """
        return True
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the fallback chunker with new settings.
        
        Args:
            config: Configuration dictionary containing chunking settings
        """
        # Call parent configure method
        super().configure(config)
        
        # Recreate text splitter with new settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.max_chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Chunk document using recursive character splitting.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunked documents
        """
        try:
            # Clean the content
            cleaned_content = self._clean_content(document.page_content)
            
            if not cleaned_content.strip():
                logger.warning("Empty document content after cleaning")
                return []
            
            # Create temporary document for text splitter
            temp_doc = Document(page_content=cleaned_content, metadata=document.metadata)
            
            # Use LangChain's text splitter
            chunks = self.text_splitter.split_documents([temp_doc])
            
            # Convert to enhanced format
            chunked_documents = []
            for i, chunk in enumerate(chunks):
                # Extract file information from metadata
                file_path = document.metadata.get("file_path", "")
                file_type = document.metadata.get("file_type", "")
                source = document.metadata.get("source", "unknown")
                
                # Create enhanced metadata
                chunk_metadata = ChunkMetadata(
                    source=source,
                    file_path=file_path,
                    file_type=file_type,
                    chunk_type="content",
                    language=self._detect_language(file_type),
                    contains_documentation=self._contains_documentation(chunk.page_content)
                )
                
                # Create enhanced document
                enhanced_doc = self._create_chunk_document(
                    content=chunk.page_content,
                    original_metadata=document.metadata,
                    chunk_metadata=chunk_metadata,
                    chunk_index=i,
                    total_chunks=len(chunks)
                )
                
                chunked_documents.append(enhanced_doc)
            
            logger.debug(f"Created {len(chunked_documents)} chunks using fallback chunker")
            return chunked_documents
            
        except Exception as e:
            logger.error(f"Error in fallback chunking: {str(e)}")
            return []
    
    def _detect_language(self, file_type: str) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            file_type: File extension
            
        Returns:
            Programming language name or 'text' for unknown types
        """
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'jsx',
            '.tsx': 'tsx',
            '.cs': 'csharp',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.sql': 'sql',
            '.sh': 'bash',
            '.ps1': 'powershell',
            '.rb': 'ruby',
            '.php': 'php',
            '.go': 'go',
            '.rs': 'rust',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.scala': 'scala',
            '.r': 'r',
            '.m': 'matlab',
            '.pl': 'perl'
        }
        
        return language_map.get(file_type.lower(), 'text')
    
    def _contains_documentation(self, content: str) -> bool:
        """
        Check if content contains documentation patterns.
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to contain documentation
        """
        doc_indicators = [
            '"""',  # Python docstrings
            "'''",  # Python docstrings
            '/**',  # JavaDoc, JSDoc
            '///',  # C# XML documentation
            '##',   # Markdown headers
            '@param',  # Parameter documentation
            '@return',  # Return documentation
            '@description',  # Description tags
            'TODO:',  # TODO comments
            'FIXME:',  # FIXME comments
            'NOTE:',  # Note comments
        ]
        
        content_lower = content.lower()
        return any(indicator.lower() in content_lower for indicator in doc_indicators)
