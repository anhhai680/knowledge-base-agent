"""
Python-specific chunker that preserves semantic boundaries.

This chunker uses AST parsing to identify Python language constructs
and creates chunks that respect class and function boundaries.
"""

from typing import List
from langchain.docstore.document import Document

from .base_chunker import BaseChunker, ChunkMetadata
from .parsers.ast_parser import ASTParser, CodeElement

# Import the logger utility from the utils package
from ...utils.logging import get_logger

logger = get_logger(__name__)


class PythonChunker(BaseChunker):
    """
    Python-specific chunker that maintains semantic boundaries.
    
    Uses AST parsing to identify:
    - Import statements (grouped together)
    - Module docstrings
    - Class definitions with their methods
    - Standalone functions
    - Module-level code
    """
    
    def __init__(self, max_chunk_size: int = 1500, chunk_overlap: int = 100):
        """
        Initialize Python chunker.
        
        Args:
            max_chunk_size: Maximum size for chunks in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        super().__init__(max_chunk_size, chunk_overlap)
        self.parser = ASTParser()
        
        # Configuration for what to preserve
        self.preserve_imports = True
        self.preserve_docstrings = True
        self.preserve_class_methods = True
        self.group_related_functions = True
    
    def get_supported_extensions(self) -> List[str]:
        """
        Return list of Python file extensions.
        
        Returns:
            List of Python file extensions
        """
        return ['.py', '.pyx', '.pyi']
    
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Chunk Python document preserving semantic boundaries.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunked documents with enhanced metadata
        """
        try:
            # Clean the content
            cleaned_content = self._clean_content(document.page_content)
            
            if not cleaned_content.strip():
                logger.warning("Empty Python document content after cleaning")
                return []
            
            # Parse with AST
            elements = self.parser.parse_python_code(cleaned_content)
            
            if not elements:
                logger.warning("No semantic elements found, using fallback chunking")
                return self._fallback_chunk(document, cleaned_content)
            
            # Group elements into logical chunks
            chunk_groups = self._group_elements(elements)
            
            # Create documents from chunk groups
            chunked_documents = []
            for i, chunk_group in enumerate(chunk_groups):
                chunk_content = self._create_chunk_content(chunk_group, cleaned_content)
                
                if not chunk_content.strip():
                    continue
                
                # Check if chunk is too large and split if necessary
                if len(chunk_content) > self.max_chunk_size:
                    sub_chunks = self._split_oversized_python_chunk(chunk_content, chunk_group)
                    for j, sub_chunk in enumerate(sub_chunks):
                        if sub_chunk.strip():
                            sub_doc = self._create_chunk_document_from_group(
                                sub_chunk, document, chunk_group, f"{i}.{j}", len(chunk_groups)
                            )
                            chunked_documents.append(sub_doc)
                else:
                    chunk_doc = self._create_chunk_document_from_group(
                        chunk_content, document, chunk_group, str(i), len(chunk_groups)
                    )
                    chunked_documents.append(chunk_doc)
            
            logger.debug(f"Created {len(chunked_documents)} chunks from Python document")
            return chunked_documents
            
        except Exception as e:
            logger.error(f"Error in Python chunking: {str(e)}")
            # Ensure cleaned_content is available for fallback
            if 'cleaned_content' not in locals():
                cleaned_content = self._clean_content(document.page_content)
            return self._fallback_chunk(document, cleaned_content)
    
    def _group_elements(self, elements: List[CodeElement]) -> List[List[CodeElement]]:
        """
        Group code elements into logical chunks.
        
        Args:
            elements: List of code elements from AST parser
            
        Returns:
            List of element groups representing chunks
        """
        groups = []
        current_group = []
        
        # Sort elements by start line
        sorted_elements = sorted(elements, key=lambda x: x.start_line)
        
        for element in sorted_elements:
            # Start new group for certain element types
            if self._should_start_new_group(element, current_group):
                if current_group:
                    groups.append(current_group)
                current_group = [element]
            else:
                current_group.append(element)
        
        # Add the last group if it exists
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _should_start_new_group(self, element: CodeElement, current_group: List[CodeElement]) -> bool:
        """
        Determine if element should start a new chunk group.
        
        Args:
            element: Code element to check
            current_group: Current group of elements
            
        Returns:
            True if element should start a new group
        """
        if not current_group:
            return True
        
        # Always group imports together
        if element.element_type == "import":
            return not any(e.element_type == "import" for e in current_group)
        
        # Module docstring should be separate or with imports
        if element.element_type == "module":
            return not any(e.element_type in ["import", "module"] for e in current_group)
        
        # Classes should typically start new groups unless very small
        if element.element_type == "class":
            return True
        
        # Methods belong with their class
        if element.element_type in ["method", "async_method"]:
            return not any(e.element_type == "class" and e.name == element.parent for e in current_group)
        
        # Functions can be grouped if they're small
        if element.element_type in ["function", "async_function"]:
            # Estimate current group size
            current_size = sum(len(e.content) for e in current_group)
            element_size = len(element.content)
            
            # Start new group if adding this would exceed size limit
            return current_size + element_size > self.max_chunk_size * 0.8
        
        return False
    
    def _create_chunk_content(self, elements: List[CodeElement], source_code: str) -> str:
        """
        Create content string from elements.
        
        Args:
            elements: List of code elements
            source_code: Original source code
            
        Returns:
            Combined content string
        """
        if not elements:
            return ""
        
        # Sort by line number
        sorted_elements = sorted(elements, key=lambda x: x.start_line)
        
        # Combine content with proper spacing
        content_parts = []
        for element in sorted_elements:
            if element.content.strip():
                content_parts.append(element.content)
        
        return "\n\n".join(content_parts)
    
    def _create_chunk_document_from_group(
        self,
        content: str,
        original_document: Document,
        elements: List[CodeElement],
        chunk_index: str,
        total_chunks: int
    ) -> Document:
        """
        Create document from element group.
        
        Args:
            content: Chunk content
            original_document: Original document
            elements: List of elements in this chunk
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks
            
        Returns:
            Document with enhanced metadata
        """
        # Determine primary element type and symbol name
        primary_element = elements[0] if elements else None
        symbol_names = [e.name for e in elements if e.name not in ["__module__", "__imports__"]]
        
        # Create metadata
        file_path = original_document.metadata.get("file_path", "")
        file_type = original_document.metadata.get("file_type", ".py")
        source = original_document.metadata.get("source", "unknown")
        
        chunk_metadata = ChunkMetadata(
            source=source,
            file_path=file_path,
            file_type=file_type,
            chunk_type=primary_element.element_type if primary_element else "content",
            symbol_name=primary_element.name if primary_element else None,
            parent_symbol=primary_element.parent if primary_element else None,
            line_start=min(e.start_line for e in elements) if elements else None,
            line_end=max(e.end_line for e in elements) if elements else None,
            language="python",
            contains_documentation=any(e.docstring for e in elements),
            symbols=symbol_names,
            element_count=len(elements)
        )
        
        return self._create_chunk_document(
            content=content,
            original_metadata=original_document.metadata,
            chunk_metadata=chunk_metadata,
            chunk_index=int(chunk_index.split('.')[0]) if '.' in str(chunk_index) else int(chunk_index),
            total_chunks=total_chunks
        )
    
    def _split_oversized_python_chunk(self, content: str, elements: List[CodeElement]) -> List[str]:
        """
        Split oversized chunk while preserving element boundaries.
        
        Args:
            content: Content to split
            elements: Elements in the content
            
        Returns:
            List of split content chunks
        """
        # If we have multiple elements, try to split by elements
        if len(elements) > 1:
            chunks = []
            current_chunk = ""
            
            for element in sorted(elements, key=lambda x: x.start_line):
                element_content = element.content
                
                # If adding this element would exceed size, start new chunk
                if current_chunk and len(current_chunk) + len(element_content) > self.max_chunk_size:
                    chunks.append(current_chunk)
                    current_chunk = element_content
                else:
                    if current_chunk:
                        current_chunk += "\n\n" + element_content
                    else:
                        current_chunk = element_content
            
            if current_chunk:
                chunks.append(current_chunk)
            
            return chunks
        else:
            # Single element is too large, use parent class method
            dummy_metadata = ChunkMetadata(
                source="", file_path="", file_type=".py", language="python"
            )
            return super()._split_oversized_chunk(content, dummy_metadata)
    
    def _fallback_chunk(self, document: Document, content: str) -> List[Document]:
        """
        Fallback to simple text chunking when AST parsing fails.
        
        Args:
            document: Original document
            content: Content to chunk
            
        Returns:
            List of simply chunked documents
        """
        from .fallback_chunker import FallbackChunker
        
        fallback_chunker = FallbackChunker(self.max_chunk_size, self.chunk_overlap)
        temp_doc = Document(page_content=content, metadata=document.metadata)
        return fallback_chunker.chunk_document(temp_doc)
