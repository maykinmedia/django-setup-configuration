import functools
from unittest import mock

from django.contrib.auth.models import User

import pytest
import yaml
from pydantic import ValidationError

from django_setup_configuration.fields import DjangoModelRef
from django_setup_configuration.models import ConfigurationModel
from django_setup_configuration.runner import SetupConfigurationRunner
from testapp.configuration import BaseConfigurationStep


@pytest.fixture
def yaml_file_factory(tmp_path_factory):
    def f(obj):
        path = tmp_path_factory.mktemp("yaml-fixtures") / "fixture.yaml"
        with open(path, mode="w") as temp_file:
            yaml.dump(obj, temp_file)
            return str(path)

    return f


def assert_validation_errors_equal(
    validation_error: pytest.ExceptionInfo[ValidationError], expected
):
    errors_without_url = []

    for err in validation_error.value.errors():
        del err["url"]
        errors_without_url.append(err)

    assert errors_without_url == expected


def _mock_execute(*args, **kwargs):
    pass


class TestStepSubConfig(ConfigurationModel):
    another_foo: int


class TestStepConfig(ConfigurationModel):
    a_string: str
    optional_sub_model: TestStepSubConfig | None = None
    username = DjangoModelRef(User, "username")


class TestStep(BaseConfigurationStep[TestStepConfig]):
    verbose_name = "TestStep"
    config_model = TestStepConfig
    namespace = "test_step"
    enable_setting = "test_step_is_enabled"

    def execute(self, model):
        _mock_execute(model)


@pytest.fixture()
def test_step_valid_config():
    return {
        "test_step_is_enabled": True,
        "test_step": {
            "a_string": "hello",
            "username": "johndoe",
            "optional_sub_model": {
                "another_foo": 42,
            },
        },
    }


@pytest.fixture()
def test_step_yaml_path(yaml_file_factory, test_step_valid_config):
    return yaml_file_factory(test_step_valid_config)


@pytest.fixture()
def test_step_bad_yaml_path(yaml_file_factory):
    return yaml_file_factory(
        {
            "test_step_is_enabled": True,
            "test_step": {
                "a_string": 42,
                "username": None,
            },
        }
    )


@pytest.fixture()
def test_step_disabled_yaml_path(yaml_file_factory):
    return yaml_file_factory(
        {
            "test_step_is_enabled": False,
        }
    )


@pytest.fixture()
def runner(test_step_yaml_path):
    return SetupConfigurationRunner(steps=[TestStep], yaml_source=test_step_yaml_path)


@pytest.fixture()
def runner_with_invalid_yaml(test_step_bad_yaml_path):
    return SetupConfigurationRunner(
        steps=[TestStep], yaml_source=test_step_bad_yaml_path
    )


@pytest.fixture()
def runner_with_step_disabled_yaml(test_step_disabled_yaml_path):
    return SetupConfigurationRunner(
        steps=[TestStep], yaml_source=test_step_disabled_yaml_path
    )


@pytest.fixture()
def runner_factory():
    return functools.partial(SetupConfigurationRunner, steps=[TestStep])


@pytest.fixture()
def runner_step(runner):
    (step,) = runner.configured_steps
    return step


@pytest.fixture()
def expected_step_config(test_step_valid_config):
    return TestStepConfig.model_validate(test_step_valid_config["test_step"])


@pytest.fixture()
def step_execute_mock():
    with mock.patch("tests.conftest._mock_execute") as m:
        yield m
