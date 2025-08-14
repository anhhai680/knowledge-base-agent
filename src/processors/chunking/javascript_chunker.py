"""
JavaScript-specific chunker that preserves semantic boundaries.

This chunker uses tree-sitter based parsing to identify JavaScript language constructs
and creates chunks that respect module, class, and function boundaries.
"""

from typing import List, Optional, Dict, Any
from langchain.docstore.document import Document
from .base_chunker import BaseChunker, ChunkMetadata
from .parsers.javascript_parser import JavaScriptAdvancedParser
from .parsers.semantic_element import SemanticElement, ElementType, ParseResult
from .parsers.advanced_parser import FallbackError, AdvancedParserError
from utils.logging import get_logger

logger = get_logger(__name__)


class JavaScriptChunker(BaseChunker):
    """
    JavaScript-specific chunker that maintains semantic boundaries.
    
    Uses tree-sitter advanced parsing to identify:
    - Import/export statements
    - Class definitions with their methods
    - Function declarations and expressions
    - Variable declarations (const, let, var)
    - Arrow functions and async functions
    - JSX components (when enabled)
    - JSDoc comments
    
    Falls back to text-based chunking if tree-sitter parsing fails.
    """
    
    def __init__(self, max_chunk_size: int = 1500, chunk_overlap: int = 100, use_advanced_parsing: bool = True):
        """
        Initialize JavaScript chunker.
        
        Args:
            max_chunk_size: Maximum size for chunks in characters
            chunk_overlap: Number of characters to overlap between chunks
            use_advanced_parsing: Whether to use tree-sitter advanced parsing
        """
        super().__init__(max_chunk_size, chunk_overlap)
        
        # Configuration
        self.use_advanced_parsing = use_advanced_parsing
        
        # Initialize advanced parser
        self.advanced_parser = None
        if self.use_advanced_parsing:
            try:
                self.advanced_parser = JavaScriptAdvancedParser({
                    'max_file_size_mb': 10,
                    'extract_exports': True,
                    'preserve_imports': True,
                    'chunk_by_function': True,
                    'handle_jsx': True,
                    'extract_comments': True
                })
                logger.info("JavaScript chunker initialized with tree-sitter advanced parsing")
            except Exception as e:
                logger.warning(f"Failed to initialize JavaScript advanced parser, falling back to text chunking: {e}")
                self.use_advanced_parsing = False
    
    def get_supported_extensions(self) -> List[str]:
        """
        Return list of JavaScript file extensions.
        
        Returns:
            List of JavaScript file extensions
        """
        return ['.js', '.mjs', '.jsx']
    
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Chunk JavaScript document preserving semantic boundaries.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunked documents with enhanced metadata
        """
        try:
            # Clean the content
            cleaned_content = self._clean_content(document.page_content)
            
            if not cleaned_content.strip():
                logger.warning("Empty JavaScript document content after cleaning")
                return []
            
            # Try advanced parsing first
            if self.use_advanced_parsing and self.advanced_parser:
                try:
                    return self._chunk_with_advanced_parsing(document, cleaned_content)
                except (FallbackError, AdvancedParserError) as e:
                    logger.warning(f"Advanced parsing failed, falling back to text chunking: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error in advanced parsing: {e}")
            
            # Fall back to text-based chunking
            logger.info("Using text-based JavaScript chunking")
            return self._fallback_chunk(document, cleaned_content)
            
        except Exception as e:
            logger.error(f"Error in JavaScript chunking: {str(e)}")
            # Ultimate fallback - simple text chunking
            return self._fallback_chunk(document, cleaned_content)
    
    def _chunk_with_advanced_parsing(self, document: Document, content: str) -> List[Document]:
        """
        Chunk JavaScript document using tree-sitter advanced parsing.
        
        Args:
            document: Original document
            content: Cleaned content to parse
            
        Returns:
            List of chunked documents
        """
        # Parse with tree-sitter
        file_path = document.metadata.get('file_path', 'unknown.js')
        parse_result = self.advanced_parser.parse(content, file_path)
        
        if not parse_result.success:
            raise FallbackError(f"Advanced parsing failed: {'; '.join(parse_result.errors)}")
        
        if not parse_result.elements:
            logger.warning("No semantic elements extracted from JavaScript code")
            raise FallbackError("No semantic elements found")
        
        # Convert semantic elements to chunks
        chunked_documents = []
        element_groups = self._group_semantic_elements(parse_result.elements)
        
        for i, group in enumerate(element_groups):
            chunk_content = self._create_chunk_from_semantic_elements(group, content)
            
            if not chunk_content.strip():
                continue
            
            # Check if chunk is too large and split if necessary
            if len(chunk_content) > self.max_chunk_size:
                sub_chunks = self._split_oversized_chunk(chunk_content, group[0] if group else None)
                for j, sub_chunk in enumerate(sub_chunks):
                    if sub_chunk.strip():
                        sub_doc = self._create_semantic_chunk_document(
                            sub_chunk, document, group, f"{i}.{j}", len(element_groups)
                        )
                        chunked_documents.append(sub_doc)
            else:
                chunk_doc = self._create_semantic_chunk_document(
                    chunk_content, document, group, str(i), len(element_groups)
                )
                chunked_documents.append(chunk_doc)
        
        logger.debug(f"Created {len(chunked_documents)} chunks from JavaScript document using tree-sitter")
        return chunked_documents
    
    def _group_semantic_elements(self, elements: List[SemanticElement]) -> List[List[SemanticElement]]:
        """
        Group semantic elements into logical chunks for JavaScript.
        
        Args:
            elements: List of semantic elements from tree-sitter parsing
            
        Returns:
            List of element groups for chunking
        """
        groups = []
        current_group = []
        
        for element in elements:
            # JavaScript-specific grouping strategy:
            # 1. Group imports together
            # 2. Keep exports with their content
            # 3. Group related functions
            # 4. Separate classes
            # 5. Group variable declarations
            
            if element.element_type == ElementType.IMPORT:
                # Group imports together
                if current_group and any(e.element_type != ElementType.IMPORT for e in current_group):
                    groups.append(current_group)
                    current_group = [element]
                else:
                    current_group.append(element)
            
            elif element.element_type == ElementType.EXPORT:
                # Exports usually include their content, so they get their own group
                if current_group:
                    groups.append(current_group)
                    current_group = []
                
                groups.append([element])
            
            elif element.element_type == ElementType.CLASS:
                # Classes get their own chunk
                if current_group:
                    groups.append(current_group)
                    current_group = []
                
                groups.append([element])
            
            elif element.element_type in [ElementType.FUNCTION, ElementType.VARIABLE, ElementType.CONSTANT]:
                # Functions and variables can be grouped together if they're small, otherwise separate
                if element.element_type == ElementType.FUNCTION and len(element.content) > self.max_chunk_size * 0.5:
                    # Large functions get their own chunk
                    if current_group:
                        groups.append(current_group)
                        current_group = []
                    groups.append([element])
                else:
                    current_group.append(element)
                    
                    # Check if we should start a new group based on size
                    if self._estimate_group_size(current_group) > self.max_chunk_size * 0.8:
                        groups.append(current_group)
                        current_group = []
            
            elif element.element_type == ElementType.COMMENT:
                # Comments should not dominate the chunk type - only include if current group is small
                if len(current_group) == 0:
                    current_group.append(element)
                elif len(current_group) == 1 and current_group[0].element_type == ElementType.COMMENT:
                    current_group.append(element)
                else:
                    # Start a new group for the comment
                    groups.append(current_group)
                    current_group = [element]
            
            else:
                # Other elements
                current_group.append(element)
        
        # Add the last group if it has content
        if current_group:
            groups.append(current_group)
        
        return groups if groups else [[]]
    
    def _create_chunk_from_semantic_elements(self, elements: List[SemanticElement], source_code: str) -> str:
        """
        Create chunk content from semantic elements.
        
        Args:
            elements: List of semantic elements to include in chunk
            source_code: Original source code
            
        Returns:
            String content for the chunk
        """
        if not elements:
            return ""
        
        # Sort elements by position
        sorted_elements = sorted(elements, key=lambda e: e.position.start_byte)
        
        # Extract content for each element
        content_parts = []
        
        for element in sorted_elements:
            element_content = element.content.strip()
            if element_content:
                content_parts.append(element_content)
        
        return '\n\n'.join(content_parts)
    
    def _create_semantic_chunk_document(self, content: str, original_doc: Document,
                                      elements: List[SemanticElement], chunk_index: str,
                                      total_chunks: int) -> Document:
        """
        Create a chunk document from semantic elements.
        
        Args:
            content: Chunk content
            original_doc: Original document
            elements: Semantic elements in this chunk
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks
            
        Returns:
            Document with enhanced metadata
        """
        if not elements:
            # Fallback metadata
            chunk_metadata = ChunkMetadata(
                source=original_doc.metadata.get('source', 'unknown'),
                file_path=original_doc.metadata.get('file_path', 'unknown'),
                file_type=original_doc.metadata.get('file_type', '.js'),
                chunk_type="content",
                language="javascript"
            )
        else:
            # Use the first element to determine chunk characteristics
            primary_element = elements[0]
            
            # Determine chunk type based on primary element
            chunk_type_map = {
                ElementType.IMPORT: "import",
                ElementType.EXPORT: "export",
                ElementType.CLASS: "class",
                ElementType.FUNCTION: "function",
                ElementType.METHOD: "method",
                ElementType.VARIABLE: "variable",
                ElementType.CONSTANT: "constant",
                ElementType.COMMENT: "comment"
            }
            
            chunk_type = chunk_type_map.get(primary_element.element_type, "content")
            
            # Collect all symbol names
            symbol_names = [e.name for e in elements if e.name and e.name != "comment"]
            primary_symbol = symbol_names[0] if symbol_names else None
            
            # Find parent context
            parent_symbol = None
            for element in elements:
                if element.parent_name:
                    parent_symbol = element.parent_name
                    break
            
            # Check for documentation
            has_docs = any(e.has_documentation for e in elements)
            
            chunk_metadata = ChunkMetadata(
                source=original_doc.metadata.get('source', 'unknown'),
                file_path=original_doc.metadata.get('file_path', 'unknown'),
                file_type=original_doc.metadata.get('file_type', '.js'),
                chunk_type=chunk_type,
                symbol_name=primary_symbol,
                parent_symbol=parent_symbol,
                line_start=min(e.position.start_line for e in elements),
                line_end=max(e.position.end_line for e in elements),
                language="javascript",
                contains_documentation=has_docs,
                # Tree-sitter specific metadata
                semantic_elements=len(elements),
                element_types=[e.element_type.value for e in elements],
                parsing_method="tree-sitter"
            )
        
        return self._create_chunk_document(
            content=content,
            original_metadata=original_doc.metadata,
            chunk_metadata=chunk_metadata,
            chunk_index=int(chunk_index.split('.')[0]),
            total_chunks=total_chunks
        )
    
    def _estimate_group_size(self, elements: List[SemanticElement]) -> int:
        """
        Estimate the size of a group of semantic elements.
        
        Args:
            elements: List of semantic elements
            
        Returns:
            Estimated size in characters
        """
        total_size = 0
        for element in elements:
            total_size += len(element.content)
        return total_size
    
    def _fallback_chunk(self, document: Document, content: str) -> List[Document]:
        """
        Create chunks using fallback text-based chunking.
        
        Args:
            document: Original document
            content: Content to chunk
            
        Returns:
            List of fallback chunks
        """
        from .fallback_chunker import FallbackChunker
        temp_doc = Document(page_content=content, metadata=document.metadata)
        fallback_chunker = FallbackChunker(self.max_chunk_size, self.chunk_overlap)
        return fallback_chunker.chunk_document(temp_doc)