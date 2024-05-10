from django.conf import settings

from ...exceptions import DocumentationCheckFailed
from .generate_config_docs import ConfigDocBaseCommand


class Command(ConfigDocBaseCommand):
    help = "Check that changes to configuration setup classes are reflected in the docs"

    def check_doc(self, config_option: str) -> None:
        SOURCE_DIR = settings.DJANGO_SETUP_CONFIG_DOC_DIR

        source_path = f"{SOURCE_DIR}/{config_option}.rst"

        try:
            with open(source_path, "r") as file:
                file_content = file.read()
        except FileNotFoundError as exc:
            msg = (
                "\nNo documentation was found for {config}\n"
                "Did you forget to run generate_config_docs?\n".format(
                    config=self.get_config(config_option, class_name_only=True)
                )
            )
            raise DocumentationCheckFailed(msg) from exc
        else:
            rendered_content = self.render_doc(config_option)

            if rendered_content != file_content:
                raise DocumentationCheckFailed(
                    "Class {config} has changes which are not reflected in the "
                    "documentation ({source_path})."
                    "Did you forget to run generate_config_docs?\n".format(
                        config=self.get_config(config_option, class_name_only=True),
                        source_path=f"{SOURCE_DIR}/{config_option}.rst",
                    )
                )

    def handle(self, *args, **kwargs) -> None:
        supported_options = self.registry.config_model_keys

        for option in supported_options:
            self.check_doc(option)
