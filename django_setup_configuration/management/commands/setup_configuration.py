from pathlib import Path

from django.core.management import BaseCommand, CommandError
from django.db import transaction

from django_setup_configuration.exceptions import ValidateRequirementsFailure
from django_setup_configuration.runner import SetupConfigurationRunner


class ErrorDict(dict):
    """
    small helper to display errors
    """

    def as_text(self) -> str:
        output = [f"{k}: {v}" for k, v in self.items()]
        return "\n".join(output)


class Command(BaseCommand):
    help = (
        "Bootstrap the initial configuration of the application. "
        "This command is run only in non-interactive mode with settings "
        "configured mainly via environment variables."
    )
    output_transaction = True

    def add_arguments(self, parser):
        parser.add_argument(
            "--yaml-file",
            type=str,
            required=True,
            help="Path to YAML file containing the configurations",
        )

    @transaction.atomic
    def handle(self, **options):
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

        self.stdout.write(
            "The following steps are configured:\n%s"
            % "\n".join(str(step) for step in runner.configured_steps),
        )

        if not runner.enabled_steps:
            raise CommandError("No steps enabled, aborting.")

        errors = ErrorDict()
        # 1. Check prerequisites of all steps
        try:
            runner.validate_all_requirements()
        except ValidateRequirementsFailure as exc_group:
            for exc in exc_group.exceptions:
                self.stderr.write(
                    f"Unable to satisfy prerequisites for step:"
                    f" {exc.step.verbose_name}:"
                )
                errors[exc.step] = str(exc)

        if errors:
            raise CommandError(
                f"Prerequisites for configuration are not fulfilled: {errors.as_text()}"
            )

        self.stdout.write("Executing steps...")

        # 2. Configure steps
        for result in runner.execute_all_iter():
            if not result.is_enabled:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Skipping step '{result.step}' because it is not enabled"
                    )
                )
                continue

            if exc := result.run_exception:
                raise CommandError(
                    f"Error while executing step `{result.step}`: {str(exc)}"
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully executed step: {result.step}")
                )

        self.stdout.write(self.style.SUCCESS("Instance configuration completed."))
