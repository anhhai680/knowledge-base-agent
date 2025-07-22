"""
AST-based parser for extracting semantic chunks from source code.
"""

import ast
import re
from typing import List, Dict, Any, Optional, Tuple, NamedTuple
import sys
import os.path

# Add the parent directory to the path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from utils.logging import get_logger

logger = get_logger(__name__)


class CodeElement(NamedTuple):
    """Represents a semantic code element."""
    
    name: str
    element_type: str  # 'class', 'function', 'method', 'import', 'module'
    start_line: int
    end_line: int
    content: str
    parent: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = []


class ASTParser:
    """AST-based parser for extracting semantic information from Python code."""
    
    def __init__(self):
        """Initialize the AST parser."""
        self.elements: List[CodeElement] = []
        self.source_lines: List[str] = []
    
    def parse_python_code(self, code: str) -> List[CodeElement]:
        """
        Parse Python code and extract semantic elements.
        
        Args:
            code: Python source code to parse
            
        Returns:
            List of CodeElement objects representing semantic chunks
        """
        self.elements = []
        self.source_lines = code.split('\n')
        
        try:
            tree = ast.parse(code)
            self._visit_node(tree)
            
            # Sort elements by line number
            self.elements.sort(key=lambda x: x.start_line)
            
            return self.elements
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in Python code: {str(e)}")
            return self._fallback_parse(code)
        except Exception as e:
            logger.warning(f"Error parsing Python code: {str(e)}")
            return self._fallback_parse(code)
    
    def _visit_node(self, node: ast.AST, parent_name: Optional[str] = None) -> None:
        """
        Visit AST nodes and extract semantic elements.
        
        Args:
            node: AST node to visit
            parent_name: Name of parent element (for methods in classes)
        """
        if isinstance(node, ast.Module):
            # Handle module-level docstring
            if (node.body and 
                isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)):
                
                docstring = node.body[0].value.value
                self.elements.append(CodeElement(
                    name="__module__",
                    element_type="module",
                    start_line=1,
                    end_line=node.body[0].end_lineno or 1,
                    content=self._get_content(1, node.body[0].end_lineno or 1),
                    docstring=docstring
                ))
            
            # Handle imports at module level
            imports = []
            for child in node.body:
                if isinstance(child, (ast.Import, ast.ImportFrom)):
                    imports.append(child)
            
            if imports:
                start_line = imports[0].lineno
                end_line = imports[-1].end_lineno or imports[-1].lineno
                self.elements.append(CodeElement(
                    name="__imports__",
                    element_type="import",
                    start_line=start_line,
                    end_line=end_line,
                    content=self._get_content(start_line, end_line)
                ))
            
            # Visit other module-level elements
            for child in node.body:
                if not isinstance(child, (ast.Import, ast.ImportFrom)):
                    self._visit_node(child, parent_name)
        
        elif isinstance(node, ast.ClassDef):
            self._handle_class(node, parent_name)
        
        elif isinstance(node, ast.FunctionDef):
            self._handle_function(node, parent_name)
        
        elif isinstance(node, ast.AsyncFunctionDef):
            self._handle_function(node, parent_name, is_async=True)
        
        else:
            # Visit child nodes
            for child in ast.iter_child_nodes(node):
                self._visit_node(child, parent_name)
    
    def _handle_class(self, node: ast.ClassDef, parent_name: Optional[str] = None) -> None:
        """Handle class definition."""
        docstring = self._extract_docstring(node)
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        class_element = CodeElement(
            name=node.name,
            element_type="class",
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            content=self._get_content(node.lineno, node.end_lineno or node.lineno),
            parent=parent_name,
            docstring=docstring,
            decorators=decorators
        )
        
        self.elements.append(class_element)
        
        # Visit methods within the class
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._visit_node(child, node.name)
    
    def _handle_function(
        self, 
        node: ast.AST,  # Changed to AST to handle both FunctionDef and AsyncFunctionDef 
        parent_name: Optional[str] = None, 
        is_async: bool = False
    ) -> None:
        """Handle function/method definition."""
        # Type check to ensure we have the right node type
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return
            
        docstring = self._extract_docstring(node)
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        element_type = "method" if parent_name else "function"
        if is_async:
            element_type = f"async_{element_type}"
        
        function_element = CodeElement(
            name=node.name,
            element_type=element_type,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            content=self._get_content(node.lineno, node.end_lineno or node.lineno),
            parent=parent_name,
            docstring=docstring,
            decorators=decorators
        )
        
        self.elements.append(function_element)
    
    def _extract_docstring(self, node: ast.AST) -> Optional[str]:
        """Extract docstring from a node."""
        # Check if node has body attribute and contains statements
        if hasattr(node, 'body'):
            body = getattr(node, 'body', [])
            if (body and 
                isinstance(body[0], ast.Expr) and 
                isinstance(body[0].value, ast.Constant) and
                isinstance(body[0].value.value, str)):
                
                return body[0].value.value
        
        return None
    
    def _get_decorator_name(self, decorator: ast.AST) -> str:
        """Get decorator name as string."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_decorator_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        else:
            return "unknown"
    
    def _get_content(self, start_line: int, end_line: int) -> str:
        """Get content between line numbers (1-indexed)."""
        if not self.source_lines:
            return ""
        
        # Convert to 0-indexed
        start_idx = max(0, start_line - 1)
        end_idx = min(len(self.source_lines), end_line)
        
        return '\n'.join(self.source_lines[start_idx:end_idx])
    
    def _fallback_parse(self, code: str) -> List[CodeElement]:
        """
        Fallback parsing using regex for malformed Python code.
        
        Args:
            code: Source code to parse
            
        Returns:
            List of CodeElement objects found via regex
        """
        elements = []
        lines = code.split('\n')
        
        # Pattern for class definitions
        class_pattern = r'^class\s+(\w+).*?:'
        
        # Pattern for function definitions
        func_pattern = r'^(\s*)def\s+(\w+)\s*\(.*?\):'
        
        # Pattern for async function definitions
        async_func_pattern = r'^(\s*)async\s+def\s+(\w+)\s*\(.*?\):'
        
        for i, line in enumerate(lines, 1):
            # Check for class
            class_match = re.match(class_pattern, line.strip())
            if class_match:
                elements.append(CodeElement(
                    name=class_match.group(1),
                    element_type="class",
                    start_line=i,
                    end_line=i,  # Will be updated when we find the end
                    content=line
                ))
            
            # Check for function
            func_match = re.match(func_pattern, line)
            if func_match:
                indent = func_match.group(1)
                func_name = func_match.group(2)
                element_type = "method" if indent else "function"
                
                elements.append(CodeElement(
                    name=func_name,
                    element_type=element_type,
                    start_line=i,
                    end_line=i,  # Will be updated when we find the end
                    content=line
                ))
            
            # Check for async function
            async_match = re.match(async_func_pattern, line)
            if async_match:
                indent = async_match.group(1)
                func_name = async_match.group(2)
                element_type = "async_method" if indent else "async_function"
                
                elements.append(CodeElement(
                    name=func_name,
                    element_type=element_type,
                    start_line=i,
                    end_line=i,  # Will be updated when we find the end
                    content=line
                ))
        
        return elements
    
    def get_element_hierarchy(self) -> Dict[str, List[CodeElement]]:
        """
        Get elements organized by hierarchy.
        
        Returns:
            Dictionary with module-level and class-level elements
        """
        hierarchy = {
            'module': [],
            'classes': {},
            'functions': []
        }
        
        for element in self.elements:
            if element.element_type in ['module', 'import']:
                hierarchy['module'].append(element)
            elif element.element_type == 'class':
                hierarchy['classes'][element.name] = []
            elif element.element_type in ['function', 'async_function']:
                hierarchy['functions'].append(element)
            elif element.element_type in ['method', 'async_method'] and element.parent:
                if element.parent not in hierarchy['classes']:
                    hierarchy['classes'][element.parent] = []
                hierarchy['classes'][element.parent].append(element)
        
        return hierarchy
