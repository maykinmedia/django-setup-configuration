import importlib
import io
import textwrap
from dataclasses import dataclass
from enum import Enum
from types import NoneType, UnionType
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Literal,
    Type,
    Union,
    get_args,
    get_origin,
)

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
    commented_out_examples: List[Any]


def get_default_from_field_info(field_info: FieldInfo) -> Any:
    """
    Retrieves the default value from a FieldInfo object if available.

    :param field_info: The FieldInfo object.
    :return: The default value or None if not defined.
    """
    if field_info.default not in {PydanticUndefined, None}:
        return (
            field_info.default.value
            if isinstance(field_info.default, Enum)
            else field_info.default
        )
    if field_info.default_factory:
        return field_info.default_factory()
    return None


def yaml_set_wrapped_comment(
    commented_map: CommentedMap,
    key: str,
    comment: str,
    max_line_length: int,
    indent: int,
    before: bool = True,
):
    """
    Adds a wrapped comment to a specified key in the CommentedMap.

    :param commented_map: The CommentedMap object.
    :param key: The key to which the comment is added.
    :param comment: The comment text.
    :param max_line_length: Maximum line length for wrapping.
    :param indent: Indentation level.
    :param before: Whether to place the comment before the key.
    """
    wrapped_comment = textwrap.fill(comment, width=max_line_length)
    kwargs = {"before": wrapped_comment} if before else {"after": wrapped_comment}
    commented_map.yaml_set_comment_before_after_key(key, indent=indent, **kwargs)


def insert_example_with_comments(
    example_data: CommentedMap,
    field_name: str,
    field_info: FieldInfo,
    example: Any,
    depth: int,
):
    """
    Inserts an example value into the CommentedMap with appropriate comments.

    :param example_data: The CommentedMap to update.
    :param field_name: The name of the field.
    :param field_info: The FieldInfo object containing metadata.
    :param example: The example value to insert.
    :param depth: Current depth for indentation.
    """
    example_data[field_name] = example
    example_data.yaml_set_comment_before_after_key(field_name, before="\n")

    if field_info.description:
        yaml_set_wrapped_comment(
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
        yaml_set_wrapped_comment(
            example_data,
            field_name,
            f"POSSIBLE VALUES: {get_args(field_info.annotation)}",
            80,
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
    """
    Inserts an example value as a comment, this is used to display possible values
    for polymorphic types

    :param example_data: The CommentedMap to update.
    :param field_name: The name of the field.
    :param example: The example value to insert.
    :param depth: Current depth for indentation.
    :param before: Whether to place the comment before or after the key.
    """
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
        field_name, indent=depth * 2, **kwargs
    )


def generate_model_example(model: Type[BaseModel], depth: int = 0) -> Dict[str, Any]:
    """
    Generates example data for a Pydantic model.

    :param model: The Pydantic model class.
    :param depth: Current depth for indentation.
    :return: A dictionary representing the example data.
    """
    example_data = CommentedMap()

    for field_name, field_info in model.model_fields.items():
        example_value = process_field_type(
            field_info.annotation, field_info, field_name, depth + 1
        )

        if isinstance(example_value, PolymorphicExample):
            insert_example_with_comments(
                example_data, field_name, field_info, example_value.example, depth
            )

            yaml_set_wrapped_comment(
                example_data,
                field_name,
                (
                    "This value is polymorphic, the possible values are divided by "
                    "dashes and only one of them can be commented out."
                ),
                70,
                indent=depth * 2,
            )

            for i, commented_example in enumerate(example_value.commented_out_examples):
                example_data.yaml_set_comment_before_after_key(
                    field_name,
                    before=f"-------------OPTION {i + 1}-------------",
                    indent=depth * 2,
                )
                insert_as_full_comment(
                    example_data, field_name, commented_example, depth, before=True
                )

            example_data.yaml_set_comment_before_after_key(
                field_name,
                before=(
                    f"-------------OPTION "
                    f"{len(example_value.commented_out_examples) + 1}-------------"
                ),
                indent=depth * 2,
            )
        else:
            insert_example_with_comments(
                example_data, field_name, field_info, example_value, depth
            )

    return example_data


def process_field_type(
    field_type: Any, field_info: FieldInfo, field_name: str, depth: int
) -> Any:
    """
    Processes a field type and generates example data accordingly.

    :param field_type: The type of the field.
    :param field_info: The FieldInfo object containing metadata.
    :param field_name: The name of the field.
    :param depth: Current depth for recursion.
    :return: Generated example data or a PolymorphicExample.
    """
    if example := generate_basic_example(field_type, field_info):
        return example

    if get_origin(field_type) == Annotated:
        return process_field_type(
            get_args(field_type)[0], field_info, field_name, depth
        )

    if get_origin(field_type) in (Union, UnionType):
        union_types = get_args(field_type)
        primary_type, *other_types = union_types

        data = process_field_type(primary_type, field_info, field_name, depth)
        if other_types == [NoneType]:
            return data

        commented_out_examples = [
            process_field_type(t, field_info, field_name, 0) for t in other_types
        ]
        return PolymorphicExample(
            example=data, commented_out_examples=commented_out_examples
        )

    if get_origin(field_type) == list:
        return [
            process_field_type(
                get_args(field_type)[0], field_info, field_name, depth + 1
            )
        ]

    if isinstance(field_type, type) and issubclass(field_type, BaseModel):
        return generate_model_example(field_type, depth)

    return None


def generate_basic_example(field_type: Any, field_info: FieldInfo) -> Any:
    """
    Generates a basic example for primitive types.

    :param field_type: The type of the field.
    :param field_info: The FieldInfo object.
    :return: A basic example value.
    """
    if field_info.examples:
        return field_info.examples[0]
    if default := get_default_from_field_info(field_info):
        return default

    example_map = {
        str: "example_string",
        int: 123,
        bool: True,
        float: 123.45,
        list: [],
        dict: {},
    }
    return example_map.get(field_type, None)


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
