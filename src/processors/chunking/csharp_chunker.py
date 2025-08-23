"""
C#-specific chunker that preserves semantic boundaries.

This chunker uses tree-sitter based parsing to identify C# language constructs
and creates chunks that respect namespace, class, and method boundaries.
Falls back to regex-based parsing if tree-sitter fails.
"""

import re
from typing import List, Optional, NamedTuple
from langchain.docstore.document import Document
from .base_chunker import BaseChunker, ChunkMetadata
from .parsers.csharp_parser import CSharpAdvancedParser
from .parsers.semantic_element import SemanticElement, ElementType
from .parsers.advanced_parser import FallbackError, AdvancedParserError
from ...utils.logging import get_logger
from ...config.settings import settings

logger = get_logger(__name__)


class CSharpElement(NamedTuple):
    """Represents a C# code element (legacy compatibility)."""
    
    name: str
    element_type: str  # 'namespace', 'class', 'method', 'property', 'using'
    start_line: int
    end_line: int
    content: str
    parent: Optional[str] = None
    access_modifier: Optional[str] = None


class CSharpChunker(BaseChunker):
    """
    C#-specific chunker that maintains semantic boundaries.
    
    Uses tree-sitter advanced parsing to identify:
    - Using statements (grouped together)
    - Namespace declarations
    - Class definitions with their members
    - Methods and properties
    - Interface definitions
    - XML documentation comments
    - Attributes and decorators
    
    Falls back to regex-based parsing if tree-sitter parsing fails.
    """
    
    def __init__(self, max_chunk_size: int = 2000, chunk_overlap: int = 50, use_advanced_parsing: Optional[bool] = None):
        """
        Initialize C# chunker.
        
        Args:
            max_chunk_size: Maximum size for chunks in characters
            chunk_overlap: Number of characters to overlap between chunks
            use_advanced_parsing: Whether to use tree-sitter advanced parsing. If None, uses environment variable USE_ADVANCED_PARSING.
        """
        super().__init__(max_chunk_size, chunk_overlap)
        
        # Configuration
        # Use environment variable if not explicitly provided
        if use_advanced_parsing is None:
            self.use_advanced_parsing = settings.use_advanced_parsing
        else:
            self.use_advanced_parsing = use_advanced_parsing
        
        # Initialize advanced parser
        self.advanced_parser = None
        if self.use_advanced_parsing:
            try:
                self.advanced_parser = CSharpAdvancedParser({
                    'max_file_size_mb': 10,
                    'extract_documentation': True,
                    'extract_attributes': True,
                    'include_using_statements': True,
                    'preserve_namespaces': True,
                    'chunk_by_class': True
                })
                logger.info("C# chunker initialized with tree-sitter advanced parsing")
            except Exception as e:
                logger.error(f"Failed to initialize C# advanced parser, falling back to regex: {e}")
                self.use_advanced_parsing = False
        
        # C# language patterns
        self.using_pattern = re.compile(r'^\s*using\s+[^;]+;', re.MULTILINE)
        self.namespace_pattern = re.compile(r'^\s*namespace\s+([^\s{]+)', re.MULTILINE)
        # Updated class pattern to handle partial classes and other modifiers
        self.class_pattern = re.compile(r'^\s*(public|private|protected|internal)?\s*(abstract|sealed|static|partial|readonly|record)?\s*(class|interface|struct|enum|record)\s+(\w+)', re.MULTILINE)
        # Updated method pattern to handle more C# syntax
        self.method_pattern = re.compile(r'^\s*(public|private|protected|internal)?\s*(static|virtual|override|abstract|partial|async|sealed)?\s*(\w+(?:\[\])?)\s+(\w+)\s*\([^{]*\)\s*{?', re.MULTILINE)
        # Updated property pattern to handle more C# syntax
        self.property_pattern = re.compile(r'^\s*(public|private|protected|internal)?\s*(static|virtual|override|abstract|partial|readonly)?\s*(\w+(?:\[\])?)\s+(\w+)\s*{\s*(get|set)', re.MULTILINE)
        # Constructor pattern
        self.constructor_pattern = re.compile(r'^\s*(public|private|protected|internal)?\s*(\w+)\s*\([^{]*\)\s*{?', re.MULTILINE)
    
    def get_supported_extensions(self) -> List[str]:
        """
        Return list of C# file extensions.
        
        Returns:
            List of C# file extensions
        """
        return ['.cs']
    
    def _should_use_advanced_parsing(self, content: str) -> bool:
        """
        Determine if advanced parsing should be used for this content.
        
        Args:
            content: C# source code content
            
        Returns:
            True if advanced parsing should be attempted
        """
        if not self.use_advanced_parsing or not self.advanced_parser:
            return False
        
        # Check for very large files that might cause memory issues
        if len(content) > 1000000:  # Files larger than 1MB
            logger.info("File too large for advanced parsing, using regex fallback")
            return False
        
        return True
    
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Chunk C# document preserving semantic boundaries.
        
        Args:
            document: Document to chunk
            
        Returns:
            List of chunked documents with enhanced metadata
        """
        try:
            # Clean the content
            cleaned_content = self._clean_content(document.page_content)
            
            if not cleaned_content.strip():
                logger.warning("Empty C# document content after cleaning")
                return []
            
            # Log file information for debugging
            file_path = document.metadata.get('file_path', 'unknown.cs')
            logger.debug(f"Processing C# file: {file_path} (size: {len(cleaned_content)} chars)")
            
            # Try advanced parsing first
            if self._should_use_advanced_parsing(cleaned_content):
                logger.info(f"Attempting tree-sitter parsing for {file_path}")
                try:
                    return self._chunk_with_advanced_parsing(document, cleaned_content)
                except (FallbackError, AdvancedParserError) as e:
                    logger.warning(f"Advanced parsing failed for {file_path}, falling back to regex: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error in advanced parsing for {file_path}: {e}")
            
            # Fall back to regex-based parsing
            logger.info(f"Using regex-based C# parsing for {file_path}")
            return self._chunk_with_regex_parsing(document, cleaned_content)
            
        except Exception as e:
            logger.error(f"Error in C# chunking for {document.metadata.get('file_path', 'unknown')}: {str(e)}")
            # Ultimate fallback - simple text chunking
            return self._fallback_chunk(document, cleaned_content)
    
    def _chunk_with_advanced_parsing(self, document: Document, content: str) -> List[Document]:
        """
        Chunk C# document using tree-sitter advanced parsing.
        
        Args:
            document: Original document
            content: Cleaned content to parse
            
        Returns:
            List of chunked documents
        """
        try:
            # Parse with tree-sitter
            file_path = document.metadata.get('file_path', 'unknown.cs')
            parse_result = self.advanced_parser.parse(content, file_path)
            
            if not parse_result.success:
                logger.warning(f"Advanced parsing failed: {'; '.join(parse_result.errors)}")
                raise FallbackError(f"Advanced parsing failed: {'; '.join(parse_result.errors)}")
            
            if not parse_result.elements:
                logger.warning("No semantic elements extracted from C# code")
                raise FallbackError("No semantic elements found")
            
            # Validate that we have usable elements (with valid content)
            valid_elements = [e for e in parse_result.elements if e.content and e.content.strip()]
            if not valid_elements:
                logger.warning("No valid semantic elements with content found, falling back to regex")
                raise FallbackError("No valid semantic elements with content")
            
            # Convert semantic elements to chunks
            chunked_documents = []
            element_groups = self._group_semantic_elements(valid_elements)
            
            for i, group in enumerate(element_groups):
                if not group:  # Skip empty groups
                    continue
                    
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
            
            if not chunked_documents:
                logger.warning("No valid chunks created from semantic elements, falling back to regex")
                raise FallbackError("No valid chunks created")
            
            logger.debug(f"Created {len(chunked_documents)} chunks from C# document using tree-sitter")
            return chunked_documents
            
        except (FallbackError, AdvancedParserError) as e:
            # Re-raise these specific errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error in advanced parsing: {e}")
            raise FallbackError(f"Advanced parsing failed with unexpected error: {e}")
    
    def _chunk_with_regex_parsing(self, document: Document, content: str) -> List[Document]:
        """
        Chunk C# document using legacy regex-based parsing.
        
        Args:
            document: Original document
            content: Cleaned content to parse
            
        Returns:
            List of chunked documents
        """
        # Parse C# elements using regex
        elements = self._parse_csharp_code(content)
        
        if not elements:
            logger.warning("No C# semantic elements found, using fallback chunking")
            return self._fallback_chunk(document, content)
        
        # Group elements into logical chunks
        chunk_groups = self._group_csharp_elements(elements)
        
        # Create documents from chunk groups
        chunked_documents = []
        for i, chunk_group in enumerate(chunk_groups):
            chunk_content = self._create_chunk_content(chunk_group, content)
            
            if not chunk_content.strip():
                continue
            
            # Check if chunk is too large and split if necessary
            if len(chunk_content) > self.max_chunk_size:
                sub_chunks = self._split_csharp_chunk(chunk_content, chunk_group)
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
        
        logger.debug(f"Created {len(chunked_documents)} chunks from C# document using regex")
        return chunked_documents
    
    def _group_semantic_elements(self, elements: List[SemanticElement]) -> List[List[SemanticElement]]:
        """
        Group semantic elements into logical chunks.
        
        Args:
            elements: List of semantic elements from tree-sitter parsing
            
        Returns:
            List of element groups for chunking
        """
        groups = []
        current_group = []
        
        for element in elements:
            # Group strategy:
            # 1. Group using statements together
            # 2. Extract classes from namespaces and make them separate chunks
            # 3. Group standalone functions/variables
            # 4. Keep small structural elements together
            
            if element.element_type == ElementType.USING:
                # Start a new group for using statements if current group has non-using elements
                if current_group and any(e.element_type != ElementType.USING for e in current_group):
                    groups.append(current_group)
                    current_group = [element]
                else:
                    current_group.append(element)
            
            elif element.element_type in [ElementType.CLASS, ElementType.INTERFACE, ElementType.STRUCT, ElementType.ENUM]:
                # Classes and similar types get their own chunks
                if current_group:
                    groups.append(current_group)
                    current_group = []
                
                # Add this element as its own group
                groups.append([element])
            
            elif element.element_type == ElementType.NAMESPACE:
                # Process namespace but extract classes from it
                if current_group:
                    groups.append(current_group)
                    current_group = []
                
                # If namespace has children (classes, interfaces, etc.), extract them
                if element.children:
                    # Add namespace header as its own chunk if it has significant content
                    namespace_content = self._get_namespace_header_content(element)
                    if namespace_content and len(namespace_content.strip()) > 50:
                        groups.append([element])
                    
                    # Process each child separately
                    for child in element.children:
                        if child.element_type in [ElementType.CLASS, ElementType.INTERFACE, ElementType.STRUCT, ElementType.ENUM]:
                            # Set the namespace as parent for context
                            child.parent_name = element.name
                            groups.append([child])
                        else:
                            # Other elements can be grouped together
                            current_group.append(child)
                else:
                    # Empty namespace or namespace without extracted children
                    groups.append([element])
            
            else:
                # Other elements (functions, variables, etc.) can be grouped together
                current_group.append(element)
                
                # Check if current group is getting too large
                if self._estimate_group_size(current_group) > self.max_chunk_size * 0.8:
                    groups.append(current_group)
                    current_group = []
        
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
            # For elements with children, the content already includes children
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
                file_type=".cs",
                chunk_type="content",
                language="csharp"
            )
        else:
            # Use the first element to determine chunk characteristics
            primary_element = elements[0]
            
            # Determine chunk type based on primary element
            chunk_type_map = {
                ElementType.USING: "using",
                ElementType.NAMESPACE: "namespace",
                ElementType.CLASS: "class",
                ElementType.INTERFACE: "interface",
                ElementType.STRUCT: "struct",
                ElementType.ENUM: "enum",
                ElementType.METHOD: "method",
                ElementType.PROPERTY: "property",
                ElementType.FIELD: "field",
                ElementType.CONSTRUCTOR: "constructor"
            }
            
            chunk_type = chunk_type_map.get(primary_element.element_type, "content")
            
            # Collect all symbol names
            symbol_names = [e.name for e in elements if e.name]
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
                file_type=".cs",
                chunk_type=chunk_type,
                symbol_name=primary_symbol,
                parent_symbol=parent_symbol,
                line_start=min(e.position.start_line for e in elements),
                line_end=max(e.position.end_line for e in elements),
                language="csharp",
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
    
    def _parse_csharp_code(self, code: str) -> List[CSharpElement]:
        """
        Parse C# code and extract semantic elements.
        
        Args:
            code: C# source code to parse
            
        Returns:
            List of CSharpElement objects representing semantic chunks
        """
        elements = []
        lines = code.split('\n')
        
        try:
            # Find using statements
            using_lines = []
            for i, line in enumerate(lines, 1):
                if self.using_pattern.match(line):
                    using_lines.append(i)
            
            if using_lines:
                using_content = '\n'.join(lines[using_lines[0]-1:using_lines[-1]])
                elements.append(CSharpElement(
                    name="__usings__",
                    element_type="using",
                    start_line=using_lines[0],
                    end_line=using_lines[-1],
                    content=using_content
                ))
            
            # Find namespaces with improved pattern matching
            namespace_matches = list(self.namespace_pattern.finditer(code))
            for match in namespace_matches:
                namespace_name = match.group(1)
                start_line = code[:match.start()].count('\n') + 1
                
                # Find the end of namespace using balanced brace counting
                namespace_start = match.start()
                brace_count = 0
                in_string = False
                in_comment = False
                namespace_end = len(code)
                
                for i, char in enumerate(code[namespace_start:], namespace_start):
                    if char == '"' and (i == 0 or code[i-1] != '\\'):
                        in_string = not in_string
                    elif char == '/' and i + 1 < len(code) and code[i+1] == '/' and not in_string:
                        in_comment = True
                    elif char == '\n' and in_comment:
                        in_comment = False
                    elif not in_string and not in_comment:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                namespace_end = i + 1
                                break
                
                end_line = code[:namespace_end].count('\n') + 1
                namespace_content = code[namespace_start:namespace_end]
                
                elements.append(CSharpElement(
                    name=namespace_name,
                    element_type="namespace",
                    start_line=start_line,
                    end_line=end_line,
                    content=namespace_content
                ))
            
            # Find classes, interfaces, structs, enums with improved pattern matching
            class_matches = list(self.class_pattern.finditer(code))
            for match in class_matches:
                access_modifier = match.group(1) or "internal"
                # Handle additional modifiers (abstract, sealed, static, partial, readonly, record)
                additional_modifiers = match.group(2) or ""
                class_type = match.group(3)
                class_name = match.group(4)
                start_line = code[:match.start()].count('\n') + 1
                
                # Find class body using balanced brace counting
                class_start = match.start()
                brace_count = 0
                in_string = False
                in_comment = False
                class_end = len(code)
                
                for i, char in enumerate(code[class_start:], class_start):
                    if char == '"' and (i == 0 or code[i-1] != '\\'):
                        in_string = not in_string
                    elif char == '/' and i + 1 < len(code) and code[i+1] == '/' and not in_string:
                        in_comment = True
                    elif char == '\n' and in_comment:
                        in_comment = False
                    elif not in_string and not in_comment:
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                class_end = i + 1
                                break
                
                end_line = code[:class_end].count('\n') + 1
                class_content = code[class_start:class_end]
                
                elements.append(CSharpElement(
                    name=class_name,
                    element_type=class_type,
                    start_line=start_line,
                    end_line=end_line,
                    content=class_content,
                    access_modifier=access_modifier
                ))
            
            # Find methods within classes (improved pattern)
            method_matches = list(self.method_pattern.finditer(code))
            for match in method_matches:
                access_modifier = match.group(1) or "private"
                # Handle additional modifiers (static, virtual, override, abstract, partial, async, sealed)
                additional_modifiers = match.group(2) or ""
                return_type = match.group(3)
                method_name = match.group(4)
                start_line = code[:match.start()].count('\n') + 1
                
                # Find method body using balanced brace counting
                method_start = match.end()
                if code[method_start-1:method_start] == '{':
                    brace_count = 1
                    method_end = method_start
                    
                    for i, char in enumerate(code[method_start:], method_start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                method_end = i + 1
                                break
                    
                    end_line = code[:method_end].count('\n') + 1
                    method_content = code[match.start():method_end]
                    
                    elements.append(CSharpElement(
                        name=method_name,
                        element_type="method",
                        start_line=start_line,
                        end_line=end_line,
                        content=method_content,
                        access_modifier=access_modifier
                    ))
            
            # Find constructors
            constructor_matches = list(self.constructor_pattern.finditer(code))
            for match in constructor_matches:
                access_modifier = match.group(1) or "private"
                constructor_name = match.group(2)
                start_line = code[:match.start()].count('\n') + 1
                
                # Find constructor body using balanced brace counting
                constructor_start = match.end()
                if code[constructor_start-1:constructor_start] == '{':
                    brace_count = 1
                    constructor_end = constructor_start
                    
                    for i, char in enumerate(code[constructor_start:], constructor_start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                constructor_end = i + 1
                                break
                    
                    end_line = code[:constructor_end].count('\n') + 1
                    constructor_content = code[match.start():constructor_end]
                    
                    elements.append(CSharpElement(
                        name=constructor_name,
                        element_type="constructor",
                        start_line=start_line,
                        end_line=end_line,
                        content=constructor_content,
                        access_modifier=access_modifier
                    ))
            
            # Sort elements by line number
            elements = sorted(elements, key=lambda x: x.start_line)
            
        except Exception as e:
            logger.warning(f"Error during regex-based C# parsing: {e}")
            # Return minimal elements to avoid complete failure
            if not elements:
                # Create a single element for the entire file
                elements.append(CSharpElement(
                    name="__file__",
                    element_type="content",
                    start_line=1,
                    end_line=len(lines),
                    content=code
                ))
        
        return elements
    
    def _group_csharp_elements(self, elements: List[CSharpElement]) -> List[List[CSharpElement]]:
        """
        Group C# elements into logical chunks.
        
        Args:
            elements: List of C# elements
            
        Returns:
            List of element groups representing chunks
        """
        groups = []
        current_group = []
        
        for element in elements:
            # Start new group for certain element types
            if self._should_start_new_csharp_group(element, current_group):
                if current_group:
                    groups.append(current_group)
                current_group = [element]
            else:
                current_group.append(element)
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _should_start_new_csharp_group(self, element: CSharpElement, current_group: List[CSharpElement]) -> bool:
        """
        Determine if element should start a new chunk group.
        
        Args:
            element: C# element to check
            current_group: Current group of elements
            
        Returns:
            True if element should start a new group
        """
        if not current_group:
            return True
        
        # Group using statements together
        if element.element_type == "using":
            return not any(e.element_type == "using" for e in current_group)
        
        # Namespaces should be with usings or start new group
        if element.element_type == "namespace":
            return not any(e.element_type in ["using", "namespace"] for e in current_group)
        
        # Classes/interfaces should typically start new groups
        if element.element_type in ["class", "interface", "struct", "enum"]:
            return True
        
        # Methods and properties should group with their class if present
        if element.element_type in ["method", "property"]:
            # Check if current group has a class
            has_class = any(e.element_type in ["class", "interface", "struct"] for e in current_group)
            if has_class:
                return False
            
            # Estimate size
            current_size = sum(len(e.content) for e in current_group)
            element_size = len(element.content)
            return current_size + element_size > self.max_chunk_size * 0.8
        
        return False
    
    def _create_chunk_content(self, elements: List[CSharpElement], source_code: str) -> str:
        """
        Create content string from C# elements.
        
        Args:
            elements: List of C# elements
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
        elements: List[CSharpElement],
        chunk_index: str,
        total_chunks: int
    ) -> Document:
        """
        Create document from C# element group.
        
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
        symbol_names = [e.name for e in elements if e.name not in ["__usings__"]]
        
        # Create metadata
        file_path = original_document.metadata.get("file_path", "")
        file_type = original_document.metadata.get("file_type", ".cs")
        source = original_document.metadata.get("source", "unknown")
        
        chunk_metadata = ChunkMetadata(
            source=source,
            file_path=file_path,
            file_type=file_type,
            chunk_type=primary_element.element_type if primary_element else "content",
            symbol_name=primary_element.name if primary_element else None,
            line_start=min(e.start_line for e in elements) if elements else None,
            line_end=max(e.end_line for e in elements) if elements else None,
            language="csharp",
            contains_documentation=self._contains_xml_docs(content),
            symbols=symbol_names,
            element_count=len(elements),
            access_modifier=primary_element.access_modifier if primary_element else None
        )
        
        return self._create_chunk_document(
            content=content,
            original_metadata=original_document.metadata,
            chunk_metadata=chunk_metadata,
            chunk_index=int(chunk_index.split('.')[0]) if '.' in str(chunk_index) else int(chunk_index),
            total_chunks=total_chunks
        )
    
    def _split_csharp_chunk(self, content: str, elements: List[CSharpElement]) -> List[str]:
        """
        Split oversized C# chunk while preserving element boundaries.
        
        Args:
            content: Content to split
            elements: Elements in the content
            
        Returns:
            List of split content chunks
        """
        if len(elements) > 1:
            chunks = []
            current_chunk = ""
            
            for element in sorted(elements, key=lambda x: x.start_line):
                element_content = element.content
                
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
                source="", file_path="", file_type=".cs", language="csharp"
            )
            return super()._split_oversized_chunk(content, dummy_metadata)
    
    def _contains_xml_docs(self, content: str) -> bool:
        """
        Check if content contains XML documentation comments.
        
        Args:
            content: Content to check
            
        Returns:
            True if content contains XML docs
        """
        xml_doc_patterns = [
            '///',  # XML documentation comments
            '<summary>',  # Summary tags
            '<param',  # Parameter tags
            '<returns>',  # Returns tags
            '<exception>',  # Exception tags
        ]
        
        content_lower = content.lower()
        return any(pattern.lower() in content_lower for pattern in xml_doc_patterns)
    
    def _fallback_chunk(self, document: Document, content: str) -> List[Document]:
        """
        Fallback to simple text chunking when C# parsing fails.
        
        Args:
            document: Original document
            content: Content to chunk
            
        Returns:
            List of simply chunked documents
        """
        try:
            # Try to create meaningful chunks based on C# structure even in fallback mode
            chunks = []
            lines = content.split('\n')
            current_chunk = []
            current_size = 0
            
            for line in lines:
                line_size = len(line) + 1  # +1 for newline
                
                # Start new chunk for certain C# patterns
                should_start_new_chunk = (
                    # Class/interface/struct declarations
                    re.match(r'^\s*(public|private|protected|internal)?\s*(abstract|sealed|static)?\s*(class|interface|struct|enum)\s+', line) or
                    # Namespace declarations
                    re.match(r'^\s*namespace\s+', line) or
                    # Method declarations
                    re.match(r'^\s*(public|private|protected|internal)?\s*(static|virtual|override|abstract)?\s*\w+\s+\w+\s*\(', line) or
                    # Property declarations
                    re.match(r'^\s*(public|private|protected|internal)?\s*\w+\s+\w+\s*{\s*(get|set)', line) or
                    # Using statements
                    re.match(r'^\s*using\s+', line) or
                    # Current chunk is getting too large
                    current_size + line_size > self.max_chunk_size
                )
                
                if should_start_new_chunk and current_chunk:
                    # Save current chunk
                    chunk_content = '\n'.join(current_chunk)
                    if chunk_content.strip():
                        chunk_doc = self._create_fallback_chunk_document(
                            chunk_content, document, len(chunks)
                        )
                        chunks.append(chunk_doc)
                    
                    # Start new chunk
                    current_chunk = [line]
                    current_size = line_size
                else:
                    current_chunk.append(line)
                    current_size += line_size
            
            # Add the last chunk
            if current_chunk:
                chunk_content = '\n'.join(current_chunk)
                if chunk_content.strip():
                    chunk_doc = self._create_fallback_chunk_document(
                        chunk_content, document, len(chunks)
                    )
                    chunks.append(chunk_doc)
            
            if chunks:
                logger.info(f"Created {len(chunks)} fallback chunks for C# document")
                return chunks
            
        except Exception as e:
            logger.warning(f"Error in C# fallback chunking: {e}")
        
        # Ultimate fallback - use the generic fallback chunker
        from .fallback_chunker import FallbackChunker
        
        fallback_chunker = FallbackChunker(self.max_chunk_size, self.chunk_overlap)
        temp_doc = Document(page_content=content, metadata=document.metadata)
        return fallback_chunker.chunk_document(temp_doc)
    
    def _create_fallback_chunk_document(self, content: str, original_doc: Document, chunk_index: int) -> Document:
        """
        Create a fallback chunk document with basic C# metadata.
        
        Args:
            content: Chunk content
            original_doc: Original document
            chunk_index: Index of this chunk
            
        Returns:
            Document with basic metadata
        """
        # Try to extract basic C# information from the chunk
        chunk_type = "content"
        symbol_name = None
        
        # Look for class/interface/struct declarations
        class_match = re.search(r'(?:class|interface|struct|enum)\s+(\w+)', content)
        if class_match:
            chunk_type = "type_declaration"
            symbol_name = class_match.group(1)
        
        # Look for method declarations
        method_match = re.search(r'(\w+)\s*\([^)]*\)\s*{?', content)
        if method_match and not symbol_name:
            chunk_type = "method"
            symbol_name = method_match.group(1)
        
        # Look for namespace declarations
        namespace_match = re.search(r'namespace\s+([^\s{]+)', content)
        if namespace_match and not symbol_name:
            chunk_type = "namespace"
            symbol_name = namespace_match.group(1)
        
        chunk_metadata = ChunkMetadata(
            source=original_doc.metadata.get('source', 'unknown'),
            file_path=original_doc.metadata.get('file_path', 'unknown'),
            file_type=".cs",
            chunk_type=chunk_type,
            symbol_name=symbol_name,
            language="csharp",
            contains_documentation=self._contains_xml_docs(content),
            parsing_method="fallback"
        )
        
        return self._create_chunk_document(
            content=content,
            original_metadata=original_doc.metadata,
            chunk_metadata=chunk_metadata,
            chunk_index=chunk_index,
            total_chunks=1  # We don't know the total in fallback mode
        )
