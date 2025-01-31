from uuid import UUID

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _


class StrChoices(models.TextChoices):
    foo = "foo", "Foo"
    bar = "bar", "Bar"


class DjangoModel(models.Model):
    required_int = models.IntegerField()
    int_with_default = models.IntegerField(default=42)
    nullable_int = models.IntegerField(null=True)
    nullable_int_with_default = models.IntegerField(default=42)
    uuid_field = models.UUIDField()
    uuid_field_with_default = models.UUIDField(
        default=UUID("125a77ef-d158-4bea-b036-8dcdbdde428d")
    )

    nullable_str = models.CharField(null=True, blank=False, max_length=1)
    nullable_and_blank_str = models.CharField(null=True, blank=False, max_length=1)
    blank_str = models.CharField(null=False, blank=True, max_length=1)
    slug = models.SlugField()

    field_with_help_text = models.IntegerField(help_text="This is the help text")
    field_with_verbose_name = models.IntegerField(verbose_name="The Verbose Name")

    foreign_key = models.ForeignKey("auth.User", on_delete=models.DO_NOTHING)

    str_with_choices_and_default = models.CharField(
        max_length=3, choices=StrChoices.choices, default=StrChoices.bar
    )
    str_with_choices_and_incorrectly_typed_default = models.CharField(
        max_length=3, choices=StrChoices.choices, default=1974
    )
    str_with_choices_and_incorrectly_typed_default_factory = models.CharField(
        max_length=3, choices=StrChoices.choices, default=lambda: 1985
    )
    str_with_choices_and_blank = models.CharField(
        max_length=3, choices=StrChoices.choices, blank=True
    )
    int_with_choices = models.IntegerField(choices=((1, "FOO"), (8, "BAR")))

    int_with_choices_and_blank = models.IntegerField(
        blank=True,
        choices=((1, "FOO"), (8, "BAR")),
        # Note we explicitly do not set null=False here -- in Django, this means we
        # would get an IntegrityError if trying to save this with the default, but at
        # the configuration model layer we'll allow that and let Django complain
        # (assuming that this was unintentional anyway).
        null=False,
    )
    int_with_choices_and_blank_and_non_choice_default = models.IntegerField(
        blank=True, choices=((1, "FOO"), (8, "BAR")), default=42
    )

    int_with_choices_callable = models.IntegerField(
        choices=lambda: ((1, "FOO"), (8, "BAR"))
    )

    boolean_field = models.BooleanField(default=True)
    json_with_default_factory = models.JSONField(default=lambda: {"foo": "bar"})
    array_field_with_default = ArrayField(
        models.JSONField(), default=lambda: [{"foo": "bar"}, {"foo": "baz"}]
    )
    array_field = ArrayField(models.JSONField(), null=True, blank=True)
    str_with_localized_default = models.TextField(default=_("Localized default"))
    int_with_lazy_default = models.IntegerField(
        default=lazy(lambda: 42, int)(), verbose_name="int with lazy default"
    )
