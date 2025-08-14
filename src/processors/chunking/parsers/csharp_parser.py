"""
C# tree-sitter parser for advanced semantic analysis.

This module provides comprehensive C# parsing using tree-sitter,
supporting all modern C# language features including generics, LINQ,
attributes, XML documentation, and more.
"""

from typing import Dict, List, Optional, Set
import tree_sitter as ts
import tree_sitter_c_sharp as ts_csharp

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


class CSharpAdvancedParser(AdvancedParser):
    """
    Advanced C# parser using tree-sitter for precise semantic analysis.
    
    Supports comprehensive C# language features:
    - Classes, interfaces, structs, enums, records
    - Methods, properties, fields, events, indexers
    - Generics and constraints
    - Attributes and XML documentation
    - Namespaces and using statements
    - LINQ expressions and lambda functions
    - Async/await patterns
    - Nullable reference types
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize C# tree-sitter parser."""
        super().__init__("csharp", config)
        
        # C# specific configuration
        self.extract_attributes = self.config.get('extract_attributes', True)
        self.extract_xml_docs = self.config.get('extract_xml_docs', True)
        self.include_using_statements = self.config.get('include_using_statements', True)
        self.preserve_namespaces = self.config.get('preserve_namespaces', True)
        self.chunk_by_class = self.config.get('chunk_by_class', True)
        
        # Track namespace context
        self._current_namespace = ""
    
    def _get_tree_sitter_language(self) -> ts.Language:
        """Get C# tree-sitter language."""
        return ts.Language(ts_csharp.language())
    
    def _extract_semantic_elements(self, tree: ts.Tree, source_code: str) -> List[SemanticElement]:
        """Extract semantic elements from C# syntax tree."""
        elements = []
        self._current_namespace = ""
        
        # Process the root compilation unit
        root = tree.root_node
        elements.extend(self._process_compilation_unit(root, source_code))
        
        return elements
    
    def _process_compilation_unit(self, node: ts.Node, source_code: str) -> List[SemanticElement]:
        """Process the top-level compilation unit."""
        elements = []
        
        for child in node.children:
            if child.type == "using_directive":
                if self.include_using_statements:
                    elements.append(self._extract_using_directive(child, source_code))
            elif child.type == "namespace_declaration":
                elements.extend(self._extract_namespace_declaration(child, source_code))
            elif child.type in ["class_declaration", "interface_declaration", "struct_declaration", 
                              "enum_declaration", "record_declaration"]:
                elements.append(self._extract_type_declaration(child, source_code))
            elif child.type in ["method_declaration", "property_declaration", "field_declaration",
                              "constructor_declaration", "destructor_declaration"]:
                elements.append(self._extract_member_declaration(child, source_code))
        
        return elements
    
    def _extract_using_directive(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract using directive information."""
        content = self._get_node_text(node, source_code)
        
        # Extract the namespace being imported
        namespace_node = self._find_child_by_type(node, "qualified_name")
        if not namespace_node:
            namespace_node = self._find_child_by_type(node, "identifier")
        
        namespace_name = self._get_node_text(namespace_node, source_code) if namespace_node else "unknown"
        
        return SemanticElement(
            name=namespace_name,
            element_type=ElementType.USING,
            position=self._create_position(node),
            content=content.strip(),
            tree_sitter_node_type=node.type,
            language_specific={
                "is_static": "static" in content,
                "is_alias": " = " in content,
                "full_directive": content
            }
        )
    
    def _extract_namespace_declaration(self, node: ts.Node, source_code: str) -> List[SemanticElement]:
        """Extract namespace declaration and its contents."""
        elements = []
        
        # Get namespace name
        name_node = self._find_child_by_type(node, "qualified_name")
        if not name_node:
            name_node = self._find_child_by_type(node, "identifier")
        
        namespace_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Update current namespace context
        old_namespace = self._current_namespace
        self._current_namespace = namespace_name if not self._current_namespace else f"{self._current_namespace}.{namespace_name}"
        
        # Create namespace element
        namespace_element = SemanticElement(
            name=namespace_name,
            element_type=ElementType.NAMESPACE,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            parent_name=old_namespace if old_namespace else None,
            tree_sitter_node_type=node.type,
            language_specific={
                "full_name": self._current_namespace,
                "is_file_scoped": node.type == "file_scoped_namespace_declaration"
            }
        )
        
        # Process namespace body
        body_node = self._find_child_by_type(node, "declaration_list")
        if body_node:
            for child in body_node.children:
                if child.type in ["class_declaration", "interface_declaration", "struct_declaration",
                                "enum_declaration", "record_declaration"]:
                    namespace_element.add_child(self._extract_type_declaration(child, source_code))
                elif child.type in ["method_declaration", "property_declaration", "field_declaration"]:
                    namespace_element.add_child(self._extract_member_declaration(child, source_code))
                elif child.type == "namespace_declaration":
                    nested_namespaces = self._extract_namespace_declaration(child, source_code)
                    for ns in nested_namespaces:
                        namespace_element.add_child(ns)
        
        elements.append(namespace_element)
        
        # Restore namespace context
        self._current_namespace = old_namespace
        
        return elements
    
    def _extract_type_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract class, interface, struct, enum, or record declaration."""
        # Get type name
        name_node = self._find_child_by_type(node, "identifier")
        type_name = self._get_node_text(name_node, source_code) if name_node else "unknown"
        
        # Determine element type
        element_type_map = {
            "class_declaration": ElementType.CLASS,
            "interface_declaration": ElementType.INTERFACE,
            "struct_declaration": ElementType.STRUCT,
            "enum_declaration": ElementType.ENUM,
            "record_declaration": ElementType.CLASS,  # Records are special classes
        }
        element_type = element_type_map.get(node.type, ElementType.CLASS)
        
        # Extract modifiers
        modifiers = self._extract_modifiers(node, source_code)
        
        # Extract generic parameters
        generic_params = self._extract_generic_parameters(node, source_code)
        
        # Extract base types
        base_types = self._extract_base_list(node, source_code)
        
        # Extract attributes
        attributes = []
        if self.extract_attributes:
            attributes = self._extract_attributes(node, source_code)
        
        # Extract XML documentation
        documentation = None
        if self.extract_xml_docs:
            documentation = self._extract_xml_documentation(node, source_code)
        
        # Create the type element
        type_element = SemanticElement(
            name=type_name,
            element_type=element_type,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            parent_name=self._current_namespace if self._current_namespace else None,
            access_modifiers=modifiers,
            generic_parameters=generic_params,
            attributes=attributes,
            documentation=documentation,
            tree_sitter_node_type=node.type,
            language_specific={
                "base_types": base_types,
                "is_partial": "partial" in self._get_node_text(node, source_code),
                "is_record": node.type == "record_declaration",
                "namespace": self._current_namespace
            }
        )
        
        # Process type body
        body_node = self._find_child_by_type(node, "declaration_list")
        if body_node:
            for child in body_node.children:
                if child.type in ["method_declaration", "property_declaration", "field_declaration",
                                "constructor_declaration", "destructor_declaration", "indexer_declaration",
                                "event_declaration", "operator_declaration"]:
                    member = self._extract_member_declaration(child, source_code)
                    type_element.add_child(member)
                elif child.type in ["class_declaration", "interface_declaration", "struct_declaration",
                                  "enum_declaration", "record_declaration"]:
                    nested_type = self._extract_type_declaration(child, source_code)
                    type_element.add_child(nested_type)
        
        return type_element
    
    def _extract_member_declaration(self, node: ts.Node, source_code: str) -> SemanticElement:
        """Extract method, property, field, or other member declaration."""
        member_type_map = {
            "method_declaration": ElementType.METHOD,
            "property_declaration": ElementType.PROPERTY,
            "field_declaration": ElementType.FIELD,
            "constructor_declaration": ElementType.CONSTRUCTOR,
            "destructor_declaration": ElementType.METHOD,
            "indexer_declaration": ElementType.PROPERTY,
            "event_declaration": ElementType.FIELD,
            "operator_declaration": ElementType.METHOD,
        }
        
        element_type = member_type_map.get(node.type, ElementType.METHOD)
        
        # Extract member name
        member_name = self._extract_member_name(node, source_code)
        
        # Extract modifiers
        modifiers = self._extract_modifiers(node, source_code)
        
        # Extract return type
        return_type = self._extract_return_type(node, source_code)
        
        # Extract parameters
        parameters = self._extract_parameters(node, source_code)
        
        # Extract generic parameters
        generic_params = self._extract_generic_parameters(node, source_code)
        
        # Extract attributes
        attributes = []
        if self.extract_attributes:
            attributes = self._extract_attributes(node, source_code)
        
        # Extract XML documentation
        documentation = None
        if self.extract_xml_docs:
            documentation = self._extract_xml_documentation(node, source_code)
        
        # Create signature
        signature = self._create_member_signature(member_name, return_type, parameters, generic_params)
        
        return SemanticElement(
            name=member_name,
            element_type=element_type,
            position=self._create_position(node),
            content=self._get_node_text(node, source_code),
            signature=signature,
            access_modifiers=modifiers,
            return_type=return_type,
            parameters=parameters,
            generic_parameters=generic_params,
            attributes=attributes,
            documentation=documentation,
            tree_sitter_node_type=node.type,
            language_specific={
                "is_extension_method": self._is_extension_method(node, source_code),
                "is_async": AccessModifier.ASYNC in modifiers,
                "has_body": self._has_method_body(node)
            }
        )
    
    def _extract_modifiers(self, node: ts.Node, source_code: str) -> List[AccessModifier]:
        """Extract access modifiers from a declaration."""
        modifiers = []
        
        # Look for modifier list
        modifiers_node = self._find_child_by_type(node, "modifier")
        if not modifiers_node:
            # Check for individual modifier nodes
            for child in node.children:
                if child.type in ["public", "private", "protected", "internal", "static", 
                                "abstract", "virtual", "override", "readonly", "async"]:
                    modifier_text = self._get_node_text(child, source_code)
                    if modifier_text in [m.value for m in AccessModifier]:
                        modifiers.append(AccessModifier(modifier_text))
        else:
            modifier_text = self._get_node_text(modifiers_node, source_code)
            for word in modifier_text.split():
                if word in [m.value for m in AccessModifier]:
                    modifiers.append(AccessModifier(word))
        
        # If no explicit access modifier, infer default
        has_access_modifier = any(m in [AccessModifier.PUBLIC, AccessModifier.PRIVATE, 
                                      AccessModifier.PROTECTED, AccessModifier.INTERNAL] 
                                for m in modifiers)
        if not has_access_modifier:
            # Default access modifiers in C#
            if node.type in ["class_declaration", "interface_declaration", "struct_declaration", 
                           "enum_declaration"]:
                modifiers.append(AccessModifier.INTERNAL)  # Default for types
            else:
                modifiers.append(AccessModifier.PRIVATE)   # Default for members
        
        return modifiers
    
    def _extract_generic_parameters(self, node: ts.Node, source_code: str) -> List[str]:
        """Extract generic type parameters."""
        generic_params = []
        
        type_params_node = self._find_child_by_type(node, "type_parameter_list")
        if type_params_node:
            for child in type_params_node.children:
                if child.type == "type_parameter":
                    param_name = self._get_node_text(child, source_code)
                    generic_params.append(param_name)
        
        return generic_params
    
    def _extract_base_list(self, node: ts.Node, source_code: str) -> List[str]:
        """Extract base class and interface list."""
        base_types = []
        
        base_list_node = self._find_child_by_type(node, "base_list")
        if base_list_node:
            for child in base_list_node.children:
                if child.type in ["identifier", "qualified_name", "generic_name"]:
                    base_type = self._get_node_text(child, source_code)
                    base_types.append(base_type)
        
        return base_types
    
    def _extract_member_name(self, node: ts.Node, source_code: str) -> str:
        """Extract member name from declaration node."""
        # Try different name patterns
        name_node = self._find_child_by_type(node, "identifier")
        if name_node:
            return self._get_node_text(name_node, source_code)
        
        # For operators, constructors, etc.
        if node.type == "constructor_declaration":
            # Constructor name is the containing class name
            return "constructor"
        elif node.type == "destructor_declaration":
            return "destructor"
        elif node.type == "operator_declaration":
            operator_token = self._find_child_by_type(node, "operator_token")
            if operator_token:
                return f"operator {self._get_node_text(operator_token, source_code)}"
        
        return "unknown"
    
    def _extract_return_type(self, node: ts.Node, source_code: str) -> Optional[str]:
        """Extract return type from method or property declaration."""
        type_node = self._find_child_by_type(node, "type")
        if type_node:
            return self._get_node_text(type_node, source_code)
        
        # For constructors, destructors
        if node.type in ["constructor_declaration", "destructor_declaration"]:
            return None
        
        return "void"  # Default for methods without explicit return type
    
    def _extract_parameters(self, node: ts.Node, source_code: str) -> List[Dict[str, str]]:
        """Extract method parameters."""
        parameters = []
        
        param_list_node = self._find_child_by_type(node, "parameter_list")
        if param_list_node:
            for child in param_list_node.children:
                if child.type == "parameter":
                    param_info = self._extract_parameter_info(child, source_code)
                    if param_info:
                        parameters.append(param_info)
        
        return parameters
    
    def _extract_parameter_info(self, param_node: ts.Node, source_code: str) -> Optional[Dict[str, str]]:
        """Extract information from a single parameter node."""
        param_type = ""
        param_name = ""
        param_modifier = ""
        default_value = ""
        
        for child in param_node.children:
            if child.type == "type":
                param_type = self._get_node_text(child, source_code)
            elif child.type == "identifier":
                param_name = self._get_node_text(child, source_code)
            elif child.type in ["ref", "out", "in", "params"]:
                param_modifier = self._get_node_text(child, source_code)
            elif child.type == "equals_value_clause":
                default_value = self._get_node_text(child, source_code)
        
        if param_name:
            return {
                "name": param_name,
                "type": param_type,
                "modifier": param_modifier,
                "default": default_value.replace("= ", "") if default_value else ""
            }
        
        return None
    
    def _extract_attributes(self, node: ts.Node, source_code: str) -> List[str]:
        """Extract C# attributes."""
        attributes = []
        
        # Look for attribute lists
        for child in node.children:
            if child.type == "attribute_list":
                attr_text = self._get_node_text(child, source_code)
                # Clean up attribute text
                attr_text = attr_text.strip("[]")
                attributes.append(attr_text)
        
        return attributes
    
    def _extract_xml_documentation(self, node: ts.Node, source_code: str) -> Optional[str]:
        """Extract XML documentation comments."""
        # Look for documentation comments before the node
        parent = node.parent
        if not parent:
            return None
        
        try:
            node_index = parent.children.index(node)
            
            # Look backwards for documentation comments
            docs = []
            for i in range(node_index - 1, -1, -1):
                prev_node = parent.children[i]
                if prev_node.type == "comment" and "///" in self._get_node_text(prev_node, source_code):
                    doc_text = self._get_node_text(prev_node, source_code)
                    docs.insert(0, doc_text)
                elif prev_node.type not in ["comment", "whitespace"]:
                    break
            
            if docs:
                # Clean up XML documentation
                cleaned_docs = []
                for doc in docs:
                    # Remove /// prefix and clean up
                    lines = doc.split('\n')
                    cleaned_lines = []
                    for line in lines:
                        line = line.strip()
                        if line.startswith('///'):
                            line = line[3:].strip()
                        if line:
                            cleaned_lines.append(line)
                    if cleaned_lines:
                        cleaned_docs.extend(cleaned_lines)
                
                return '\n'.join(cleaned_docs) if cleaned_docs else None
        
        except (ValueError, IndexError):
        except (ValueError, IndexError) as e:
            logger.debug(
                "Exception during XML documentation extraction for node %r: %s",
                node, e
            )
        
        return None
    
    def _create_member_signature(self, name: str, return_type: Optional[str], 
                                parameters: List[Dict[str, str]], 
                                generic_params: List[str]) -> str:
        """Create a method signature string."""
        signature_parts = []
        
        # Add generic parameters
        if generic_params:
            generic_part = f"<{', '.join(generic_params)}>"
            signature_parts.append(f"{name}{generic_part}")
        else:
            signature_parts.append(name)
        
        # Add parameters
        param_strs = []
        for param in parameters:
            param_str = ""
            if param.get("modifier"):
                param_str += f"{param['modifier']} "
            param_str += f"{param['type']} {param['name']}"
            if param.get("default"):
                param_str += f" = {param['default']}"
            param_strs.append(param_str)
        
        signature_parts.append(f"({', '.join(param_strs)})")
        
        # Add return type
        if return_type:
            return f"{return_type} {' '.join(signature_parts)}"
        else:
            return ' '.join(signature_parts)
    
    def _is_extension_method(self, node: ts.Node, source_code: str) -> bool:
        """Check if method is an extension method."""
        param_list_node = self._find_child_by_type(node, "parameter_list")
        if param_list_node and param_list_node.children:
            first_param = param_list_node.children[0]
            if first_param.type == "parameter":
                param_text = self._get_node_text(first_param, source_code)
                return "this " in param_text
        return False
    
    def _has_method_body(self, node: ts.Node) -> bool:
        """Check if method has a body implementation."""
        body_node = self._find_child_by_type(node, "block")
        return body_node is not None