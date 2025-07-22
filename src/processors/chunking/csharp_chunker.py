"""
C#-specific chunker that preserves semantic boundaries.

This chunker uses regex-based parsing to identify C# language constructs
and creates chunks that respect namespace, class, and method boundaries.
"""

import re
from typing import List, Dict, Any, Optional, NamedTuple
from langchain.docstore.document import Document

from .base_chunker import BaseChunker, ChunkMetadata
import sys
import os.path

# Add the parent directory to the path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from utils.logging import get_logger

logger = get_logger(__name__)


class CSharpElement(NamedTuple):
    """Represents a C# code element."""
    
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
    
    Uses regex parsing to identify:
    - Using statements (grouped together)
    - Namespace declarations
    - Class definitions with their members
    - Methods and properties
    - Interface definitions
    """
    
    def __init__(self, max_chunk_size: int = 2000, chunk_overlap: int = 50):
        """
        Initialize C# chunker.
        
        Args:
            max_chunk_size: Maximum size for chunks in characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        super().__init__(max_chunk_size, chunk_overlap)
        
        # C# language patterns
        self.using_pattern = re.compile(r'^\s*using\s+[^;]+;', re.MULTILINE)
        self.namespace_pattern = re.compile(r'^\s*namespace\s+([^\s{]+)', re.MULTILINE)
        self.class_pattern = re.compile(r'^\s*(public|private|protected|internal)?\s*(abstract|sealed|static)?\s*(class|interface|struct|enum)\s+(\w+)', re.MULTILINE)
        self.method_pattern = re.compile(r'^\s*(public|private|protected|internal)?\s*(static|virtual|override|abstract)?\s*(\w+(?:\[\])?)\s+(\w+)\s*\([^{]*\)\s*{?', re.MULTILINE)
        self.property_pattern = re.compile(r'^\s*(public|private|protected|internal)?\s*(static)?\s*(\w+(?:\[\])?)\s+(\w+)\s*{\s*(get|set)', re.MULTILINE)
    
    def get_supported_extensions(self) -> List[str]:
        """
        Return list of C# file extensions.
        
        Returns:
            List of C# file extensions
        """
        return ['.cs']
    
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
            
            # Parse C# elements
            elements = self._parse_csharp_code(cleaned_content)
            
            if not elements:
                logger.warning("No C# semantic elements found, using fallback chunking")
                return self._fallback_chunk(document, cleaned_content)
            
            # Group elements into logical chunks
            chunk_groups = self._group_csharp_elements(elements)
            
            # Create documents from chunk groups
            chunked_documents = []
            for i, chunk_group in enumerate(chunk_groups):
                chunk_content = self._create_chunk_content(chunk_group, cleaned_content)
                
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
            
            logger.debug(f"Created {len(chunked_documents)} chunks from C# document")
            return chunked_documents
            
        except Exception as e:
            logger.error(f"Error in C# chunking: {str(e)}")
            # Ensure cleaned_content is available for fallback
            if 'cleaned_content' not in locals():
                cleaned_content = self._clean_content(document.page_content)
            return self._fallback_chunk(document, cleaned_content)
    
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
        
        # Find using statements
        using_lines = []
        for i, line in enumerate(lines, 1):
            if self.using_pattern.match(line):
                using_lines.append(i)
        
        if using_lines:
            elements.append(CSharpElement(
                name="__usings__",
                element_type="using",
                start_line=using_lines[0],
                end_line=using_lines[-1],
                content='\n'.join(lines[using_lines[0]-1:using_lines[-1]])
            ))
        
        # Find namespaces
        for match in self.namespace_pattern.finditer(code):
            namespace_name = match.group(1)
            start_line = code[:match.start()].count('\n') + 1
            
            # Find the end of namespace (simplified - assumes single namespace per file)
            elements.append(CSharpElement(
                name=namespace_name,
                element_type="namespace",
                start_line=start_line,
                end_line=start_line,  # Will be updated when we process content
                content=lines[start_line-1] if start_line <= len(lines) else ""
            ))
        
        # Find classes, interfaces, structs, enums
        for match in self.class_pattern.finditer(code):
            access_modifier = match.group(1) or "internal"
            class_type = match.group(3)
            class_name = match.group(4)
            start_line = code[:match.start()].count('\n') + 1
            
            # Find class body using regex for balanced braces
            class_body_pattern = re.compile(r'\{(?:[^{}]*|(?R))*\}')
            class_body_match = class_body_pattern.search(code, match.end())
            
            if class_body_match:
                class_end = class_body_match.end()
                class_content = code[match.start():class_end]
                end_line = code[:class_end].count('\n') + 1
            else:
                logger.warning(f"Could not find class body for {class_name}")
                class_end = match.end()
                class_content = code[match.start():class_end]
                end_line = code[:class_end].count('\n') + 1
            
            elements.append(CSharpElement(
                name=class_name,
                element_type=class_type,
                start_line=start_line,
                end_line=end_line,
                content=class_content,
                access_modifier=access_modifier
            ))
        
        # Find methods within classes (simplified)
        for match in self.method_pattern.finditer(code):
            access_modifier = match.group(1) or "private"
            return_type = match.group(3)
            method_name = match.group(4)
            start_line = code[:match.start()].count('\n') + 1
            
            # Simplified method end detection
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
        
        return sorted(elements, key=lambda x: x.start_line)
    
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
        from .fallback_chunker import FallbackChunker
        
        fallback_chunker = FallbackChunker(self.max_chunk_size, self.chunk_overlap)
        temp_doc = Document(page_content=content, metadata=document.metadata)
        return fallback_chunker.chunk_document(temp_doc)
