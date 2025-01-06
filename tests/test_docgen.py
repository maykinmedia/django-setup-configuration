from typing import Union

from pydantic import Field
from django_setup_configuration.docgen import DocGraphBuilder, YamlGenerator
from django_setup_configuration.models import ConfigurationModel
from django.contrib.auth.models import User


class AnotherNestedConfigModel(ConfigurationModel):
    nested_foo: str
    nested_optional_bar: int | None = None


class NestedConfigModel(ConfigurationModel):
    nested_foo: str
    nested_optional_bar: int | None = None


class ConfigModel(ConfigurationModel):
    foo: str = Field(description="Foo is my name")
    nested_obj: NestedConfigModel
    a_union_type: NestedConfigModel | AnotherNestedConfigModel
    a_legacy_union_type: Union[NestedConfigModel, AnotherNestedConfigModel]


class SimpleModel(ConfigurationModel):

    nested_field: NestedConfigModel
    config_model: ConfigModel
    deep_nested: list[list[ConfigModel]] | list[ConfigModel | NestedConfigModel]

    class Meta:
        django_model_refs = {User: ("username", "password")}


def test_builder():
    builder = DocGraphBuilder()
    graph = builder.build_graph(SimpleModel)

    assert graph

    generator = YamlGenerator()
    yaml = generator.generate_yaml(graph)

    assert yaml

    with open("example.yaml", "w") as f:
        f.write(yaml)
