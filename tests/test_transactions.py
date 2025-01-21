from unittest import mock

from django.contrib.auth.models import User

import pytest

from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.models import ConfigurationModel
from tests.conftest import ConfigStep

pytestmark = pytest.mark.django_db


def side_effect_test_func():
    pass


class TransactionTestConfigurationModel(ConfigurationModel):

    username: str


class TransactionTestConfigurationStep(
    BaseConfigurationStep[TransactionTestConfigurationModel]
):

    config_model = TransactionTestConfigurationModel
    enable_setting = "transaction_test_configuration_enabled"
    namespace = "transaction_test_configuration"
    verbose_name = "Transaction Test Configuration"

    def execute(self, model) -> None:
        User.objects.create_user(
            username=model.username,
            password="secret",
        )

        side_effect_test_func()


@pytest.fixture()
def valid_config_object(test_step_valid_config):
    return {
        "transaction_test_configuration_enabled": True,
        "transaction_test_configuration": {"username": "alice"},
    } | test_step_valid_config


def test_runner_rolls_back_all_on_failing_step(
    runner_factory, valid_config_object, step_execute_mock
):
    runner = runner_factory(
        steps=[TransactionTestConfigurationStep, ConfigStep],
        object_source=valid_config_object,
    )
    exc = Exception()
    step_execute_mock.side_effect = exc

    user_configuration_step_result, test_step_result = runner.execute_all()

    # Initial run is rolled back, so no objects created
    assert test_step_result.has_run
    assert test_step_result.run_exception is exc

    assert user_configuration_step_result.has_run
    assert user_configuration_step_result.run_exception is None
    assert User.objects.count() == 0

    # Subsequent run does not raise, so the objects are created
    step_execute_mock.side_effect = None

    user_configuration_step_result, test_step_result = runner.execute_all()

    assert test_step_result.has_run
    assert test_step_result.run_exception is None

    assert user_configuration_step_result.has_run
    assert user_configuration_step_result.run_exception is None
    assert User.objects.count() == 1


def test_runner_rolls_back_on_executing_single_step(
    runner_factory, valid_config_object
):
    runner = runner_factory(
        steps=[TransactionTestConfigurationStep, ConfigStep],
        object_source=valid_config_object,
    )
    with mock.patch("tests.test_transactions.side_effect_test_func") as m:
        exc = Exception()
        m.side_effect = exc

        user_configuration_step_result = runner._execute_step(
            runner.configured_steps[0]
        )

        assert user_configuration_step_result.has_run
        assert user_configuration_step_result.run_exception is exc
        assert User.objects.count() == 0

    user_configuration_step_result = runner._execute_step(runner.configured_steps[0])

    assert user_configuration_step_result.has_run
    assert user_configuration_step_result.run_exception is None
    assert User.objects.count() == 1
