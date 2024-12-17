from django.db import models


class StrChoices(models.TextChoices):
    foo = "foo", "Foo"
    bar = "bar", "Bar"


class TestModel(models.Model):
    required_int = models.IntegerField()
    int_with_default = models.IntegerField(default=42)
    nullable_int = models.IntegerField(null=True)
    nullable_int_with_default = models.IntegerField(default=42)

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
