from dataclasses import dataclass, field
from types import UnionType
from typing import Any, Dict, List, Union, get_args, get_origin
from pydantic import BaseModel, Field
from enum import Enum
from pydantic_core import PydanticUndefined
import yaml
from typing import Optional


@dataclass
class DocNode:
    key: str
    type: str
    value: Any = None
    description: Optional[str] = None
    examples: List[Any] = field(default_factory=list)
    default: Optional[Any] = None
    children: List["DocNode"] = field(default_factory=list)
    options: Dict[str, Optional[Union["DocNode", List["DocNode"]]]] = field(
        default_factory=dict
    )


class DocGraphBuilder:
    def __init__(self):
        self.processed_models = set()

    def _is_union(self, type_: Any) -> bool:
        """Check if a type is either a Union or UnionType."""
        origin = get_origin(type_)
        return origin in (Union, UnionType)

    def _get_example_value(self, field_type: type) -> Any:
        if field_type == str:
            return "a string"
        elif field_type == int:
            return 0
        elif field_type == float:
            return 0.0
        elif field_type == bool:
            return True
        elif get_origin(field_type) == list:
            return ["string1", "string2"]
        elif get_origin(field_type) == dict:
            return {"key": "value"}
        return None

    def _is_pydantic_model(self, type_: Any) -> bool:
        try:
            return isinstance(type_, type) and issubclass(type_, BaseModel)
        except TypeError:
            return False

    def _is_enum(self, type_: Any) -> bool:
        try:
            return isinstance(type_, type) and issubclass(type_, Enum)
        except TypeError:
            return False

    def _is_optional(self, type_: Any) -> bool:
        """Check if a type is Optional (Union with None)."""
        if self._is_union(type_):
            args = get_args(type_)
            return type(None) in args
        return False

    def _handle_union_type(
        self, field_name: str, field_type: Any, description: Optional[str]
    ) -> DocNode:
        """Handle a union type field."""
        types = get_args(field_type)
        options = {}

        node = DocNode(key=field_name, type="union", description=description)

        for t in types:
            if t is type(None):
                options["None"] = None
            elif self._is_pydantic_model(t):
                child_nodes = self._process_regular_model(t)
                options[t.__name__] = child_nodes
            else:
                value_node = DocNode(
                    key="value", type=str(t), value=self._get_example_value(t)
                )
                options[str(t)] = value_node

        node.options = options
        return node

    def _process_regular_model(self, model_class: type[BaseModel]) -> List[DocNode]:
        """Process a regular (non-union) model."""
        if model_class in self.processed_models:
            return [
                DocNode(
                    key="<recursive>",
                    type=f"recursive {model_class.__name__}",
                    value="<recursive reference>",
                )
            ]

        self.processed_models.add(model_class)
        nodes = []

        for field_name, field in model_class.model_fields.items():
            field_type = field.annotation

            if self._is_union(field_type):
                node = self._handle_union_type(
                    field_name, field_type, field.description
                )
            else:
                node = DocNode(
                    key=field_name,
                    type=str(field_type),
                    description=field.description,
                    default=(
                        field.default
                        if field.default is not PydanticUndefined
                        else None
                    ),
                )

                if self._is_pydantic_model(field_type):
                    node.type = field_type.__name__
                    node.children = self._process_regular_model(field_type)
                elif self._is_enum(field_type):
                    node.value = next(iter(field_type.__members__.values())).value
                    node.examples = [v.value for v in field_type.__members__.values()]
                else:
                    node.value = self._get_example_value(field_type)

            nodes.append(node)

        self.processed_models.remove(model_class)
        return nodes

    def build_graph(self, model_class: type[BaseModel]) -> List[DocNode]:
        """Build a documentation graph from a Pydantic model."""
        return self._process_regular_model(model_class)


