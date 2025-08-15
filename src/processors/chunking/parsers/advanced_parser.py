"""
Base advanced parser class using tree-sitter for semantic code analysis.

This module provides the foundation for tree-sitter based parsing with
error handling, fallback mechanisms, and common utilities for all
language-specific parsers.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Callable
import tree_sitter as ts
from pathlib import Path

from .semantic_element import (
    SemanticElement, 
    ElementType, 
    SemanticPosition, 
    ParseResult,
    AccessModifier
)
from ....utils.logging import get_logger

logger = get_logger(__name__)


class ParsingError(Exception):
    """Base exception for parsing errors."""
    pass


class AdvancedParserError(ParsingError):
    """Exception for advanced parser specific errors."""
    pass


class FallbackError(ParsingError):
    """Exception when fallback parsing is required."""
    pass


class AdvancedParser(ABC):
    """
    Base class for tree-sitter based advanced parsers.
    
    Provides common functionality for parsing source code using tree-sitter,
    including error handling, caching, and fallback mechanisms.
    """
    
    def __init__(self, language_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the advanced parser.
        
        Args:
            language_name: Name of the programming language (e.g., 'csharp', 'javascript')
            config: Configuration dictionary for parser-specific settings
        """
        self.language_name = language_name
        self.config = config or {}
        self._parser: Optional[ts.Parser] = None
        self._language: Optional[ts.Language] = None
        
        # Configuration options
        self.max_file_size = self.config.get('max_file_size_mb', 10) * 1024 * 1024
        self.enable_error_recovery = self.config.get('enable_error_recovery', True)
        self.extract_documentation = self.config.get('extract_documentation', True)
        self.include_comments = self.config.get('include_comments', False)
        
        # Performance tracking
        self._parse_count = 0
        self._total_parse_time = 0.0
        
        # Initialize the tree-sitter parser
        self._initialize_parser()
    
    def _initialize_parser(self) -> None:
        """Initialize the tree-sitter parser and language."""
        try:
            self._language = self._get_tree_sitter_language()
            self._parser = ts.Parser(self._language)
            logger.debug(f"Initialized tree-sitter parser for {self.language_name}")
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter parser for {self.language_name}: {e}")
            raise AdvancedParserError(f"Parser initialization failed: {e}")
    
    @abstractmethod
    def _get_tree_sitter_language(self) -> ts.Language:
        """
        Get the tree-sitter language object for this parser.
        
        Returns:
            Tree-sitter Language object
        """
        pass
    
    @abstractmethod
    def _extract_semantic_elements(self, tree: ts.Tree, source_code: str) -> List[SemanticElement]:
        """
        Extract semantic elements from the parsed tree.
        
        Args:
            tree: The parsed tree-sitter tree
            source_code: Original source code
            
        Returns:
            List of extracted semantic elements
        """
        pass
    
    def parse(self, source_code: str, file_path: Optional[str] = None) -> ParseResult:
        """
        Parse source code and extract semantic elements.
        
        Args:
            source_code: The source code to parse
            file_path: Optional file path for context and error reporting
            
        Returns:
            ParseResult containing extracted elements and metadata
        """
        start_time = time.time()
        result = ParseResult(
            elements=[],
            parser_type=self.language_name,
            source_length=len(source_code),
            source_lines=source_code.count('\n') + 1
        )
        
        try:
            # Validate input
            if not source_code.strip():
                result.add_warning("Empty source code provided")
                return result
            
            if len(source_code.encode('utf-8')) > self.max_file_size:
                raise FallbackError(f"File too large: {len(source_code)} bytes > {self.max_file_size}")
            
            # Parse with tree-sitter
            tree = self._parse_with_tree_sitter(source_code)
            result.tree_objects = tree
            
            # Check for parse errors
            if tree.root_node.has_error:
                error_msg = "Tree-sitter found syntax errors in source code"
                if self.enable_error_recovery:
                    result.add_warning(f"{error_msg}, attempting partial parsing")
                    # Continue with partial parsing
                else:
                    raise FallbackError(error_msg)
            
            # Extract semantic elements
            result.elements = self._extract_semantic_elements(tree, source_code)
            
            # Validate extracted elements
            self._validate_elements(result.elements, source_code)
            
        except FallbackError as e:
            result.add_error(f"Fallback required: {e}")
            logger.warning(f"Parser fallback required for {file_path or 'unknown'}: {e}")
        except Exception as e:
            result.add_error(f"Parsing failed: {e}")
            logger.error(f"Parsing error in {file_path or 'unknown'}: {e}")
        
        # Record timing
        result.parse_time_ms = (time.time() - start_time) * 1000
        self._parse_count += 1
        self._total_parse_time += result.parse_time_ms
        
        logger.debug(f"Parsed {self.language_name} file in {result.parse_time_ms:.2f}ms "
                    f"with {len(result.elements)} elements")
        
        return result
    
    def _parse_with_tree_sitter(self, source_code: str) -> ts.Tree:
        """
        Parse source code with tree-sitter.
        
        Args:
            source_code: Source code to parse
            
        Returns:
            Parsed tree-sitter tree
        """
        if not self._parser:
            raise AdvancedParserError("Parser not initialized")
        
        try:
            # Convert to bytes for tree-sitter
            source_bytes = source_code.encode('utf-8')
            tree = self._parser.parse(source_bytes)
            return tree
        except Exception as e:
            raise AdvancedParserError(f"Tree-sitter parsing failed: {e}")
    
    def _validate_elements(self, elements: List[SemanticElement], source_code: str) -> None:
        """
        Validate extracted semantic elements.
        
        Args:
            elements: List of semantic elements to validate
            source_code: Original source code for position validation
        """
        source_lines = source_code.split('\n')
        source_length = len(source_code)
        
        for element in elements:
            # Validate position bounds
            if element.position.start_byte < 0 or element.position.end_byte > source_length:
                logger.warning(f"Element '{element.name}' has invalid byte position")
            
            if element.position.start_line < 1 or element.position.end_line > len(source_lines):
                logger.warning(f"Element '{element.name}' has invalid line position")
            
            # Validate content consistency
            if element.content:
                try:
                    extracted_content = source_code[element.position.start_byte:element.position.end_byte]
                    if element.content.strip() != extracted_content.strip():
                        logger.debug(f"Element '{element.name}' content may not match position")
                except IndexError:
                    logger.warning(f"Element '{element.name}' position out of bounds")
    
    def _create_position(self, node: ts.Node) -> SemanticPosition:
        """
        Create SemanticPosition from tree-sitter node.
        
        Args:
            node: Tree-sitter node
            
        Returns:
            SemanticPosition object
        """
        return SemanticPosition(
            start_line=node.start_point[0] + 1,  # Convert to 1-based
            end_line=node.end_point[0] + 1,
            start_column=node.start_point[1],
            end_column=node.end_point[1],
            start_byte=node.start_byte,
            end_byte=node.end_byte
        )
    
    def _get_node_text(self, node: ts.Node, source_code: str) -> str:
        """
        Extract text content from a tree-sitter node.
        
        Args:
            node: Tree-sitter node
            source_code: Original source code
            
        Returns:
            Text content of the node
        """
        try:
            return source_code[node.start_byte:node.end_byte]
        except IndexError:
            logger.warning(f"Node position out of bounds: {node.start_byte}-{node.end_byte}")
            return ""
    
    def _find_child_by_type(self, node: ts.Node, node_type: str) -> Optional[ts.Node]:
        """
        Find first child node of specific type.
        
        Args:
            node: Parent node to search
            node_type: Type of child node to find
            
        Returns:
            First matching child node or None
        """
        for child in node.children:
            if child.type == node_type:
                return child
        return None
    
    def _find_children_by_type(self, node: ts.Node, node_type: str) -> List[ts.Node]:
        """
        Find all child nodes of specific type.
        
        Args:
            node: Parent node to search  
            node_type: Type of child nodes to find
            
        Returns:
            List of matching child nodes
        """
        return [child for child in node.children if child.type == node_type]
    
    def _extract_documentation_comment(self, node: ts.Node, source_code: str) -> Optional[str]:
        """
        Extract documentation comment for a node.
        
        Args:
            node: Node to find documentation for
            source_code: Original source code
            
        Returns:
            Documentation string or None
        """
        if not self.extract_documentation:
            return None
        
        # This is a base implementation that can be overridden by language-specific parsers
        # Look for comment nodes immediately before this node
        parent = node.parent
        if not parent:
            return None
        
        node_index = parent.children.index(node)
        if node_index > 0:
            prev_node = parent.children[node_index - 1]
            if 'comment' in prev_node.type:
                comment_text = self._get_node_text(prev_node, source_code)
                return self._clean_comment_text(comment_text)
        
        return None
    
    def _clean_comment_text(self, comment: str) -> str:
        """
        Clean and normalize comment text.
        
        Args:
            comment: Raw comment text
            
        Returns:
            Cleaned comment text
        """
        if not comment:
            return ""
        
        # Remove common comment markers
        lines = comment.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Remove common prefixes
            for prefix in ['//', '///', '/*', '*/', '*', '#']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break
            if line:  # Only add non-empty lines
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get parser performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        avg_parse_time = self._total_parse_time / max(self._parse_count, 1)
        
        return {
            "language": self.language_name,
            "parse_count": self._parse_count,
            "total_parse_time_ms": self._total_parse_time,
            "average_parse_time_ms": avg_parse_time,
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
            "error_recovery_enabled": self.enable_error_recovery,
            "documentation_extraction_enabled": self.extract_documentation
        }
    
    def reset_statistics(self) -> None:
        """Reset parser statistics."""
        self._parse_count = 0
        self._total_parse_time = 0.0
    
    def __str__(self) -> str:
        """String representation of the parser."""
        return f"AdvancedParser({self.language_name})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the parser."""
        return (f"AdvancedParser(language='{self.language_name}', "
               f"parsed_files={self._parse_count}, "
               f"avg_time={self._total_parse_time / max(self._parse_count, 1):.2f}ms)")