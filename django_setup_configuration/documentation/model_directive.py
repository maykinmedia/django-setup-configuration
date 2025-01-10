import importlib
import io
import textwrap
from dataclasses import dataclass
from enum import Enum
from types import NoneType, UnionType
from typing import Annotated, Any, Dict, Literal, Type, Union, get_args, get_origin

import ruamel.yaml
from docutils import nodes
from docutils.parsers.rst import Directive
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined
from ruamel.yaml.comments import CommentedMap


@dataclass
class PolymorphicExample:
    example: Any
    commented_out_examples: list[Any]


def get_default_from_field_info(field_info: FieldInfo) -> Any:
    if field_info.default != PydanticUndefined and field_info.default:
        if isinstance(field_info.default, Enum):
            return field_info.default.value
        return field_info.default
    elif field_info.default_factory and (default := field_info.default_factory()):
        return default


def yaml_set_comment_with_max_length(
    commented_map: CommentedMap,
    key: str,
    comment: str,
    max_line_length: int,
    indent: int,
    before: bool = True,
):
    """
    Adds a comment to the specified key in the commented map, wrapping it to fit within
    the max_line_length.

    :param commented_map: The CommentedMap object.
    :param key: The key where the comment should be placed.
    :param comment: The comment string to be added.
    :param max_line_length: The maximum allowed line length for the comment.
    :param before: Whether to place the comment before or after the key.
        Defaults to `True` (before).
    """
    # Split the comment into lines with the specified max line length
    wrapped_comment = textwrap.fill(comment, width=max_line_length)

    # If before is True, add the comment before the key
    if before:
        commented_map.yaml_set_comment_before_after_key(
            key, before=wrapped_comment, after=None, indent=indent
        )
    else:
        # Otherwise, add it after the key
        commented_map.yaml_set_comment_before_after_key(
            key, before=None, after=wrapped_comment, indent=indent
        )


def insert_example_with_comments(
    example_data: CommentedMap,
    field_name: str,
    field_info: FieldInfo,
    example: Any,
    depth: int,
):
    example_data[field_name] = example
    # TODO adding a newline after keys is difficult apparently
    example_data.yaml_set_comment_before_after_key(field_name, before="\n")
    if field_info.description:
        yaml_set_comment_with_max_length(
            example_data,
            field_name,
            f"DESCRIPTION: {field_info.description}",
            80,
            indent=depth * 2,
        )

    if default := get_default_from_field_info(field_info):
        example_data.yaml_set_comment_before_after_key(
            field_name, f"DEFAULT VALUE: {default}", indent=depth * 2
        )

    if get_origin(field_info.annotation) == Literal:
        example_data.yaml_set_comment_before_after_key(
            field_name,
            f"POSSIBLE VALUES: {get_args(field_info.annotation)}",
            indent=depth * 2,
        )

    example_data.yaml_set_comment_before_after_key(
        field_name, f"REQUIRED: {field_info.is_required()}", indent=depth * 2
    )


def insert_as_full_comment(
    example_data: CommentedMap,
    field_name: str,
    example: Any,
    depth: int,
    before: bool = False,
):
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    output = io.StringIO()
    yaml.dump(example, output)
    yaml_example = output.getvalue()

    # Remove newlines and dots, dumping simple values will add an ellipsis
    # TODO is there another way to prevent this?
    if yaml_example.endswith("...\n"):
        yaml_example = yaml_example.rstrip("\n.")
        yaml_example = f"{field_name}: {yaml_example}\n"
    else:
        # Ensure indentation is correct for complex examples
        yaml_example = "\n".join(
            ["  " + line for line in yaml_example.splitlines()]
        ).lstrip(" ")
        yaml_example = f"{field_name}:{yaml_example}\n"

    kwargs = {"before": yaml_example} if before else {"after": yaml_example}
    example_data.yaml_set_comment_before_after_key(
        field_name,
        indent=depth * 2,
        **kwargs,
    )


def generate_model_example(model: Type[BaseModel], depth: int = 0) -> Dict[str, Any]:
    example_data = CommentedMap()

    # Loop through the annotations of the model to create example data
    for field_name, field_info in model.model_fields.items():
        _data = process_field_type(
            field_info.annotation, field_info, field_name, depth + 1
        )
        if isinstance(_data, PolymorphicExample):
            insert_example_with_comments(
                example_data, field_name, field_info, _data.example, depth
            )

            yaml_set_comment_with_max_length(
                example_data,
                field_name,
                (
                    "This value is polymorphic, the possible values are divided by "
                    "dashes and only one of them can be commented out.\n"
                ),
                70,
                indent=depth * 2,
            )
            for i, commented_example in enumerate(_data.commented_out_examples):
                example_data.yaml_set_comment_before_after_key(
                    field_name,
                    before=(f"-------------OPTION {i+1}-------------"),
                    indent=depth * 2,
                )
                insert_as_full_comment(
                    example_data, field_name, commented_example, depth, before=True
                )
            example_data.yaml_set_comment_before_after_key(
                field_name,
                before=(f"-------------OPTION {i+2}-------------"),
                indent=depth * 2,
            )
        else:
            insert_example_with_comments(
                example_data, field_name, field_info, _data, depth
            )

    return example_data


