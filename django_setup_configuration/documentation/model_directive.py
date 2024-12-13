import yaml
import importlib
from docutils import nodes
from docutils.parsers.rst import Directive
from pydantic import BaseModel
from typing import Type
from django_setup_configuration.fields import DjangoModelRefInfo
from sphinx.directives.code import CodeBlock


def generate_model_example(model: Type[BaseModel]) -> dict:
    example_data = {}

    # Loop through the annotations of the model to create example data
    for field_name, field_type in model.__annotations__.items():
        if isinstance(field_type, DjangoModelRefInfo):
            # For DjangoModelRef, provide a mock string (model reference)
            example_data[field_name] = "mock_django_model_reference"

        elif isinstance(field_type, type) and isinstance(field_type, BaseModel):
            # For nested Pydantic models, create an example using that model
            example_data[field_name] = generate_model_example(field_type)

        elif hasattr(field_type, "__origin__") and field_type.__origin__ == list:
            # For lists of models or other types, create an example with a list
            list_type = field_type.__args__[0]  # This is the type inside the list
            if isinstance(list_type, type) and issubclass(list_type, BaseModel):
                # If the list contains a Pydantic model, generate one example item
                example_data[field_name] = [generate_model_example(list_type)]
            else:
                # Otherwise, just provide a list with a basic example type
                example_data[field_name] = [list_type() if list_type else None]

        else:
            # For simple types (int, str, bool, etc.), generate a basic value
            if field_type == str:
                example_data[field_name] = "example_string"
            elif field_type == int:
                example_data[field_name] = 123
            elif field_type == bool:
                example_data[field_name] = True
            elif field_type == float:
                example_data[field_name] = 123.45
            else:
                example_data[field_name] = None  # Placeholder for unsupported types

    return example_data


# Custom directive for generating a YAML example from a Pydantic model
class PydanticModelExampleDirective(Directive):
    has_content = False
    required_arguments = 1  # Accept the full import path of the step class as an argument

    def run(self):
        step_class_path = self.arguments[0]

        # Dynamically import the step class
        try:
            # Split the step class path into module and class name
            module_name, class_name = step_class_path.rsplit('.', 1)

            # Import the module and get the step class
            module = importlib.import_module(module_name)
            step_class = getattr(module, class_name)

            # Ensure the class has the config_model attribute
            if not hasattr(step_class, 'config_model'):
                raise ValueError(f"The step class '{step_class}' does not have a 'config_model' attribute.")

            config_model = step_class.config_model

            # Ensure the config_model is a Pydantic model
            if not issubclass(config_model, BaseModel):
                raise ValueError(f"The config_model '{config_model}' is not a valid Pydantic model.")

        except (ValueError, AttributeError, ImportError) as e:
            raise ValueError(f"Step class '{step_class_path}' could not be found or is invalid.") from e

        # Derive the `namespace` and `enable_setting` from the step class
        namespace = getattr(step_class, 'namespace', None)
        enable_setting = getattr(step_class, 'enable_setting', None)

        # Generate the model example data
        example_data = generate_model_example(config_model)

        data = {}
        if enable_setting:
            data[enable_setting] = True
        if namespace:
            data[namespace] = example_data

        # Convert the example data to YAML format using safe_dump to ensure proper formatting
        yaml_example = yaml.safe_dump(data, default_flow_style=False)

        # Create a code block with YAML formatting
        literal_block = nodes.literal_block(yaml_example, yaml_example)
        literal_block['language'] = 'yaml'

        # Return the node to be inserted into the document
        return [literal_block]

def setup(app):
    app.add_directive('pydantic-model-example', PydanticModelExampleDirective)
