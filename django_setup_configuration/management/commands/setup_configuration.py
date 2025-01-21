import functools
import textwrap
from pathlib import Path

from django.core.management import BaseCommand, CommandError

from django_setup_configuration.exceptions import ValidateRequirementsFailure
from django_setup_configuration.runner import SetupConfigurationRunner

indent = functools.partial(textwrap.indent, prefix=" " * 4)


class Command(BaseCommand):
    help = (
        "Bootstrap the initial configuration of the application. "
        "This command is run only in non-interactive mode with settings "
        "configured mainly via environment variables. "
        "This command is declarative - each step is idempotent, so it's safe to run "
        "the command multiple times. The steps will overwrite any manual changes made "
        "in the admin if you run the command after making these changes. "
    )
    output_transaction = True

    def add_arguments(self, parser):
        parser.add_argument(
            "--yaml-file",
            type=str,
            required=True,
            help="Path to YAML file containing the configurations",
        )
        parser.add_argument(
            "--validate-only",
            action="store_true",
            default=False,
            help="Validate that all the step configurations can be successfully loaded "
            "from source, without actually executing the steps.",
        )

    def handle(self, **options):
        validate_only = options["validate_only"]
        yaml_file = Path(options["yaml_file"]).resolve()
        if not yaml_file.exists():
            raise CommandError(f"Yaml file `{yaml_file}` does not exist.")

        self.stdout.write(f"Loading config settings from {yaml_file}")

        try:
            runner = SetupConfigurationRunner(yaml_source=options["yaml_file"])
        except Exception as exc:
            raise CommandError(str(exc))

        if not runner.configured_steps:
            raise CommandError("No steps configured, aborting.")

        self.stdout.write("The following steps are configured:")
        for step in runner.configured_steps:
            step_is_enabled = step in runner.enabled_steps
            self.stdout.write(
                indent(
                    f"{step.verbose_name} from {step.__class__}"
                    f" [{'enabled' if step_is_enabled else '***disabled***'}]"
                ),
            )

        if not runner.enabled_steps:
            raise CommandError("No steps enabled, aborting.")

        if disabled_steps := runner.disabled_steps:
            self.stdout.write(
                "The following steps will be skipped because they are disabled:",
                self.style.WARNING,
            )
            for step in disabled_steps:
                self.stdout.write(
                    indent(
                        f"{step.verbose_name} from {step.__class__}"
                        f" [{step.enable_setting} = false]"
                    ),
                    self.style.WARNING,
                )

        # 1. Check prerequisites of all steps
        steps_with_invalid_requirements = []
        self.stdout.write()
        self.stdout.write("Validating requirements...")
        try:
            runner.validate_all_requirements()
        except ValidateRequirementsFailure as exc_group:
            for exc in exc_group.exceptions:
                self.stderr.write(
                    self.style.ERROR(
                        f"Invalid configuration settings for step"
                        f' "{exc.step.verbose_name}":'
                    )
                )
                # Print an indented version of the validation error
                self.stderr.write(indent(str(exc.validation_error)), self.style.ERROR)
                self.stderr.write()
                steps_with_invalid_requirements.append(exc.step)

            raise CommandError(
                f"Failed to validate requirements for {len(exc_group.exceptions)}"
                " steps"
            )

        self.stdout.write(
            "Valid configuration settings found for all steps.", self.style.SUCCESS
        )

        # Bail out early if we're only validating
        if validate_only:
            return

        # 2. Execute steps
        self.stdout.write()
        self.stdout.write("Executing steps...")
        for result in runner.execute_all_iter():
            if exc := result.run_exception:
                self.stderr.write(
                    f"Error while executing step `{result.step}`", self.style.ERROR
                )
                self.stderr.write(indent(str(exc)))

                raise CommandError(
                    "Aborting run due to a failed step. All database changes have been"
                    " rolled back."
                ) from exc
            else:
                self.stdout.write(
                    indent(f"Successfully executed step: {result.step}"),
                    self.style.SUCCESS,
                )

        # Done
        self.stdout.write("")
        self.stdout.write("Configuration completed.", self.style.SUCCESS)
