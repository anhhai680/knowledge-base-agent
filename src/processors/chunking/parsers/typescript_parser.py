"""
TypeScript tree-sitter parser for advanced semantic analysis.

This module provides comprehensive TypeScript parsing using tree-sitter,
supporting all TypeScript features including types, interfaces, generics,
decorators, namespaces, and modern ES6+ features.
"""

from typing import Dict, List, Optional, Set
import tree_sitter as ts
import tree_sitter_typescript as ts_typescript

from .javascript_parser import JavaScriptAdvancedParser
from .semantic_element import (
    SemanticElement, 
    ElementType, 
    SemanticPosition,
    AccessModifier,
    ParseResult
)
from ....utils.logging import get_logger

logger = get_logger(__name__)


class TypeScriptAdvancedParser(JavaScriptAdvancedParser):
    """
    Advanced TypeScript parser using tree-sitter for precise semantic analysis.
    
    Extends JavaScript parser with TypeScript-specific features:
    - Type annotations and type aliases
    - Interfaces and abstract classes
    - Generic types and constraints
    - Decorators and metadata
    - Namespaces and modules
    - Enums and const assertions
    - Access modifiers (public, private, protected)
    - Optional chaining and nullish coalescing
    - Template literal types
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize TypeScript tree-sitter parser."""
        # Initialize as JavaScript parser first
        super().__init__(config)
        self.language_name = "typescript"
        
        # TypeScript specific configuration
        self.extract_types = self.config.get('extract_types', True)
        self.preserve_interfaces = self.config.get('preserve_interfaces', True)
        self.chunk_by_module = self.config.get('chunk_by_module', True)
        self.include_decorators = self.config.get('include_decorators', True)
        self.extract_generics = self.config.get('extract_generics', True)
        
        # Re-initialize with TypeScript language
        self._initialize_parser()
    
    def _get_tree_sitter_language(self) -> ts.Language:
        """Get TypeScript tree-sitter language."""
        return ts.Language(ts_typescript.language_typescript())
    
    def _process_program(self, node: ts.Node, source_code: str) -> List[SemanticElement]:
        """Process the top-level program node with TypeScript features."""
        elements = []
        
        for child in node.children:
            # Handle TypeScript-specific constructs first
            if child.type == "interface_declaration":
                elements.append(self._extract_interface_declaration(child, source_code))
            elif child.type == "type_alias_declaration":
                elements.append(self._extract_type_alias_declaration(child, source_code))
            elif child.type == "enum_declaration":
                elements.append(self._extract_enum_declaration(child, source_code))
            elif child.type == "namespace_declaration":
                elements.append(self._extract_namespace_declaration(child, source_code))
            elif child.type == "module_declaration":
                elements.append(self._extract_module_declaration(child, source_code))
            elif child.type == "abstract_class_declaration":
                elements.append(self._extract_abstract_class_declaration(child, source_code))
            # Handle JavaScript constructs with TypeScript enhancements
            elif child.type == "class_declaration":
                elements.append(self._extract_typescript_class_declaration(child, source_code))
            elif child.type == "function_declaration":
                elements.append(self._extract_typescript_function_declaration(child, source_code))
            elif child.type == "variable_declaration":
                elements.extend(self._extract_typescript_variable_declaration(child, source_code))
            # Fall back to JavaScript handling for other constructs
            else:
                # Process using the same logic as JavaScript for import/export/etc
                if child.type == "import_statement":
                    if self.preserve_imports:
                        elements.append(self._extract_import_statement(child, source_code))
                        self._is_module = True
                elif child.type == "export_statement":
                    if self.extract_exports:
                        elements.append(self._extract_export_statement(child, source_code))
                        self._is_module = True
                elif child.type == "comment" and self.extract_comments:
                    elements.append(self._extract_comment(child, source_code))
        
        return elements
    
    def _extract_interface_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript interface declaration."""
        # Get interface name
        name_node = self._find_child_by_type(node, "type_identifier")
        interface_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Extract generic parameters
        generic_params = self._extract_typescript_generic_parameters(node, source_code)
        
        # Extract extends clause
        extends_types = self._extract_heritage_clause(node, source_code, "extends_clause")
        
        # Extract decorators
        decorators = []
        if self.include_decorators:
            decorators = self._extract_typescript_decorators(node, source_code)
        
        # Extract JSDoc
        documentation = self._extract_jsdoc_comment(node, source_code)
        
        # Create interface element
        interface_element = SemanticElement(
            name=interface_name,
            element_type=ElementType.INTERFACE,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            generic_parameters=generic_params,
            decorators=decorators,
            documentation=documentation,
            tree_sitter_node_type=node.type,
            language_specific={
                "extends_types": extends_types,
                "is_exported": self._is_in_export(node),
                "is_declared": self._is_declared(node)
            }
        )
        
        # Process interface body
        object_type = self._find_child_by_type(node, "object_type")
        if object_type:
            for child in object_type.children:
                if child.type == "property_signature":
                    prop = self._extract_property_signature(child, source_code)
                    interface_element.add_child(prop)
                elif child.type == "method_signature":
                    method = self._extract_method_signature(child, source_code)
                    interface_element.add_child(method)
                elif child.type == "index_signature":
                    index = self._extract_index_signature(child, source_code)
                    interface_element.add_child(index)
        
        return interface_element
    
    def _extract_type_alias_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript type alias declaration."""
        # Get type name
        name_node = self._find_child_by_type(node, "type_identifier")
        type_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Extract generic parameters
        generic_params = self._extract_typescript_generic_parameters(node, source_code)
        
        # Extract the type definition
        type_annotation = self._extract_type_annotation(node, source_code)
        
        # Extract JSDoc
        documentation = self._extract_jsdoc_comment(node, source_code)
        
        return SemanticElement(
            name=type_name,
            element_type=ElementType.TYPE_ALIAS,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            generic_parameters=generic_params,
            documentation=documentation,
            tree_sitter_node_type=node.type,
            language_specific={
                "type_definition": type_annotation,
                "is_exported": self._is_in_export(node),
                "is_declared": self._is_declared(node)
            }
        )
    
    def _extract_enum_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript enum declaration."""
        # Get enum name
        name_node = self._find_child_by_type(node, "identifier")
        enum_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Check if const enum
        is_const = "const" in self._get_node_text(node, source_code)
        
        # Extract JSDoc
        documentation = self._extract_jsdoc_comment(node, source_code)
        
        # Create enum element
        enum_element = SemanticElement(
            name=enum_name,
            element_type=ElementType.ENUM,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            documentation=documentation,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_const": is_const,
                "is_exported": self._is_in_export(node),
                "is_declared": self._is_declared(node)
            }
        )
        
        # Process enum body
        enum_body = self._find_child_by_type(node, "enum_body")
        if enum_body:
            for child in enum_body.children:
                if child.type == "property_identifier":
                    member = self._extract_enum_member(child, source_code)
                    enum_element.add_child(member)
        
        return enum_element
    
    def _extract_namespace_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript namespace declaration."""
        # Get namespace name
        name_node = self._find_child_by_type(node, "identifier")
        namespace_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Extract JSDoc
        documentation = self._extract_jsdoc_comment(node, source_code)
        
        # Create namespace element
        namespace_element = SemanticElement(
            name=namespace_name,
            element_type=ElementType.NAMESPACE,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            documentation=documentation,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_exported": self._is_in_export(node),
                "is_declared": self._is_declared(node)
            }
        )
        
        # Process namespace body
        statement_block = self._find_child_by_type(node, "statement_block")
        if statement_block:
            for child in statement_block.children:
                # Recursively process namespace contents
                if child.type in ["class_declaration", "interface_declaration", "function_declaration",
                                "type_alias_declaration", "enum_declaration", "namespace_declaration"]:
                    # Process the child using appropriate extraction method
                    child_element = self._extract_namespace_member(child, source_code)
                    if child_element:
                        namespace_element.add_child(child_element)
        
        return namespace_element
    
    def _extract_module_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript module declaration."""
        # Similar to namespace but for ambient modules
        return self._extract_namespace_declaration(node, source_code)
    
    def _extract_abstract_class_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript abstract class declaration."""
        # Extract as regular class but mark as abstract
        class_element = self._extract_typescript_class_declaration(node, source_code)
        class_element.access_modifiers.append(AccessModifier.ABSTRACT)
        class_element.language_specific["is_abstract"] = True
        
        return class_element
    
    def _extract_typescript_class_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript class declaration with type information."""
        # Start with JavaScript class extraction
        class_element = super()._extract_class_declaration(node, source_code)
        
        # Add TypeScript-specific features
        
        # Extract generic parameters
        generic_params = self._extract_typescript_generic_parameters(node, source_code)
        class_element.generic_parameters = generic_params
        
        # Extract implements clause
        implements_types = self._extract_heritage_clause(node, source_code, "implements_clause")
        
        # Extract decorators
        decorators = []
        if self.include_decorators:
            decorators = self._extract_typescript_decorators(node, source_code)
        class_element.decorators = decorators
        
        # Update language-specific info
        class_element.language_specific.update({
            "implements_types": implements_types,
            "is_abstract": "abstract" in self._get_node_text(node, source_code),
            "has_decorators": len(decorators) > 0
        })
        
        return class_element
    
    def _extract_typescript_function_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript function declaration with type information."""
        # Start with JavaScript function extraction
        function_element = super()._extract_function_declaration(node, source_code)
        
        # Add TypeScript-specific features
        
        # Extract generic parameters
        generic_params = self._extract_typescript_generic_parameters(node, source_code)
        function_element.generic_parameters = generic_params
        
        # Extract return type
        return_type = self._extract_function_return_type(node, source_code)
        function_element.return_type = return_type
        
        # Extract typed parameters
        typed_parameters = self._extract_typescript_function_parameters(node, source_code)
        function_element.parameters = typed_parameters
        
        # Extract decorators
        decorators = []
        if self.include_decorators:
            decorators = self._extract_typescript_decorators(node, source_code)
        function_element.decorators = decorators
        
        # Update signature with type information
        function_element.signature = self._create_typescript_function_signature(
            function_element.name, typed_parameters, return_type, generic_params,
            AccessModifier.ASYNC in function_element.access_modifiers,
            function_element.language_specific.get("is_generator", False)
        )
        
        # Update language-specific info
        function_element.language_specific.update({
            "has_decorators": len(decorators) > 0,
            "is_declared": self._is_declared(node)
        })
        
        return function_element
    
    def _extract_typescript_variable_declaration(self, node: ts.Node, source_code: str) -> List[SemanticElement]:
        """Extract TypeScript variable declarations with type information."""
        # Start with JavaScript variable extraction
        elements = super()._extract_variable_declaration(node, source_code)
        
        # Enhance with TypeScript type information
        for element in elements:
            # Extract type annotation if present
            type_annotation = self._extract_variable_type_annotation(node, source_code, element.name)
            if type_annotation:
                element.language_specific["type_annotation"] = type_annotation
        
        return elements
    
    def _extract_property_signature(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript property signature from interface."""
        # Get property name
        name_node = self._find_child_by_type(node, "property_identifier")
        prop_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Extract type annotation
        type_annotation = self._extract_type_annotation(node, source_code)
        
        # Check if optional
        is_optional = "?" in self._get_node_text(node, source_code)
        is_readonly = "readonly" in self._get_node_text(node, source_code)
        
        modifiers = []
        if is_readonly:
            modifiers.append(AccessModifier.READONLY)
        
        return SemanticElement(
            name=prop_name,
            element_type=ElementType.PROPERTY,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            access_modifiers=modifiers,
            tree_sitter_node_type=node.type,
            language_specific={
                "type_annotation": type_annotation,
                "is_optional": is_optional,
                "is_readonly": is_readonly
            }
        )
    
    def _extract_method_signature(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript method signature from interface."""
        # Get method name
        name_node = self._find_child_by_type(node, "property_identifier")
        method_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Extract parameters
        parameters = self._extract_typescript_function_parameters(node, source_code)
        
        # Extract return type
        return_type = self._extract_function_return_type(node, source_code)
        
        # Extract generic parameters
        generic_params = self._extract_typescript_generic_parameters(node, source_code)
        
        # Check if optional
        is_optional = "?" in self._get_node_text(node, source_code)
        
        # Create signature
        signature = self._create_typescript_function_signature(
            method_name, parameters, return_type, generic_params, False, False
        )
        
        return SemanticElement(
            name=method_name,
            element_type=ElementType.METHOD,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            signature=signature,
            parameters=parameters,
            return_type=return_type,
            generic_parameters=generic_params,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_optional": is_optional,
                "is_signature": True
            }
        )
    
    def _extract_index_signature(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript index signature."""
        content = self._get_node_text(node, source_code)
        
        return SemanticElement(
            name="[index]",
            element_type=ElementType.PROPERTY,
            position=self._create_position(node),
            content=content,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_index_signature": True
            }
        )
    
    def _extract_enum_member(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract TypeScript enum member."""
        member_name = self._get_node_text(node, source_code)
        
        return SemanticElement(
            name=member_name,
            element_type=ElementType.FIELD,
            position=self._create_position(node),
            content=member_name,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_enum_member": True
            }
        )
    
    def _extract_namespace_member(self, node: ts.Node, source_code: str) -> Optional[SemanticElement]:
        """Extract a member from within a namespace."""
        if node.type == "class_declaration":
            return self._extract_typescript_class_declaration(node, source_code)
        elif node.type == "interface_declaration":
            return self._extract_interface_declaration(node, source_code)
        elif node.type == "function_declaration":
            return self._extract_typescript_function_declaration(node, source_code)
        elif node.type == "type_alias_declaration":
            return self._extract_type_alias_declaration(node, source_code)
        elif node.type == "enum_declaration":
            return self._extract_enum_declaration(node, source_code)
        elif node.type == "namespace_declaration":
            return self._extract_namespace_declaration(node, source_code)
        
        return None
    
    def _extract_typescript_generic_parameters(self, node: ts.Node, source_code: str) -> List[str]:
        """Extract TypeScript generic parameters."""
        generic_params = []
        
        type_params_node = self._find_child_by_type(node, "type_parameters")
        if type_params_node:
            for child in type_params_node.children:
                if child.type == "type_parameter":
                    param_text = self._get_node_text(child, source_code)
                    generic_params.append(param_text)
        
        return generic_params
    
    def _extract_heritage_clause(self, node: ts.Node, source_code: str, clause_type: str) -> List[str]:
        """Extract extends or implements clause."""
        types = []
        
        clause_node = self._find_child_by_type(node, clause_type)
        if clause_node:
            for child in clause_node.children:
                if child.type in ["type_identifier", "generic_type", "qualified_name"]:
                    type_text = self._get_node_text(child, source_code)
                    types.append(type_text)
        
        return types
    
    def _extract_typescript_decorators(self, node: ts.Node, source_code: str) -> List[str]:
        """Extract TypeScript decorators."""
        decorators = []
        
        # Look for decorator nodes before the main node
        parent = node.parent
        if parent:
            try:
                node_index = parent.children.index(node)
                
                # Look backwards for decorators
                for i in range(node_index - 1, -1, -1):
                    prev_node = parent.children[i]
                    if prev_node.type == "decorator":
                        decorator_text = self._get_node_text(prev_node, source_code)
                        decorators.insert(0, decorator_text)
                    elif prev_node.type not in ["comment"]:
                        break
            except (ValueError, IndexError):
                pass
        
        return decorators
    
    def _extract_type_annotation(self, node: ts.Node, source_code: str) -> Optional[str]:
        """Extract type annotation from a node."""
        type_annotation_node = self._find_child_by_type(node, "type_annotation")
        if type_annotation_node:
            # Skip the ":" and get the actual type
            for child in type_annotation_node.children:
                if child.type != ":":
                    return self._get_node_text(child, source_code)
        
        return None
    
    def _extract_function_return_type(self, node: ts.Node, source_code: str) -> Optional[str]:
        """Extract function return type annotation."""
        return self._extract_type_annotation(node, source_code)
    
    def _extract_variable_type_annotation(self, node: ts.Node, source_code: str, var_name: str) -> Optional[str]:
        """Extract type annotation for a specific variable."""
        # Find the variable declarator for this variable
        for child in node.children:
            if child.type == "variable_declarator":
                # Check if this is the right variable
                name_node = self._find_child_by_type(child, "identifier")
                if name_node and self._get_node_text(name_node, source_code) == var_name:
                    return self._extract_type_annotation(child, source_code)
        
        return None
    
    def _extract_typescript_function_parameters(self, node: ts.Node, source_code: str) -> List[Dict[str, str]]:
        """Extract TypeScript function parameters with type information."""
        parameters = []
        
        param_node = self._find_child_by_type(node, "formal_parameters")
        if param_node:
            for child in param_node.children:
                if child.type == "required_parameter":
                    param_info = self._extract_typescript_parameter_info(child, source_code)
                    if param_info:
                        parameters.append(param_info)
                elif child.type == "optional_parameter":
                    param_info = self._extract_typescript_parameter_info(child, source_code)
                    if param_info:
                        param_info["optional"] = "true"
                        parameters.append(param_info)
                elif child.type == "rest_parameter":
                    param_info = self._extract_typescript_rest_parameter(child, source_code)
                    if param_info:
                        parameters.append(param_info)
        
        return parameters
    
    def _extract_typescript_parameter_info(self, param_node: ts.Node, source_code: str) -> Optional[Dict[str, str]]:
        """Extract information from a TypeScript parameter node."""
        param_name = ""
        param_type = ""
        default_value = ""
        
        for child in param_node.children:
            if child.type == "identifier":
                param_name = self._get_node_text(child, source_code)
            elif child.type == "type_annotation":
                param_type = self._extract_type_annotation(param_node, source_code) or ""
            elif child.type in ["assignment_pattern", "default_parameter"]:
                # Parameter with default value
                default_value = self._get_node_text(child, source_code)
        
        if param_name:
            return {
                "name": param_name,
                "type": param_type,
                "default": default_value,
                "optional": "false"
            }
        
        return None
    
    def _extract_typescript_rest_parameter(self, param_node: ts.Node, source_code: str) -> Optional[Dict[str, str]]:
        """Extract TypeScript rest parameter information."""
        param_text = self._get_node_text(param_node, source_code)
        
        # Extract the parameter name (after ...)
        name_parts = param_text.replace("...", "").strip().split(":")
        param_name = name_parts[0].strip()
        param_type = name_parts[1].strip() if len(name_parts) > 1 else ""
        
        return {
            "name": f"...{param_name}",
            "type": param_type,
            "default": "",
            "optional": "false",
            "is_rest": "true"
        }
    
    def _create_typescript_function_signature(self, name: str, parameters: List[Dict[str, str]], 
                                            return_type: Optional[str], generic_params: List[str],
                                            is_async: bool, is_generator: bool) -> str:
        """Create a TypeScript function signature string."""
        signature_parts = []
        
        if is_async:
            signature_parts.append("async")
        
        if is_generator:
            signature_parts.append("function*")
        else:
            signature_parts.append("function")
        
        # Add function name with generics
        if generic_params:
            signature_parts.append(f"{name}<{', '.join(generic_params)}>")
        else:
            signature_parts.append(name)
        
        # Add parameters with types
        param_strs = []
        for param in parameters:
            param_str = param["name"]
            if param.get("optional") == "true":
                param_str += "?"
            if param.get("type"):
                param_str += f": {param['type']}"
            if param.get("default"):
                param_str += f" = {param['default']}"
            param_strs.append(param_str)
        
        signature_parts.append(f"({', '.join(param_strs)})")
        
        # Add return type
        if return_type:
            signature_parts.append(f": {return_type}")
        
        return ' '.join(signature_parts)
    
    def _is_declared(self, node: ts.Node) -> bool:
        """Check if node is in a declare context."""
        # Look for 'declare' keyword in ancestors
        parent = node.parent
        while parent:
            node_text = self._get_node_text(parent, "")
            if node_text.startswith("declare "):
                return True
            parent = parent.parent
        return False