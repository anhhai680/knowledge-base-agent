"""
Tree-sitter based parser for multi-language code analysis.
Integrated from the provided CodeParser.py with enhancements for the chunking system.
"""

import os
import subprocess
from typing import List, Dict, Union, Tuple, Optional
from tree_sitter import Language, Parser, Node
import tree_sitter_python as ts_python
import tree_sitter_javascript as ts_javascript
import tree_sitter_typescript as ts_typescript
import tree_sitter_c_sharp as ts_c_sharp
import tree_sitter_css as ts_css
import tree_sitter_php as ts_php


# Import the logger utility from the utils package  
from ....utils.logging import get_logger

logger = get_logger(__name__)

# Try to import language-specific bindings for tree-sitter 0.25.0+
_language_modules = {
    "python": ts_python,
    "javascript": ts_javascript,
    "typescript": ts_typescript,
    "c_sharp": ts_c_sharp,
    "css": ts_css,
    "php": ts_php
}
MODERN_TREE_SITTER = False

if _language_modules:
    MODERN_TREE_SITTER = True
    logger.info(f"Using modern tree-sitter language bindings for: {list(_language_modules.keys())}")
else:
    logger.warning("No modern tree-sitter bindings available, falling back to legacy mode")


class CodeParser:
    """
    Enhanced tree-sitter parser for multi-language code analysis.
    Based on the provided CodeParser.py with integration improvements.
    """
    
    # Cache directory for tree-sitter grammars
    CACHE_DIR = os.path.expanduser("~/.code_parser_cache")

    def __init__(self, file_extensions: Union[None, List[str], str] = None):
        """
        Initialize the tree-sitter parser for specified file extensions.
        
        Args:
            file_extensions: List of file extensions to support, or None for all
        """
        if isinstance(file_extensions, str):
            file_extensions = [file_extensions]
        
        # Mapping from file extensions to language names
        self.language_extension_map = {
            "py": "python",
            "js": "javascript", 
            "jsx": "javascript",
            "css": "css",
            "ts": "typescript",
            "tsx": "typescript",
            "php": "php",
            "cs": "c_sharp"
        }
        
        # Mapping from language names to repository names (for git cloning)
        self.repository_name_map = {
            "python": "python",
            "javascript": "javascript",
            "css": "css",
            "typescript": "typescript",
            "php": "php",
            "c_sharp": "c-sharp"
        }
        
        # Determine which languages to initialize
        if file_extensions is None:
            self.language_names = list(self.language_extension_map.values())
        else:
            language_names_with_none = [
                self.language_extension_map.get(ext) 
                for ext in file_extensions 
                if ext in self.language_extension_map
            ]
            # Remove None values and duplicates while preserving order
            self.language_names = list(dict.fromkeys(lang for lang in language_names_with_none if lang is not None))
        
        logger.info(f"Initializing CodeParser for languages: {self.language_names}")
        self.languages = {}
        self.parsers = {}
        self._install_parsers()

    def _install_parsers(self):
        """Install parsers using modern tree-sitter language bindings."""
        for language in self.language_names:
            try:
                if language in _language_modules:
                    # Get language from binding - different APIs for different bindings
                    language_binding = _language_modules[language]
                    
                    # Try different ways to get the language object
                    language_obj = None
                    
                    if language == 'typescript':
                        # TypeScript has special handling
                        if hasattr(language_binding, 'language_typescript'):
                            language_obj = language_binding.language_typescript()
                        elif hasattr(language_binding, 'language'):
                            language_obj = language_binding.language()
                    else:
                        # Standard case - most languages have language() function
                        if hasattr(language_binding, 'language') and callable(language_binding.language):
                            language_obj = language_binding.language()
                        elif hasattr(language_binding, 'language'):
                            language_obj = language_binding.language
                        elif hasattr(language_binding, 'LANGUAGE'):
                            # Some bindings have a LANGUAGE constant
                            language_obj = language_binding.LANGUAGE
                    
                    if language_obj is not None:
                        # Wrap PyCapsule with tree_sitter.Language if needed
                        if hasattr(language_obj, '__class__') and 'PyCapsule' in str(type(language_obj)):
                            language_obj = Language(language_obj)
                        
                        # Store the language object and create parser with modern API
                        self.languages[language] = language_obj
                        self.parsers[language] = Parser(language_obj)
                        logger.info(f"Successfully loaded {language} parser using modern bindings")
                    else:
                        logger.warning(f"Could not find language object in {language} binding")
                        
                else:
                    logger.warning(f"No modern binding available for {language}, skipping")
                    
            except Exception as e:
                logger.error(f"Failed to load modern parser for {language}: {str(e)}")
                continue

    def _is_repo_valid(self, repo_path: str, language: str) -> bool:
        """Check if the repository contains necessary files."""
        if language == 'typescript':
            return (os.path.exists(os.path.join(repo_path, 'typescript', 'src', 'parser.c')) and
                   os.path.exists(os.path.join(repo_path, 'tsx', 'src', 'parser.c')))
        elif language == 'php':
            return os.path.exists(os.path.join(repo_path, 'php', 'src', 'parser.c'))
        else:
            return os.path.exists(os.path.join(repo_path, 'src', 'parser.c'))

    def parse_code(self, code: str, file_extension: str) -> Optional[Node]:
        """
        Parse code and return the root node of the syntax tree.
        
        Args:
            code: Source code to parse
            file_extension: File extension (e.g., 'py', 'js')
            
        Returns:
            Root node of the syntax tree, or None if parsing failed
        """
        language_name = self.language_extension_map.get(file_extension)
        if language_name is None:
            logger.warning(f"Unsupported file type: {file_extension}")
            return None

        parser = self.parsers.get(language_name)
        if parser is None:
            logger.warning(f"Language parser for {language_name} not found. Cannot parse code.")
            return None

        try:
            tree = parser.parse(bytes(code, "utf8"))
            if tree is None:
                logger.warning("Failed to parse the code")
                return None
            return tree.root_node
        except Exception as e:
            logger.error(f"Error parsing code: {str(e)}")
            return None

    def extract_points_of_interest(self, node: Node, file_extension: str) -> List[Tuple[Node, str]]:
        """
        Extract semantically important nodes from the syntax tree.
        
        Args:
            node: Root node to search from
            file_extension: File extension to determine node types
            
        Returns:
            List of (node, description) tuples for important code elements
        """
        node_types_of_interest = self._get_node_types_of_interest(file_extension)

        points_of_interest = []
        if node.type in node_types_of_interest.keys():
            points_of_interest.append((node, node_types_of_interest[node.type]))

        for child in node.children:
            points_of_interest.extend(self.extract_points_of_interest(child, file_extension))

        return points_of_interest

    def _get_node_types_of_interest(self, file_extension: str) -> Dict[str, str]:
        """Get node types that represent important code constructs."""
        node_types = {
            'py': {
                'import_statement': 'Import',
                'import_from_statement': 'Import',
                'class_definition': 'Class',
                'function_definition': 'Function',
                'decorated_definition': 'Decorated Function/Class',
            },
            'css': {
                'rule_set': 'CSS Rule',
                'at_rule': 'At-rule',
                'media_statement': 'Media Query',
            },
            'js': {
                'import_statement': 'Import',
                'export_statement': 'Export',
                'class_declaration': 'Class',
                'function_declaration': 'Function',
                'arrow_function': 'Arrow Function',
                'method_definition': 'Method',
                'variable_declaration': 'Variable Declaration',
            },
            'ts': {
                'import_statement': 'Import',
                'export_statement': 'Export',
                'class_declaration': 'Class',
                'function_declaration': 'Function',
                'arrow_function': 'Arrow Function',
                'method_definition': 'Method',
                'interface_declaration': 'Interface',
                'type_alias_declaration': 'Type Alias',
                'enum_declaration': 'Enum',
            },
            'php': {
                'namespace_definition': 'Namespace',
                'class_declaration': 'Class',
                'method_declaration': 'Method',
                'function_definition': 'Function',
                'interface_declaration': 'Interface',
                'trait_declaration': 'Trait',
            },
            'cs': {
                'using_directive': 'Using',
                'namespace_declaration': 'Namespace',
                'class_declaration': 'Class',
                'method_declaration': 'Method',
                'interface_declaration': 'Interface',
                'enum_declaration': 'Enum',
                'record_declaration': 'Record',
            }
        }

        if file_extension in node_types.keys():
            return node_types[file_extension]
        elif file_extension == "jsx":
            return node_types["js"]
        elif file_extension == "tsx":
            return node_types["ts"]
        else:
            logger.warning(f"No node types defined for file extension: {file_extension}")
            return {}

    def get_semantic_boundaries(self, code: str, file_extension: str) -> List[int]:
        """
        Get line numbers that represent good chunking boundaries.
        
        Args:
            code: Source code to analyze
            file_extension: File extension (e.g., 'py', 'js')
            
        Returns:
            List of line numbers (0-indexed) that are good chunk boundaries
        """
        root_node = self.parse_code(code, file_extension)
        if root_node is None:
            return []

        points_of_interest = self.extract_points_of_interest(root_node, file_extension)
        boundaries = []

        for node, _ in points_of_interest:
            # Add the start line of each semantic element
            start_line = node.start_point[0]
            boundaries.append(start_line)

        # Also include comment boundaries
        comment_boundaries = self._get_comment_boundaries(root_node, file_extension)
        boundaries.extend(comment_boundaries)

        # Sort and remove duplicates
        return sorted(set(boundaries))

    def _get_comment_boundaries(self, node: Node, file_extension: str) -> List[int]:
        """Extract line numbers for comments and docstrings."""
        comment_types = self._get_comment_node_types(file_extension)
        boundaries = []

        def visit_node(node: Node):
            if node.type in comment_types:
                boundaries.append(node.start_point[0])
            for child in node.children:
                visit_node(child)

        visit_node(node)
        return boundaries

    def _get_comment_node_types(self, file_extension: str) -> List[str]:
        """Get node types that represent comments for different languages."""
        comment_types = {
            'py': ['comment', 'string'],  # string can be docstring
            'js': ['comment'],
            'ts': ['comment'],
            'css': ['comment'],
            'php': ['comment'],
            'cs': ['comment'],
        }
        
        return comment_types.get(file_extension, ['comment'])

    def get_loaded_languages(self) -> List[str]:
        """Get a list of successfully loaded language parsers."""
        return list(self.languages.keys())
    
    def get_language_status(self) -> Dict[str, bool]:
        """Get the status of all language parsers."""
        status = {}
        for ext, lang_name in self.language_extension_map.items():
            status[ext] = lang_name in self.languages
        return status
    
    def is_language_supported(self, file_extension: str) -> bool:
        """Check if a file extension is supported."""
        return file_extension in self.language_extension_map
    
    def is_language_loaded(self, file_extension: str) -> bool:
        """Check if a language parser is successfully loaded."""
        language_name = self.language_extension_map.get(file_extension)
        if language_name is None:
            return False
        return language_name in self.languages
    
    def get_language_error_message(self, file_extension: str) -> str:
        """Get a helpful error message for when a language is not available."""
        if not self.is_language_supported(file_extension):
            supported = list(self.language_extension_map.keys())
            return f"File extension '{file_extension}' is not supported. Supported extensions: {supported}"
        
        language_name = self.language_extension_map.get(file_extension)
        if not self.is_language_loaded(file_extension):
            return (f"Language parser for '{language_name}' (extension: {file_extension}) failed to load. "
                   f"This may be due to compilation issues or missing dependencies.")
        
        return f"Language parser for '{language_name}' (extension: {file_extension}) is available and working."

    def get_symbol_information(self, code: str, file_extension: str) -> List[Dict]:
        """
        Extract detailed symbol information for enhanced chunking metadata.
        
        Args:
            code: Source code to analyze
            file_extension: File extension
            
        Returns:
            List of symbol dictionaries with name, type, line numbers, etc.
        """
        root_node = self.parse_code(code, file_extension)
        if root_node is None:
            return []
        
        symbols = []
        points_of_interest = self.extract_points_of_interest(root_node, file_extension)
        
        for node, symbol_type in points_of_interest:
            symbol_info = {
                'name': self._extract_symbol_name(node, file_extension),
                'type': symbol_type,
                'line_start': node.start_point[0],
                'line_end': node.end_point[0],
                'byte_start': node.start_byte,
                'byte_end': node.end_byte,
            }
            symbols.append(symbol_info)
        
        return symbols

    def _extract_symbol_name(self, node: Node, file_extension: str) -> Optional[str]:
        """Extract the name of a symbol from its AST node."""
        try:
            # Common patterns for extracting names from different node types
            if node.type in ['function_definition', 'class_definition', 'method_declaration']:
                # Look for identifier child nodes
                for child in node.children:
                    if child.type == 'identifier':
                        return child.text.decode('utf-8')
            
            # For other types, try to find the first identifier
            for child in node.children:
                if child.type == 'identifier':
                    return child.text.decode('utf-8')
            
            return None
        except Exception as e:
            logger.warning(f"Failed to extract symbol name: {e}")
            return None