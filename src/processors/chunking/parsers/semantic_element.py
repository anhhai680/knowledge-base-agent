"""
Enhanced semantic element data structures for tree-sitter based parsing.

This module provides comprehensive data structures for representing semantic
elements extracted from source code using tree-sitter parsers.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class ElementType(Enum):
    """Types of semantic elements that can be extracted from source code."""
    
    # Import/Export related
    IMPORT = "import"
    USING = "using"
    EXPORT = "export"
    
    # Namespace/Module organization
    NAMESPACE = "namespace" 
    MODULE = "module"
    
    # Type definitions
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"
    
    # Function/Method definitions
    FUNCTION = "function"
    METHOD = "method"
    CONSTRUCTOR = "constructor"
    PROPERTY = "property"
    FIELD = "field"
    
    # Variables and constants
    VARIABLE = "variable"
    CONSTANT = "constant"
    
    # Special constructs
    DECORATOR = "decorator"
    ATTRIBUTE = "attribute"
    COMMENT = "comment"
    DOCUMENTATION = "documentation"
    
    # Generic content
    CONTENT = "content"
    OTHER = "other"


class AccessModifier(Enum):
    """Access modifiers for class members."""
    
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"
    STATIC = "static"
    ABSTRACT = "abstract"
    VIRTUAL = "virtual"
    OVERRIDE = "override"
    READONLY = "readonly"
    ASYNC = "async"


@dataclass
class SemanticPosition:
    """Represents position information for a semantic element."""
    
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    start_byte: int
    end_byte: int
    
    def __post_init__(self):
        """Validate position data."""
        if self.start_line < 0 or self.end_line < 0:
            raise ValueError("Line numbers must be non-negative")
        if self.start_line > self.end_line:
            raise ValueError("Start line must be <= end line")
        if self.start_line == self.end_line and self.start_column > self.end_column:
            raise ValueError("Start column must be <= end column on same line")
        if self.start_byte < 0 or self.end_byte < 0:
            raise ValueError("Byte positions must be non-negative")
        if self.start_byte > self.end_byte:
            raise ValueError("Start byte must be <= end byte")


@dataclass
class SemanticElement:
    """
    Enhanced semantic element with tree-sitter metadata.
    
    Represents a semantic unit of code (class, method, import, etc.) with
    precise positioning, type information, and hierarchical relationships.
    """
    
    # Core identification
    name: str
    element_type: ElementType
    position: SemanticPosition
    
    # Content and structure
    content: str = ""
    signature: Optional[str] = None
    
    # Hierarchical relationships
    parent_name: Optional[str] = None
    children: List['SemanticElement'] = field(default_factory=list)
    
    # Language-specific attributes
    access_modifiers: List[AccessModifier] = field(default_factory=list)
    return_type: Optional[str] = None
    parameters: List[Dict[str, str]] = field(default_factory=list)
    generic_parameters: List[str] = field(default_factory=list)
    
    # Documentation and metadata
    documentation: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    
    # Language-specific extensions
    language_specific: Dict[str, Any] = field(default_factory=dict)
    
    # Parser-specific metadata
    tree_sitter_node_type: Optional[str] = None
    # Stores additional metadata extracted from tree-sitter nodes.
    # Typical keys may include 'is_definition', 'is_reference', 'node_id', or other
    # parser-specific attributes. The structure is a dictionary mapping string keys
    # to values of any type, allowing flexible extension for language-specific or
    # parser-specific information.
    additional_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize the semantic element."""
        if not self.name and self.element_type not in [ElementType.CONTENT, ElementType.COMMENT]:
            raise ValueError(f"Name is required for element type {self.element_type}")
    
    @property
    def full_name(self) -> str:
        """Get the fully qualified name including parent context."""
        if self.parent_name:
            return f"{self.parent_name}.{self.name}"
        return self.name
    
    @property
    def is_public(self) -> bool:
        """Check if the element has public access."""
        return (AccessModifier.PUBLIC in self.access_modifiers or 
                len(self.access_modifiers) == 0)  # Default to public if no modifiers
    
    @property
    def is_static(self) -> bool:
        """Check if the element is static."""
        return AccessModifier.STATIC in self.access_modifiers
    
    @property
    def is_async(self) -> bool:
        """Check if the element is async."""
        return AccessModifier.ASYNC in self.access_modifiers
    
    @property
    def has_documentation(self) -> bool:
        """Check if the element has documentation."""
        return bool(self.documentation and self.documentation.strip())
    
    def add_child(self, child: 'SemanticElement') -> None:
        """Add a child element and set its parent reference."""
        child.parent_name = self.full_name
        self.children.append(child)
    
    def get_children_by_type(self, element_type: ElementType) -> List['SemanticElement']:
        """Get all children of a specific type."""
        return [child for child in self.children if child.element_type == element_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for serialization."""
        return {
            "name": self.name,
            "element_type": self.element_type.value,
            "position": {
                "start_line": self.position.start_line,
                "end_line": self.position.end_line,
                "start_column": self.position.start_column,
                "end_column": self.position.end_column,
                "start_byte": self.position.start_byte,
                "end_byte": self.position.end_byte,
            },
            "content": self.content,
            "signature": self.signature,
            "parent_name": self.parent_name,
            "access_modifiers": [mod.value for mod in self.access_modifiers],
            "return_type": self.return_type,
            "parameters": self.parameters,
            "generic_parameters": self.generic_parameters,
            "documentation": self.documentation,
            "decorators": self.decorators,
            "attributes": self.attributes,
            "language_specific": self.language_specific,
            "tree_sitter_node_type": self.tree_sitter_node_type,
            "tree_sitter_metadata": self.additional_metadata,
            "has_children": len(self.children) > 0,
            "children_count": len(self.children),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticElement':
        """Create SemanticElement from dictionary representation."""
        position = SemanticPosition(
            start_line=data["position"]["start_line"],
            end_line=data["position"]["end_line"],
            start_column=data["position"]["start_column"],
            end_column=data["position"]["end_column"],
            start_byte=data["position"]["start_byte"],
            end_byte=data["position"]["end_byte"],
        )
        
        return cls(
            name=data["name"],
            element_type=ElementType(data["element_type"]),
            position=position,
            content=data.get("content", ""),
            signature=data.get("signature"),
            parent_name=data.get("parent_name"),
            access_modifiers=[AccessModifier(mod) for mod in data.get("access_modifiers", [])],
            return_type=data.get("return_type"),
            parameters=data.get("parameters", []),
            generic_parameters=data.get("generic_parameters", []),
            documentation=data.get("documentation"),
            decorators=data.get("decorators", []),
            attributes=data.get("attributes", []),
            language_specific=data.get("language_specific", {}),
            tree_sitter_node_type=data.get("tree_sitter_node_type"),
            additional_metadata=data.get("tree_sitter_metadata", {}),
        )


@dataclass
class ParseResult:
    """Result of parsing a source code file with tree-sitter."""
    
    elements: List[SemanticElement]
    success: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Parser metadata
    parser_type: str = ""
    parse_time_ms: float = 0.0
    tree_objects: Optional[Any] = None  # The actual parsing tree object
    
    # Source information
    source_length: int = 0
    source_lines: int = 0
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
    
    @property
    def element_count(self) -> int:
        """Get total number of elements including nested ones."""
        count = len(self.elements)
        for element in self.elements:
            count += self._count_children(element)
        return count
    
    def _count_children(self, element: SemanticElement) -> int:
        """Recursively count children."""
        count = len(element.children)
        for child in element.children:
            count += self._count_children(child)
        return count
    
    def get_elements_by_type(self, element_type: ElementType) -> List[SemanticElement]:
        """Get all elements of a specific type (including nested)."""
        result = []
        for element in self.elements:
            if element.element_type == element_type:
                result.append(element)
            result.extend(self._get_children_by_type(element, element_type))
        return result
    
    def _get_children_by_type(self, element: SemanticElement, element_type: ElementType) -> List[SemanticElement]:
        """Recursively get children of a specific type."""
        result = []
        for child in element.children:
            if child.element_type == element_type:
                result.append(child)
            result.extend(self._get_children_by_type(child, element_type))
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "elements": [element.to_dict() for element in self.elements],
            "success": self.success,
            "errors": self.errors,
            "warnings": self.warnings,
            "parser_type": self.parser_type,
            "parse_time_ms": self.parse_time_ms,
            "source_length": self.source_length,
            "source_lines": self.source_lines,
            "element_count": self.element_count,
            "stats": {
                element_type.value: len(self.get_elements_by_type(element_type))
                for element_type in ElementType
                if len(self.get_elements_by_type(element_type)) > 0
            }
        }