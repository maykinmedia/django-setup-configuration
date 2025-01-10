from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import IntegrityError

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.contrib.sites.models import SitesConfigurationModel
from django_setup_configuration.exceptions import ConfigurationRunFailed


class SitesConfigurationStep(BaseConfigurationStep):
    """
    This step configures one or more ``django.contrib.sites.Site`` objects
    """

    config_model = SitesConfigurationModel
    verbose_name = "Sites configuration"

    namespace = "sites_config"
    enable_setting = "sites_config_enable"

    def execute(self, model: SitesConfigurationModel) -> None:
        if not model.items:
            raise ConfigurationRunFailed("Please specify one or more sites")

        first_site = model.items[0]

        # We need to ensure the current site is updated, to make sure that `get_current`
        # keeps working. The first site in the list is treated as the current site.
        current_site = None

        try:
            current_site = Site.objects.get_current()
        except (Site.DoesNotExist, ImproperlyConfigured):
            current_site = Site()

            # We have no current site, which means there is no site pointed to by
            # settings.SITE_ID -- however, `get_current()` expects a Site with that ID
            # to exist, so we have to make sure the created site receives that ID.
            current_site.pk = getattr(settings, "SITE_ID")

        try:
            current_site.domain = first_site.domain
            current_site.name = first_site.name
            current_site.full_clean(exclude=("id",), validate_unique=False)
            current_site.save()
        except ValidationError as exception:
            exception_message = (
                f"Validation error(s) occurred for "
                f"the current site {first_site.domain}."
            )
            raise ConfigurationRunFailed(exception_message) from exception
        except IntegrityError as exception:
            exception_message = (
                f"Failed updating the current site with domain {first_site.domain}."
            )
            raise ConfigurationRunFailed(exception_message) from exception

        for item in model.items[1:]:
            site_instance = Site(domain=item.domain, name=item.name)

            try:
                site_instance.full_clean(exclude=("id",), validate_unique=False)
            except ValidationError as exception:
                exception_message = (
                    f"Validation error(s) occured for site {item.domain}."
                )
                raise ConfigurationRunFailed(exception_message) from exception

            try:
                Site.objects.update_or_create(
                    domain=item.domain, defaults={"name": item.name}
                )
            except IntegrityError as exception:
                exception_message = f"Failed configuring site {item.domain}."
                raise ConfigurationRunFailed(exception_message) from exception
