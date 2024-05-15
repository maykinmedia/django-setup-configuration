import pathlib

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template import loader
from django.utils.module_loading import import_string

from ...base import ConfigSettingsModel


class ConfigDocBase:
    """
    Base class encapsulating the functionality for generating + checking documentation.

    Defined independently of `BaseCommand` for more flexibility (the class could be
    used without running a Django management command).
    """

    def get_detailed_info(self, config: ConfigSettingsModel) -> list[list[str]]:
        ret = []
        for field in config.config_fields:
            part = []
            part.append(f"{'Variable':<20}{config.get_setting_name(field)}")
            part.append(f"{'Setting':<20}{field.verbose_name}")
            part.append(f"{'Description':<20}{field.description or 'No description'}")
            part.append(f"{'Possible values':<20}{field.field_description}")
            part.append(f"{'Default value':<20}{field.default_value}")
            ret.append(part)
        return ret

    def format_display_name(self, display_name: str) -> str:
        """Surround title with '=' to display as heading in rst file"""

        heading_bar = "=" * len(display_name)
        display_name_formatted = f"{heading_bar}\n{display_name}\n{heading_bar}"
        return display_name_formatted

    def render_doc(self, config_settings: ConfigSettingsModel, config_step) -> None:
        # 1.
        enable_setting = getattr(config_step, "enable_setting", None)

        # 2.
        required_settings = getattr(config_step, "required_settings", None)
        if required_settings:
            required_settings.sort()

        # 3.
        all_settings = [
            config_settings.get_setting_name(field)
            for field in config_settings.config_fields
        ]
        all_settings.sort()

        # 4.
        detailed_info = self.get_detailed_info(config_settings)
        detailed_info.sort()

        # 5.
        title = self.format_display_name(config_step.verbose_name)

        template_variables = {
            "enable_settings": enable_setting,
            "required_settings": required_settings,
            "all_settings": all_settings,
            "detailed_info": detailed_info,
            "link": f".. _{config_settings.file_name}:",
            "title": title,
        }

        template = loader.get_template(settings.DJANGO_SETUP_CONFIG_TEMPLATE)
        rendered = template.render(template_variables)

        return rendered


class Command(ConfigDocBase, BaseCommand):
    help = "Generate documentation for configuration setup steps"

    def content_is_up_to_date(self, rendered_content: str, doc_path: str) -> bool:
        """
        Check that documentation at `doc_path` exists and that its content matches
        that of `rendered_content`
        """
        try:
            with open(doc_path, "r") as file:
                file_content = file.read()
        except FileNotFoundError:
            return False

        if not file_content == rendered_content:
            return False

        return True

    def handle(self, *args, **kwargs) -> str:
        target_dir = settings.DJANGO_SETUP_CONFIG_DOC_PATH

        # create directory for docs if it doesn't exist
        pathlib.Path(target_dir).mkdir(parents=True, exist_ok=True)

        for config_string in settings.SETUP_CONFIGURATION_STEPS:
            config_step = import_string(config_string)

            if config_settings := getattr(config_step, "config_settings", None):
                doc_path = f"{target_dir}/{config_settings.file_name}.rst"
                rendered_content = self.render_doc(config_settings, config_step)

                if not self.content_is_up_to_date(rendered_content, doc_path):
                    with open(doc_path, "w+") as output:
                        output.write(rendered_content)