class YamlGenerator:
    def __init__(self, indent: int = 2):
        self.indent = indent

    def _format_value(self, value: Any) -> str:
        """Format a value for YAML output."""
        if isinstance(value, str):
            if "\n" in value:
                return "|\n" + textwrap.indent(value, " " * self.indent)
            return f"'{value}'"
        return str(value)

    def _is_primitive_union(self, options: Dict) -> bool:
        """Check if a union consists only of primitive types and None."""
        return all(
            option_value is None
            or (not isinstance(option_value, list) and not option_value.children)
            for option_value in options.values()
        )

    def _is_list_type(self, type_str: str) -> bool:
        """Check if a type string represents a list."""
        return (
            type_str.startswith("List[")
            or type_str.startswith("list[")
            or "typing.List[" in type_str
        )

    def _get_list_inner_type(self, type_str: str) -> str:
        """Extract the inner type from a list type string."""
        if "typing.List[" in type_str:
            start = type_str.index("typing.List[") + len("typing.List[")
        elif type_str.startswith("List["):
            start = 5
        else:
            start = 5  # list[

        count = 1
        end = start
        while count > 0 and end < len(type_str):
            if type_str[end] == "[":
                count += 1
            elif type_str[end] == "]":
                count -= 1
            end += 1

        return type_str[start : end - 1]

    def _get_example_value(self, field_type: type) -> Any:
        """Generate example values for basic types."""
        if field_type == str:
            return "a string"
        elif field_type == int:
            return 0
        elif field_type == float:
            return 0.0
        elif field_type == bool:
            return True
        elif get_origin(field_type) == list:
            return None  # Lists are handled specially
        elif get_origin(field_type) == dict:
            return {"key": "value"}
        return None

    def _generate_union_banner(self, node: DocNode) -> List[str]:
        """Generate a banner comment for complex union types."""
        return [
            "# #####################",
            "# Union type with variants:",
            *[f"# - {variant}" for variant in node.options.keys()],
            "# #####################",
        ]

    def _generate_variant_banner(self, variant_name: str) -> List[str]:
        """Generate a banner for a complex variant."""
        return [
            "# -------------------",
            f"# Variant: {variant_name}",
            "# -------------------",
        ]

    def _get_field_comments(self, node: DocNode) -> List[str]:
        """Get comments for a field, to be placed above the field."""
        comments = []
        if node.description:
            comments.append(node.description)
        if node.default is not None:
            comments.append(f"Default: {node.default}")
        if node.examples:
            comments.append(f"Examples: {', '.join(map(str, node.examples))}")
        return comments

    def _write_field_comments(
        self, comments: List[str], indent_level: int = 0
    ) -> List[str]:
        """Write field comments above the field."""
        if not comments:
            return []
        indent = " " * (self.indent * indent_level)
        return [f"{indent}# {comment}" for comment in comments]

    def _generate_list_items(self, node: DocNode, indent_level: int) -> List[str]:
        """Generate YAML lines for list items."""
        lines = []
        indent = " " * (self.indent * indent_level)

        if node.type == "union":
            if self._is_primitive_union(node.options):
                # For primitive unions in lists, show one example with or: comment
                first_value = next(
                    (opt for opt in node.options.items() if opt[1] is not None), None
                )
                other_variants = (
                    [name for name in node.options.keys() if name != first_value[0]]
                    if first_value
                    else []
                )

                if first_value:
                    variant_name, variant_node = first_value
                    value = self._format_value(variant_node.value)
                    others = (
                        f"or: {', '.join(other_variants)}" if other_variants else ""
                    )
                    lines.append(f"{indent}- {value}  # {others}")
                else:
                    lines.append(f"{indent}- null")
            else:
                # For complex unions in lists, show one example of each variant
                for variant_name, variant_value in node.options.items():
                    if variant_value is None:
                        lines.append(f"{indent}- null  # Variant: {variant_name}")
                    elif isinstance(variant_value, list):
                        lines.append(f"{indent}# Variant: {variant_name}")
                        lines.append(f"{indent}-")
                        for child_node in variant_value:
                            lines.extend(
                                self._generate_yaml_lines(child_node, indent_level + 1)
                            )
                        lines.append("")  # Add space between variants
        else:
            # For regular complex types in lists, show one example
            if node.children:
                lines.append(f"{indent}# Example list item")
                lines.append(f"{indent}-")
                for child in node.children:
                    lines.extend(self._generate_yaml_lines(child, indent_level + 1))
            else:
                lines.append(
                    f"{indent}- {self._format_value(node.value)}  # Example list item"
                )

        return lines

    def _generate_yaml_lines(self, node: DocNode, indent_level: int = 0) -> List[str]:
        """Generate YAML lines for a node."""
        lines = []
        indent = " " * (self.indent * indent_level)

        # Handle list types
        if self._is_list_type(node.type):
            comments = self._get_field_comments(node)
            lines.extend(self._write_field_comments(comments, indent_level))
            lines.append(f"{indent}{node.key}:")
            inner_type = self._get_list_inner_type(node.type)
            inner_node = DocNode(
                key="item",
                type=inner_type,
                children=node.children,
                options=node.options,
            )
            lines.extend(self._generate_list_items(inner_node, indent_level))
            return lines

        # Handle union types
        if node.type == "union":
            if self._is_primitive_union(node.options):
                comments = self._get_field_comments(node)
                lines.extend(self._write_field_comments(comments, indent_level))

                first_value = next(
                    (opt for opt in node.options.items() if opt[1] is not None), None
                )
                other_variants = [
                    name
                    for name in node.options.keys()
                    if first_value and name != first_value[0]
                ]

                if first_value:
                    variant_name, variant_node = first_value
                    value = self._format_value(variant_node.value)
                    others = (
                        f"or: {', '.join(other_variants)}" if other_variants else ""
                    )
                    lines.append(f"{indent}{node.key}: {value}  # {others}")
                else:
                    lines.append(f"{indent}{node.key}: null")
            else:
                lines.extend(
                    [f"{indent}{line}" for line in self._generate_union_banner(node)]
                )
                comments = self._get_field_comments(node)
                lines.extend(self._write_field_comments(comments, indent_level))

                for variant_name, variant_value in node.options.items():
                    if variant_value is None:
                        lines.append(
                            f"{indent}{node.key}: null  # Variant: {variant_name}"
                        )
                    elif isinstance(variant_value, list):
                        lines.extend(
                            [
                                f"{indent}{line}"
                                for line in self._generate_variant_banner(variant_name)
                            ]
                        )
                        lines.append(f"{indent}{node.key}:")
                        for child_node in variant_value:
                            lines.extend(
                                self._generate_yaml_lines(child_node, indent_level + 1)
                            )
            return lines

        # For regular nodes
        comments = self._get_field_comments(node)
        lines.extend(self._write_field_comments(comments, indent_level))

        if node.children:
            lines.append(f"{indent}{node.key}:")
            for child in node.children:
                lines.extend(self._generate_yaml_lines(child, indent_level + 1))
        else:
            lines.append(f"{indent}{node.key}: {self._format_value(node.value)}")

        return lines

    def generate_yaml(self, nodes: List[DocNode]) -> str:
        """Generate YAML documentation from a list of DocNodes."""
        all_lines = []
        for node in nodes:
            all_lines.extend(self._generate_yaml_lines(node))
            all_lines.append("")  # Empty line between top-level nodes
        return "\n".join(all_lines)
