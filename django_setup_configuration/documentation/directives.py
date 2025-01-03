import importlib

import yaml
from docutils import nodes
from docutils.parsers.rst import Directive


class InjectValidatedExample(Directive):
    """
    Directive to inject and validate an example from a model class,
    then display it as a YAML code block.
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    def run(self):
        full_path = self.arguments[0]

        # Split the full path into module and class parts
        *module_parts, class_name = full_path.split(".")
        module_name = ".".join(module_parts)

        # Dynamically import the module
        module = importlib.import_module(module_name)
        step_class = getattr(module, class_name)

        # Validate the example using the model
        model_class = step_class.config_model
        data = yaml.safe_load(step_class.example)
        model_class.parse_obj(data[step_class.namespace])

        # Convert validated data to YAML
        # yaml_output = yaml.dump(step_class.example, default_flow_style=False)

        # Create a literal block with YAML output
        literal = nodes.literal_block(step_class.example, step_class.example)
        literal["language"] = "yaml"

        return [literal]
