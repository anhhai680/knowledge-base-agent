"""
TypeScript-specific chunker that preserves semantic boundaries.

This chunker extends JavaScript chunker with TypeScript-specific features
using tree-sitter based parsing to identify TypeScript language constructs
and creates chunks that respect type, interface, and module boundaries.
"""

from typing import List, Optional, Dict, Any
from langchain.docstore.document import Document
from .javascript_chunker import JavaScriptChunker
from .base_chunker import ChunkMetadata
from .parsers.typescript_parser import TypeScriptAdvancedParser
from .parsers.semantic_element import SemanticElement, ElementType, ParseResult
from .parsers.advanced_parser import FallbackError, AdvancedParserError
from utils.logging import get_logger

logger = get_logger(__name__)


class TypeScriptChunker(JavaScriptChunker):
    """
    TypeScript-specific chunker that maintains semantic boundaries.
    
    Extends JavaScript chunker with TypeScript-specific features:
    - Type annotations and type aliases
    - Interface definitions
    - Enum declarations
    - Namespace/module declarations
    - Generic types and constraints
    - Decorators and metadata
    - Abstract classes
    - All JavaScript features with enhanced type information
    
    Falls back to JavaScript parsing or text-based chunking if TypeScript parsing fails.
    """
    
    def __init__(self, max_chunk_size: int = 1800, chunk_overlap: int = 75, use_advanced_parsing: bool = True):
        """
        Initialize TypeScript chunker.
        
        Args:
            max_chunk_size: Maximum size for chunks in characters
            chunk_overlap: Number of characters to overlap between chunks
            use_advanced_parsing: Whether to use tree-sitter advanced parsing
        """
        # Initialize as JavaScript chunker first
        super().__init__(max_chunk_size, chunk_overlap, use_advanced_parsing=False)
        
        # Override with TypeScript-specific configuration
        self.use_advanced_parsing = use_advanced_parsing
        
        # Initialize TypeScript advanced parser
        self.advanced_parser = None
        if self.use_advanced_parsing:
            try:
                self.advanced_parser = TypeScriptAdvancedParser({
                    'max_file_size_mb': 10,
                    'extract_types': True,
                    'preserve_interfaces': True,
                    'chunk_by_module': True,
                    'include_decorators': True,
                    'extract_generics': True,
                    'extract_exports': True,
                    'preserve_imports': True,
                    'handle_jsx': True,
                    'extract_comments': True
                })
                logger.info("TypeScript chunker initialized with tree-sitter advanced parsing")
            except Exception as e:
                logger.warning(f"Failed to initialize TypeScript advanced parser, falling back to JavaScript: {e}")
                # Fall back to JavaScript parser
                super().__init__(max_chunk_size, chunk_overlap, use_advanced_parsing=True)
    
    def get_supported_extensions(self) -> List[str]:
        """
        Return list of TypeScript file extensions.
        
        Returns:
            List of TypeScript file extensions
        """
        return ['.ts', '.tsx', '.d.ts']
    
    def _group_semantic_elements(self, elements: List[SemanticElement]) -> List[List[SemanticElement]]:
        """
        Group semantic elements into logical chunks for TypeScript.
        
        Args:
            elements: List of semantic elements from tree-sitter parsing
            
        Returns:
            List of element groups for chunking
        """
        groups = []
        current_group = []
        
        for element in elements:
            # TypeScript-specific grouping strategy:
            # 1. Group imports together
            # 2. Keep type definitions separate
            # 3. Group interfaces logically
            # 4. Keep exports with their content
            # 5. Separate classes and namespaces
            # 6. Group related functions and variables
            
            if element.element_type == ElementType.IMPORT:
                # Group imports together
                if current_group and any(e.element_type != ElementType.IMPORT for e in current_group):
                    groups.append(current_group)
                    current_group = [element]
                else:
                    current_group.append(element)
            
            elif element.element_type == ElementType.TYPE_ALIAS:
                # Type aliases can be grouped with related types or standalone
                if current_group and all(e.element_type in [ElementType.TYPE_ALIAS, ElementType.INTERFACE] for e in current_group):
                    current_group.append(element)
                    # Check if we should split based on size or if we have too many types
                    if self._estimate_group_size(current_group) > self.max_chunk_size * 0.6 or len(current_group) >= 3:
                        groups.append(current_group)
                        current_group = []
                else:
                    if current_group:
                        groups.append(current_group)
                    current_group = [element]
            
            elif element.element_type == ElementType.INTERFACE:
                # Interfaces can be grouped with related interfaces or type aliases
                if current_group and all(e.element_type in [ElementType.TYPE_ALIAS, ElementType.INTERFACE] for e in current_group):
                    current_group.append(element)
                    # Check if we should split based on size
                    if self._estimate_group_size(current_group) > self.max_chunk_size * 0.6:
                        groups.append(current_group)
                        current_group = []
                else:
                    if current_group:
                        groups.append(current_group)
                    current_group = [element]
            
            elif element.element_type == ElementType.ENUM:
                # Enums get their own chunk or can be grouped with related types
                if current_group and all(e.element_type in [ElementType.ENUM, ElementType.TYPE_ALIAS] for e in current_group):
                    current_group.append(element)
                else:
                    if current_group:
                        groups.append(current_group)
                    groups.append([element])
                    current_group = []
            
            elif element.element_type == ElementType.NAMESPACE:
                # Namespaces get their own chunk
                if current_group:
                    groups.append(current_group)
                    current_group = []
                
                # Process namespace but extract major types from it
                if element.children:
                    # Add namespace header if it has significant content
                    namespace_content = self._get_namespace_header_content(element)
                    if namespace_content and len(namespace_content.strip()) > 50:
                        groups.append([element])
                    
                    # Process each child separately based on type
                    type_group = []
                    class_group = []
                    
                    for child in element.children:
                        child.parent_name = element.name  # Set namespace as parent
                        
                        if child.element_type in [ElementType.TYPE_ALIAS, ElementType.INTERFACE]:
                            type_group.append(child)
                        elif child.element_type in [ElementType.CLASS, ElementType.ENUM]:
                            if type_group:
                                groups.append(type_group)
                                type_group = []
                            groups.append([child])
                        else:
                            class_group.append(child)
                    
                    # Add remaining groups
                    if type_group:
                        groups.append(type_group)
                    if class_group:
                        groups.append(class_group)
                else:
                    # Empty namespace
                    groups.append([element])
            
            elif element.element_type == ElementType.EXPORT:
                # Exports get their own group
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
                # Functions and variables can be grouped together
                current_group.append(element)
                
                # Check if we should start a new group based on size
                if self._estimate_group_size(current_group) > self.max_chunk_size * 0.8:
                    groups.append(current_group)
                    current_group = []
            
            elif element.element_type == ElementType.COMMENT:
                # Comments can be included with the next group if it's small
                if len(current_group) < 3:
                    current_group.append(element)
                else:
                    groups.append(current_group)
                    current_group = [element]
            
            else:
                # Other elements
                current_group.append(element)
        
        # Add the last group if it has content
        if current_group:
            groups.append(current_group)
        
        return groups if groups else [[]]
    
    def _create_semantic_chunk_document(self, content: str, original_doc: Document,
                                      elements: List[SemanticElement], chunk_index: str,
                                      total_chunks: int) -> Document:
        """
        Create a chunk document from semantic elements with TypeScript-specific metadata.
        
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
                file_type=original_doc.metadata.get('file_type', '.ts'),
                chunk_type="content",
                language="typescript"
            )
        else:
            # Use the first element to determine chunk characteristics
            primary_element = elements[0]
            
            # TypeScript-specific chunk type mapping
            chunk_type_map = {
                ElementType.IMPORT: "import",
                ElementType.EXPORT: "export",
                ElementType.TYPE_ALIAS: "type",
                ElementType.INTERFACE: "interface",
                ElementType.ENUM: "enum",
                ElementType.NAMESPACE: "namespace",
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
            
            # TypeScript-specific metadata
            has_generics = any(e.generic_parameters for e in elements)
            has_decorators = any(e.decorators for e in elements)
            
            chunk_metadata = ChunkMetadata(
                source=original_doc.metadata.get('source', 'unknown'),
                file_path=original_doc.metadata.get('file_path', 'unknown'),
                file_type=original_doc.metadata.get('file_type', '.ts'),
                chunk_type=chunk_type,
                symbol_name=primary_symbol,
                parent_symbol=parent_symbol,
                line_start=min(e.position.start_line for e in elements),
                line_end=max(e.position.end_line for e in elements),
                language="typescript",
                contains_documentation=has_docs,
                # Tree-sitter specific metadata
                semantic_elements=len(elements),
                element_types=[e.element_type.value for e in elements],
                parsing_method="tree-sitter",
                # TypeScript-specific metadata
                has_generics=has_generics,
                has_decorators=has_decorators,
                has_types=any(e.element_type in [ElementType.TYPE_ALIAS, ElementType.INTERFACE] for e in elements)
            )
        
        return self._create_chunk_document(
            content=content,
            original_metadata=original_doc.metadata,
            chunk_metadata=chunk_metadata,
            chunk_index=int(chunk_index.split('.')[0]),
            total_chunks=total_chunks
        )
    
    def _get_namespace_header_content(self, namespace_element: SemanticElement) -> str:
        """
        Extract just the namespace declaration header without its contents.
        
        Args:
            namespace_element: The namespace semantic element
            
        Returns:
            String containing just the namespace header
        """
        content = namespace_element.content
        if not content:
            return ""
        
        # Find the opening brace and return content up to that point
        lines = content.split('\n')
        header_lines = []
        
        for line in lines:
            header_lines.append(line)
            if '{' in line:
                break
        
        return '\n'.join(header_lines).strip()