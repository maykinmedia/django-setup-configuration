from django.contrib.postgres.fields import ArrayField
from django.db import models


class Service(models.Model):
    url = models.URLField(
        verbose_name="Service url",
        help_text="The url of the service",
    )
    bogus = models.CharField(
        verbose_name="Bogus service field", help_text="Should not be included in docs"
    )


class ProductConfig(models.Model):
    name = models.CharField(
        verbose_name="Name",
        help_text="The name of the product",
    )
    service = models.OneToOneField(
        to=Service,
        verbose_name="Service",
        default=None,
        on_delete=models.SET_NULL,
        help_text="API service of the product",
    )
    tags = ArrayField(
        base_field=models.CharField("Product tag"),
        default=["example_tag"],
        help_text="Tags for the product",
    )
    bogus = models.CharField(
        help_text="Should be excluded",
    )
