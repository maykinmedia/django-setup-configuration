from collections.abc import Sequence
from typing import ClassVar

from django.contrib.sites.models import Site
from django.db.models import Model

from django_setup_configuration.models import ConfigurationModel


class SiteConfigurationModel(ConfigurationModel):
    class Meta:
        django_model_refs: ClassVar[dict[type[Model], Sequence[str]]] = {
            Site: (
                "domain",
                "name",
            )
        }


class SitesConfigurationModel(ConfigurationModel):
    items: list[SiteConfigurationModel]
