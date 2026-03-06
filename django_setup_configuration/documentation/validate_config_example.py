import importlib

import ruamel.yaml
from docutils import nodes
from docutils.parsers.rst import Directive
from pydantic import BaseModel

from django_setup_configuration.configuration import BaseConfigurationStep


class ValidateConfigExampleDirective(Directive):
    """
    Directive to validate and display a YAML configuration for a given ConfigurationStep

    Can be used to provide validated examples for specific configuration setups
    """

    # The content of the directive will be interpreted as the YAML example to validate
    has_content = True
    # Accept the full import path of the step class as an argument
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

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
            if not issubclass(step_class, BaseConfigurationStep):
                raise ValueError(
                    f"The step class '{step_class}' does not "
                    "inherit from BaseConfigurationStep."
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

        if not self.content:
            error = self.state_machine.reporter.error(
                "No YAML content provided to validate", line=self.lineno
            )
            return [error]

        yaml_example = "\n".join(self.content)

        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)

        literal_block = nodes.literal_block(yaml_example, yaml_example)
        literal_block["language"] = "yaml"

        # Validate that the model can parse the example YAML
        model_class = step_class.config_model
        data = yaml.load(yaml_example)
        model_class.model_validate(data[step_class.namespace])

        # Return the node to be inserted into the document
        return [literal_block]


def setup(app):
    app.add_directive("validate-config-example", ValidateConfigExampleDirective)
