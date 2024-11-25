from django.db import models


class TestModel(models.Model):
    required_int = models.IntegerField()
    int_with_default = models.IntegerField(default=42)
    nullable_int = models.IntegerField(null=True)
    nullable_str = models.CharField(null=True, blank=False, max_length=1)
    nullable_and_blank_str = models.CharField(null=True, blank=False, max_length=1)
    blank_str = models.CharField(null=False, blank=True, max_length=1)

    field_with_help_text = models.IntegerField(help_text="This is the help text")
    field_with_verbose_name = models.IntegerField(verbose_name="The Verbose Name")

    foreign_key = models.ForeignKey("auth.User", on_delete=models.DO_NOTHING)
