from django.db import models


class BasicFieldDescription(models.TextChoices):
    """
    Description of the values for basic Django model fields
    """

    ArrayField = "string, comma-delimited ('foo,bar,baz')"
    BooleanField = "True, False"
    CharField = "string"
    FileField = (
        "string represeting the (absolute) path to a file, "
        "including file extension: {example}".format(
            example="/absolute/path/to/file.xml"
        )
    )
    ImageField = (
        "string represeting the (absolute) path to an image file, "
        "including file extension: {example}".format(
            example="/absolute/path/to/image.png"
        )
    )
    IntegerField = "string representing an integer"
    JSONField = "Mapping: {example}".format(example="{'some_key': 'Some value'}")
    PositiveIntegerField = "string representing a positive integer"
    TextField = "text (string)"
    URLField = "string (URL)"
    UUIDField = "UUID string {example}".format(
        example="(e.g. f6b45142-0c60-4ec7-b43d-28ceacdc0b34)"
    )
