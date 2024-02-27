from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.db import transaction
from django.utils.module_loading import import_string

from ...configuration import BaseConfigurationStep
from ...exceptions import ConfigurationRunFailed, PrerequisiteFailed, SelfTestFailed


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
            "--overwrite",
            action="store_true",
            help=(
                "Overwrite the existing configuration. Should be used if some "
                "of the env variables have been changed."
            ),
        )
        parser.add_argument(
            "--no-selftest",
            action="store_true",
            dest="skip_selftest",
            help=(
                "Skip checking if configuration is successful. Use it if you "
                "run this command in the init container before the web app is started"
            ),
        )

    @transaction.atomic
    def handle(self, **options):
        overwrite: bool = options["overwrite"]
        skip_selftest: bool = options["skip_selftest"]

        errors = ErrorDict()
        steps: list[BaseConfigurationStep] = [
            import_string(path)() for path in settings.SETUP_CONFIGURATION_STEPS
        ]
        enabled_steps = [step for step in steps if step.is_enabled()]

        if not enabled_steps:
            self.stdout.write(
                "There are no enabled configuration steps. "
                "Configuration can't be set up"
            )
            return

        self.stdout.write(
            f"Configuration will be set up with following steps: {enabled_steps}"
        )

        # 1. Check prerequisites of all steps
        for step in enabled_steps:
            try:
                step.validate_requirements()
            except PrerequisiteFailed as exc:
                errors[step] = exc

        if errors:
            raise CommandError(
                f"Prerequisites for configuration are not fulfilled: {errors.as_text()}"
            )

        # 2. Configure steps
        configured_steps = []
        for step in enabled_steps:
            if not overwrite and step.is_configured():
                self.stdout.write(
                    f"Step {step} is skipped, because the configuration already exists."
                )
                continue
            else:
                self.stdout.write(f"Configuring {step}...")
                try:
                    step.configure()
                except ConfigurationRunFailed as exc:
                    raise CommandError(f"Could not configure step {step}") from exc
                else:
                    self.stdout.write(f"{step} is successfully configured")
                    configured_steps.append(step)

        # 3. Test configuration
        if skip_selftest:
            self.stdout.write("Selftest is skipped.")

        else:
            for step in configured_steps:
                try:
                    step.test_configuration()
                except SelfTestFailed as exc:
                    errors[step] = exc

            if errors:
                raise CommandError(
                    f"Configuration test failed with errors: {errors.as_text()}"
                )

        self.stdout.write(self.style.SUCCESS("Instance configuration completed."))
