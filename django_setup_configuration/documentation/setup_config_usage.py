from importlib.metadata import version
from pathlib import Path

from django.template import Template
from django.template.context import Context
from django.utils.module_loading import import_string

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from pydantic.dataclasses import dataclass

from django_setup_configuration.configuration import BaseConfigurationStep

_TEMPLATES_PATH = Path(__file__).parent / "templates"


def _parse_bool(argument):
    value = directives.choice(argument, ("true", "false", "yes", "no", "1", "0"))
    return value in ("true", "yes", "1")


@dataclass(frozen=True)
class StepInfo:
    title: str
    description: str
    anchor_id: str
    module_path: str
    step_cls: type[BaseConfigurationStep]


class SetupConfigUsageDirective(Directive):
    has_content = True

    option_spec = {
        "show_command_usage": _parse_bool,
        "show_steps": _parse_bool,
        "show_steps_toc": _parse_bool,
        "show_steps_autodoc": _parse_bool,
    }

    def run(self):
        show_command_usage = self.options.get("show_command_usage", True)
        show_steps = self.options.get("show_steps", True)
        show_steps_toc = self.options.get("show_steps_toc", True)
        show_steps_autodoc = self.options.get("show_steps_autodoc", True)

        if not (settings := self._get_django_settings()):
            raise ValueError(
                "Unable to load Django settings. Is DJANGO_SETTINGS_MODULE set?"
            )

        if not (configured_steps := settings.get("SETUP_CONFIGURATION_STEPS")):
            raise ValueError(
                "No steps configured. Set SETUP_CONFIGURATION_STEPS via your "
                "Django settings."
            )

        usage_template = self._load_usage_template()
        steps = self._load_steps(configured_steps)

        rst = ViewList()
        rst.append("", "<dynamic>")
        usage_rst = usage_template.render(
            context=Context(
                {
                    "steps": steps,
                    "show_toc": show_steps_toc,
                    "show_steps": show_steps,
                    "package_version": version("django_setup_configuration"),
                }
            )
        )
        lines = usage_rst.split("\n")
        for line in lines:
            rst.append(line, "<dynamic>")

        usage_node: nodes.section | None = None
        if show_command_usage:
            usage_node = nodes.section()
            usage_node["ids"] = ["django-setup-config"]
            usage_node += nodes.title(
                text="Using the setup_configuration management command"
            )
            self.state.nested_parse(rst, 0, usage_node)

        step_sections: list[nodes.section] = []
        if show_steps:
            for step in steps:
                step_node = nodes.section(ids=[step.module_path])
                step_node += nodes.title(text=step.title)

                rst = ViewList()
                rst.append(f".. _{step.anchor_id}:", "<dynamic>")
                if show_steps_autodoc:
                    rst.append(f".. autoclass:: {step.module_path}", "<dynamic>")
                    rst.append("    :noindex:", "<dynamic>")
                else:
                    # Explicitly display the docstring if there's no autodoc to serve
                    # as the step description.
                    for line in step.description.splitlines():
                        rst.append(line, "<dynamic>")

                rst.append(f".. setup-config-example:: {step.module_path}", "<dynamic>")

                self.state.nested_parse(rst, 0, step_node)
                step_sections.append(step_node)

        return [node for node in (usage_node, *step_sections) if node]

    @classmethod
    def _get_django_settings(cls):
        from django.conf import settings
        from django.core.exceptions import AppRegistryNotReady, ImproperlyConfigured

        try:
            return settings._wrapped.__dict__ if hasattr(settings, "_wrapped") else {}
        except (AppRegistryNotReady, AttributeError, ImproperlyConfigured):
            return {}

    def _load_usage_template(self):
        return Template((_TEMPLATES_PATH / "config_doc.rst").read_text())

    def _load_steps(self, configured_steps) -> list[StepInfo]:  # -> list:
        steps_info: list[StepInfo] = []
        for step_path in configured_steps:
            step_cls = import_string(step_path)
            step_info = StepInfo(
                title=step_cls.verbose_name,
                anchor_id=f"ref_step_{step_path}",
                module_path=step_path,
                step_cls=step_cls,
                description=step_cls.__doc__ or "",
            )
            steps_info.append(step_info)
        return steps_info


def setup(app):
    app.add_directive("setup-config-usage", SetupConfigUsageDirective)