def process_field_type(
    field_type: Any, field_info: FieldInfo, field_name: str, depth: int
) -> Any:
    """
    Processes a field type and generates example data based on its type.
    """
    # Handle basic types
    if example := generate_basic_example(field_type, field_info):
        return example

    # Step 1: Handle Annotated
    if get_origin(field_type) == Annotated:
        annotated_type = get_args(field_type)[0]

        # Process the unwrapped type
        return process_field_type(annotated_type, field_info, field_name, depth)

    # Handle Union and "... | ..."
    if get_origin(field_type) in (Union, UnionType):
        union_types = get_args(field_type)

        # Generate example for the first type in the Union
        primary_type = union_types[0]
        data = process_field_type(primary_type, field_info, field_name, depth)
        if union_types[1:] == (NoneType,):
            return data

        other = [
            process_field_type(type, field_info, field_name, 0)
            for type in union_types[1:]
        ]
        return PolymorphicExample(example=data, commented_out_examples=other)

    # Handle lists
    if get_origin(field_type) == list:
        list_type = get_args(field_type)[0]
        return [process_field_type(list_type, field_info, field_name, depth + 1)]

    # Handle Pydantic models
    if isinstance(field_type, type) and issubclass(field_type, BaseModel):
        return generate_model_example(field_type, depth=depth)


def generate_basic_example(field_type: Any, field_info: FieldInfo) -> Any:
    """
    Generates a basic example for simple types like str, int, bool, etc.
    """
    if field_info.examples:
        return field_info.examples[0]
    elif default := get_default_from_field_info(field_info):
        return default
    elif field_type == str:
        return "example_string"
    elif field_type == int:
        return 123
    elif field_type == bool:
        return True
    elif field_type == float:
        return 123.45
    elif field_type == list:
        return []
    elif field_type == dict:
        return {}
    else:
        return None  # Placeholder for unsupported types


# Custom directive for generating a YAML example from a Pydantic model
class PydanticModelExampleDirective(Directive):
    has_content = False
    required_arguments = (
        1  # Accept the full import path of the step class as an argument
    )

    def run(self):
        step_class_path = self.arguments[0]

        # Dynamically import the step class
        try:
            # Split the step class path into module and class name
            module_name, class_name = step_class_path.rsplit(".", 1)

            # Import the module and get the step class
            module = importlib.import_module(module_name)
            step_class = getattr(module, class_name)

            # Ensure the class has the config_model attribute
            if not hasattr(step_class, "config_model"):
                raise ValueError(
                    f"The step class '{step_class}' does not "
                    "have a 'config_model' attribute."
                )

            config_model = step_class.config_model

            # Ensure the config_model is a Pydantic model
            if not issubclass(config_model, BaseModel):
                raise ValueError(
                    f"The config_model '{config_model}' is not a valid Pydantic model."
                )

        except (ValueError, AttributeError, ImportError) as e:
            raise ValueError(
                f"Step class '{step_class_path}' could not be found or is invalid."
            ) from e

        # Derive the `namespace` and `enable_setting` from the step class
        namespace = getattr(step_class, "namespace", None)
        enable_setting = getattr(step_class, "enable_setting", None)

        # Generate the model example data
        example_data = generate_model_example(config_model, depth=1)

        data = {}
        if enable_setting:
            data[enable_setting] = True
        if namespace:
            data[namespace] = example_data

        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)

        output = io.StringIO()
        yaml.dump(data, output)
        yaml_example = output.getvalue()

        # Create a code block with YAML formatting
        literal_block = nodes.literal_block(yaml_example, yaml_example)
        literal_block["language"] = "yaml"

        # Validate that the model can parse the example YAML
        model_class = step_class.config_model
        data = yaml.load(yaml_example)
        model_class.model_validate(data[step_class.namespace])

        # Return the node to be inserted into the document
        return [literal_block]


def setup(app):
    app.add_directive("pydantic-model-example", PydanticModelExampleDirective)
