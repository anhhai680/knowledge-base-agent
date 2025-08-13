"""
JavaScript tree-sitter parser for advanced semantic analysis.

This module provides comprehensive JavaScript parsing using tree-sitter,
supporting modern ES6+ features including classes, modules, arrow functions,
async/await, destructuring, and JSX.
"""

from typing import Dict, List, Optional, Set
import tree_sitter as ts
import tree_sitter_javascript as ts_javascript

from .advanced_parser import AdvancedParser
from .semantic_element import (
    SemanticElement, 
    ElementType, 
    SemanticPosition,
    AccessModifier,
    ParseResult
)
from ....utils.logging import get_logger

logger = get_logger(__name__)


class JavaScriptAdvancedParser(AdvancedParser):
    """
    Advanced JavaScript parser using tree-sitter for precise semantic analysis.
    
    Supports comprehensive JavaScript language features:
    - ES6+ modules (import/export)
    - Classes and methods
    - Functions and arrow functions
    - Variables (let, const, var)
    - Async/await patterns
    - Destructuring assignments
    - Template literals
    - JSX syntax (when enabled)
    - Object and array destructuring
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize JavaScript tree-sitter parser."""
        super().__init__("javascript", config)
        
        # JavaScript specific configuration
        self.extract_exports = self.config.get('extract_exports', True)
        self.preserve_imports = self.config.get('preserve_imports', True)
        self.chunk_by_function = self.config.get('chunk_by_function', True)
        self.handle_jsx = self.config.get('handle_jsx', True)
        self.extract_comments = self.config.get('extract_comments', True)
        
        # Track module context
        self._current_module = ""
        self._is_module = False
    
    def _get_tree_sitter_language(self) -> ts.Language:
        """Get JavaScript tree-sitter language."""
        return ts.Language(ts_javascript.language())
    
    def _extract_semantic_elements(self, tree: ts.Tree, source_code: str) -> List[SemanticElement]:
        """Extract semantic elements from JavaScript syntax tree."""
        elements = []
        self._current_module = ""
        self._is_module = False
        
        # Process the root program
        root = tree.root_node
        elements.extend(self._process_program(root, source_code))
        
        return elements
    
    def _process_program(self, node: ts.Node, source_code: str) -> List[SemanticElement]:
        """Process the top-level program node."""
        elements = []
        
        for child in node.children:
            if child.type == "import_statement":
                if self.preserve_imports:
                    elements.append(self._extract_import_statement(child, source_code))
                    self._is_module = True
            elif child.type == "export_statement":
                if self.extract_exports:
                    elements.append(self._extract_export_statement(child, source_code))
                    self._is_module = True
            elif child.type == "class_declaration":
                elements.append(self._extract_class_declaration(child, source_code))
            elif child.type == "function_declaration":
                elements.append(self._extract_function_declaration(child, source_code))
            elif child.type == "variable_declaration":
                elements.extend(self._extract_variable_declaration(child, source_code))
            elif child.type == "expression_statement":
                # Check for function expressions, class expressions, etc.
                expr_element = self._extract_expression_statement(child, source_code)
                if expr_element:
                    elements.append(expr_element)
            elif child.type == "comment" and self.extract_comments:
                elements.append(self._extract_comment(child, source_code))
        
        return elements
    
    def _extract_import_statement(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract import statement information."""
        content = self._get_node_text(node, source_code)
        
        # Extract import source
        source_node = self._find_child_by_type(node, "string")
        source_path = ""
        if source_node:
            source_text = self._get_node_text(source_node, source_code)
            source_path = source_text.strip('"\'')
        
        # Extract imported names
        imported_names = []
        import_clause = self._find_child_by_type(node, "import_clause")
        if import_clause:
            imported_names = self._extract_import_names(import_clause, source_code)
        
        return SemanticElement(
            name=source_path or "unknown",
            element_type=ElementType.IMPORT,
            position=self._create_position(node),
            content=content.strip(),
            tree_sitter_node_type=node.type,
            language_specific={
                "source_path": source_path,
                "imported_names": imported_names,
                "is_default_import": "default" in imported_names,
                "is_namespace_import": "*" in content,
                "import_type": self._get_import_type(content)
            }
        )
    
    def _extract_export_statement(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract export statement information."""
        content = self._get_node_text(node, source_code)
        
        # Check what's being exported
        exported_element = None
        export_name = "export"
        
        for child in node.children:
            if child.type == "function_declaration":
                exported_element = self._extract_function_declaration(child, source_code)
                export_name = f"export {exported_element.name}"
            elif child.type == "class_declaration":
                exported_element = self._extract_class_declaration(child, source_code)
                export_name = f"export {exported_element.name}"
            elif child.type == "variable_declaration":
                vars = self._extract_variable_declaration(child, source_code)
                if vars:
                    exported_element = vars[0]
                    export_name = f"export {exported_element.name}"
        
        export_element = SemanticElement(
            name=export_name,
            element_type=ElementType.EXPORT,
            position=self._create_position(node),
            content=content.strip(),
            tree_sitter_node_type=node.type,
            language_specific={
                "is_default_export": "default" in content,
                "is_named_export": "default" not in content,
                "export_type": self._get_export_type(content)
            }
        )
        
        # Add the exported element as a child
        if exported_element:
            export_element.add_child(exported_element)
        
        return export_element
    
    def _extract_class_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract class declaration."""
        # Get class name
        name_node = self._find_child_by_type(node, "identifier")
        class_name = self._get_node_text(name_node, source_code) if name_node else "anonymous"
        
        # Extract superclass
        superclass = None
        heritage_clause = self._find_child_by_type(node, "class_heritage")
        if heritage_clause:
            extends_clause = self._find_child_by_type(heritage_clause, "extends_clause")
            if extends_clause:
                superclass_node = self._find_child_by_type(extends_clause, "identifier")
                if superclass_node:
                    superclass = self._get_node_text(superclass_node, source_code)
        
        # Extract class documentation
        documentation = self._extract_jsdoc_comment(node, source_code)
        
        # Create class element
        class_element = SemanticElement(
            name=class_name,
            element_type=ElementType.CLASS,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            documentation=documentation,
            tree_sitter_node_type=node.type,
            language_specific={
                "superclass": superclass,
                "is_expression": False,  # This is a declaration
                "is_exported": self._is_in_export(node)
            }
        )
        
        # Process class body
        class_body = self._find_child_by_type(node, "class_body")
        if class_body:
            for child in class_body.children:
                if child.type == "method_definition":
                    method = self._extract_method_definition(child, source_code)
                    class_element.add_child(method)
                elif child.type == "field_definition":
                    field = self._extract_field_definition(child, source_code)
                    class_element.add_child(field)
        
        return class_element
    
    def _extract_function_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract function declaration."""
        # Get function name
        name_node = self._find_child_by_type(node, "identifier")
        function_name = self._get_node_text(name_node, source_code) if name_node else "anonymous"
        
        # Extract parameters
        parameters = self._extract_function_parameters(node, source_code)
        
        # Check if async
        is_async = "async" in self._get_node_text(node, source_code)
        modifiers = [AccessModifier.ASYNC] if is_async else []
        
        # Check if generator
        is_generator = "*" in self._get_node_text(node, source_code)
        
        # Extract JSDoc
        documentation = self._extract_jsdoc_comment(node, source_code)
        
        # Create signature
        signature = self._create_function_signature(function_name, parameters, is_async, is_generator)
        
        return SemanticElement(
            name=function_name,
            element_type=ElementType.FUNCTION,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            signature=signature,
            parameters=parameters,
            access_modifiers=modifiers,
            documentation=documentation,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_async": is_async,
                "is_generator": is_generator,
                "is_arrow_function": False,
                "is_exported": self._is_in_export(node)
            }
        )
    
    def _extract_variable_declaration(self, node: ts.Node, source_code: str) -> List[SemanticElement]:
        """Extract variable declarations (let, const, var)."""
        elements = []
        
        # Get declaration kind
        kind = "var"  # default
        for child in node.children:
            if child.type in ["let", "const", "var"]:
                kind = child.type
                break
        
        # Process variable declarators
        for child in node.children:
            if child.type == "variable_declarator":
                element = self._extract_variable_declarator(child, source_code, kind)
                if element:
                    elements.append(element)
        
        return elements
    
    def _extract_variable_declarator(self, node: ts.Node, source_code: str, kind: str) -> Optional[SemanticElement]:
        """Extract a single variable declarator."""
        # Get variable name
        name_node = self._find_child_by_type(node, "identifier")
        if not name_node:
            # Handle destructuring assignments
            pattern_node = node.children[0] if node.children else None
            if pattern_node and pattern_node.type in ["object_pattern", "array_pattern"]:
                return self._extract_destructuring_pattern(pattern_node, source_code, kind)
            return None
        
        var_name = self._get_node_text(name_node, source_code)
        
        # Check if it's a function expression
        value_node = None
        for child in node.children:
            if child.type in ["function_expression", "arrow_function", "class_expression"]:
                value_node = child
                break
        
        # Determine element type based on value
        element_type = ElementType.VARIABLE
        if value_node:
            if value_node.type in ["function_expression", "arrow_function"]:
                element_type = ElementType.FUNCTION
            elif value_node.type == "class_expression":
                element_type = ElementType.CLASS
        elif kind == "const":
            element_type = ElementType.CONSTANT
        
        # Create element
        element = SemanticElement(
            name=var_name,
            element_type=element_type,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            tree_sitter_node_type=node.type,
            language_specific={
                "declaration_kind": kind,
                "is_const": kind == "const",
                "is_let": kind == "let",
                "is_var": kind == "var",
                "is_exported": self._is_in_export(node),
                "value_type": value_node.type if value_node else None
            }
        )
        
        # If it's a function or class expression, extract its details
        if value_node and value_node.type in ["function_expression", "arrow_function"]:
            parameters = self._extract_function_parameters(value_node, source_code)
            element.parameters = parameters
            element.signature = self._create_function_signature(var_name, parameters, 
                                                              "async" in self._get_node_text(value_node, source_code),
                                                              "*" in self._get_node_text(value_node, source_code))
        
        return element
    
    def _extract_method_definition(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract class method definition."""
        # Get method name
        name_node = self._find_child_by_type(node, "property_identifier")
        if not name_node:
            name_node = self._find_child_by_type(node, "identifier")
        
        method_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Check method type
        is_static = "static" in self._get_node_text(node, source_code)
        is_async = "async" in self._get_node_text(node, source_code)
        is_generator = "*" in self._get_node_text(node, source_code)
        is_constructor = method_name == "constructor"
        is_getter = "get " in self._get_node_text(node, source_code)
        is_setter = "set " in self._get_node_text(node, source_code)
        
        # Set element type
        element_type = ElementType.CONSTRUCTOR if is_constructor else ElementType.METHOD
        if is_getter or is_setter:
            element_type = ElementType.PROPERTY
        
        # Extract modifiers
        modifiers = []
        if is_static:
            modifiers.append(AccessModifier.STATIC)
        if is_async:
            modifiers.append(AccessModifier.ASYNC)
        
        # Extract parameters
        parameters = self._extract_function_parameters(node, source_code)
        
        # Extract JSDoc
        documentation = self._extract_jsdoc_comment(node, source_code)
        
        # Create signature
        signature = self._create_function_signature(method_name, parameters, is_async, is_generator)
        
        return SemanticElement(
            name=method_name,
            element_type=element_type,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            signature=signature,
            parameters=parameters,
            access_modifiers=modifiers,
            documentation=documentation,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_static": is_static,
                "is_async": is_async,
                "is_generator": is_generator,
                "is_constructor": is_constructor,
                "is_getter": is_getter,
                "is_setter": is_setter,
                "method_kind": self._get_method_kind(node, source_code)
            }
        )
    
    def _extract_field_definition(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract class field definition."""
        # Get field name
        name_node = self._find_child_by_type(node, "property_identifier")
        field_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Check if static
        is_static = "static" in self._get_node_text(node, source_code)
        modifiers = [AccessModifier.STATIC] if is_static else []
        
        return SemanticElement(
            name=field_name,
            element_type=ElementType.FIELD,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            access_modifiers=modifiers,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_static": is_static,
                "has_initializer": self._has_field_initializer(node)
            }
        )
    
    def _extract_expression_statement(self, node: ts.Node, source_code: str) -> Optional[SemanticElement]:
        """Extract meaningful expression statements."""
        # Look for function expressions assigned to variables
        expression = node.children[0] if node.children else None
        if not expression:
            return None
        
        if expression.type == "assignment_expression":
            return self._extract_assignment_expression(expression, source_code)
        
        return None
    
    def _extract_assignment_expression(self, node: ts.Node, source_code: str) -> Optional[SemanticElement]:
        """Extract assignment expressions that create functions."""
        # Check if right side is a function
        right_node = None
        left_node = None
        
        for child in node.children:
            if child.type in ["function_expression", "arrow_function", "class_expression"]:
                right_node = child
            elif child.type in ["identifier", "member_expression"]:
                left_node = child
        
        if not (left_node and right_node):
            return None
        
        # Get the assigned name
        assigned_name = self._get_node_text(left_node, source_code)
        
        # Determine element type
        element_type = ElementType.FUNCTION
        if right_node.type == "class_expression":
            element_type = ElementType.CLASS
        
        # Extract function details if applicable
        parameters = []
        signature = assigned_name
        if right_node.type in ["function_expression", "arrow_function"]:
            parameters = self._extract_function_parameters(right_node, source_code)
            is_async = "async" in self._get_node_text(right_node, source_code)
            signature = self._create_function_signature(assigned_name, parameters, is_async, False)
        
        return SemanticElement(
            name=assigned_name,
            element_type=element_type,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            signature=signature,
            parameters=parameters,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_assignment": True,
                "assigned_type": right_node.type,
                "is_arrow_function": right_node.type == "arrow_function"
            }
        )
    
    def _extract_comment(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract comment."""
        content = self._get_node_text(node, source_code)
        
        return SemanticElement(
            name="comment",
            element_type=ElementType.COMMENT,
            position=self._create_position(node),
            content=content,
            tree_sitter_node_type=node.type,
            language_specific={
                "comment_type": "line" if content.startswith("//") else "block"
            }
        )
    
    def _extract_destructuring_pattern(self, node: ts.Node, source_code: str, kind: str) -> SemanticElement:
        """Extract destructuring pattern."""
        pattern_text = self._get_node_text(node, source_code)
        
        return SemanticElement(
            name=f"destructuring_{node.type}",
            element_type=ElementType.VARIABLE,
            position=self._create_position(node),
            content=pattern_text,
            tree_sitter_node_type=node.type,
            language_specific={
                "declaration_kind": kind,
                "is_destructuring": True,
                "pattern_type": node.type
            }
        )
    
    def _extract_function_parameters(self, node: ts.Node, source_code: str) -> List[Dict[str, str]]:
        """Extract function parameters."""
        parameters = []
        
        param_node = self._find_child_by_type(node, "formal_parameters")
        if param_node:
            for child in param_node.children:
                if child.type == "identifier":
                    param_name = self._get_node_text(child, source_code)
                    parameters.append({"name": param_name, "type": "", "default": ""})
                elif child.type == "assignment_pattern":
                    # Parameter with default value
                    param_info = self._extract_parameter_with_default(child, source_code)
                    if param_info:
                        parameters.append(param_info)
                elif child.type in ["object_pattern", "array_pattern"]:
                    # Destructured parameter
                    param_text = self._get_node_text(child, source_code)
                    parameters.append({"name": param_text, "type": "destructured", "default": ""})
        
        return parameters
    
    def _extract_parameter_with_default(self, node: ts.Node, source_code: str) -> Optional[Dict[str, str]]:
        """Extract parameter with default value."""
        param_name = ""
        default_value = ""
        
        for child in node.children:
            if child.type == "identifier":
                param_name = self._get_node_text(child, source_code)
            else:
                # This is likely the default value
                default_value = self._get_node_text(child, source_code)
        
        if param_name:
            return {"name": param_name, "type": "", "default": default_value}
        
        return None
    
    def _extract_import_names(self, node: ts.Node, source_code: str) -> List[str]:
        """Extract imported names from import clause."""
        names = []
        
        for child in node.children:
            if child.type == "identifier":
                names.append(self._get_node_text(child, source_code))
            elif child.type == "import_specifier":
                spec_name = self._get_node_text(child, source_code)
                names.append(spec_name)
            elif child.type == "namespace_import":
                names.append("*")
        
        return names
    
    def _extract_jsdoc_comment(self, node: ts.Node, source_code: str) -> Optional[str]:
        """Extract JSDoc comment for a node."""
        # Look for comment nodes immediately before this node
        parent = node.parent
        if not parent:
            return None
        
        try:
            node_index = parent.children.index(node)
            
            # Look backwards for JSDoc comments
            docs = []
            for i in range(node_index - 1, -1, -1):
                prev_node = parent.children[i]
                if prev_node.type == "comment":
                    comment_text = self._get_node_text(prev_node, source_code)
                    if comment_text.startswith("/**"):
                        docs.insert(0, comment_text)
                    elif comment_text.startswith("//"):
                        # Regular comment, stop looking
                        break
                elif prev_node.type not in ["comment"]:
                    break
            
            if docs:
                # Clean up JSDoc
                cleaned_docs = []
                for doc in docs:
                    lines = doc.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        line = line.strip()
                        # Remove /** and */ and leading *
                        line = line.replace('/**', '').replace('*/', '').strip()
                        if line.startswith('*'):
                            line = line[1:].strip()
                        if line:
                            cleaned_lines.append(line)
                    if cleaned_lines:
                        cleaned_docs.extend(cleaned_lines)
                
                return '\n'.join(cleaned_docs) if cleaned_docs else None
        
        except (ValueError, IndexError):
            pass
        
        return None
    
    def _create_function_signature(self, name: str, parameters: List[Dict[str, str]], 
                                  is_async: bool, is_generator: bool) -> str:
        """Create a function signature string."""
        signature_parts = []
        
        if is_async:
            signature_parts.append("async")
        
        if is_generator:
            signature_parts.append("function*")
        else:
            signature_parts.append("function")
        
        signature_parts.append(name)
        
        # Add parameters
        param_strs = []
        for param in parameters:
            param_str = param["name"]
            if param.get("default"):
                param_str += f" = {param['default']}"
            param_strs.append(param_str)
        
        signature_parts.append(f"({', '.join(param_strs)})")
        
        return ' '.join(signature_parts)
    
    def _get_import_type(self, content: str) -> str:
        """Determine the type of import."""
        if "* as" in content:
            return "namespace"
        elif "default" in content or not "{" in content:
            return "default"
        else:
            return "named"
    
    def _get_export_type(self, content: str) -> str:
        """Determine the type of export."""
        if "default" in content:
            return "default"
        else:
            return "named"
    
    def _get_method_kind(self, node: ts.Node, source_code: str) -> str:
        """Get the kind of method."""
        content = self._get_node_text(node, source_code)
        
        if "get " in content:
            return "getter"
        elif "set " in content:
            return "setter"
        elif "static" in content:
            return "static"
        elif "constructor" in content:
            return "constructor"
        else:
            return "method"
    
    def _is_in_export(self, node: ts.Node) -> bool:
        """Check if node is within an export statement."""
        parent = node.parent
        while parent:
            if parent.type == "export_statement":
                return True
            parent = parent.parent
        return False
    
    def _has_field_initializer(self, node: ts.Node) -> bool:
        """Check if field has an initializer."""
        for child in node.children:
            if child.type in ["=", "assignment_operator"]:
                return True
        return False