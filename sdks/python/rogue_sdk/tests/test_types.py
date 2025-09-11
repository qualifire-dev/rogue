import pytest
from pydantic import ValidationError
from rogue_sdk.types import AgentConfig, AuthType, Scenario, Scenarios, ScenarioType


class TestScenario:
    @pytest.mark.parametrize(
        "scenario_type, dataset, should_raise",
        [
            (ScenarioType.POLICY, None, False),
            (ScenarioType.POLICY, "some_dataset", False),  # will be ignored
            (ScenarioType.PROMPT_INJECTION, "some_dataset", False),
            (ScenarioType.PROMPT_INJECTION, None, True),
        ],
    )
    def test_validate_dataset_for_type(self, scenario_type, dataset, should_raise):
        input_data = {
            "scenario": "Test Scenario",
            "scenario_type": scenario_type,
            "dataset": dataset,
            "dataset_sample_size": -1,  # to avoid second validator raising
        }

        if should_raise:
            with pytest.raises(ValidationError, match="`dataset` must be provided"):
                Scenario(**input_data)
        else:
            scenario = Scenario(**input_data)
            if scenario_type == ScenarioType.POLICY:
                assert scenario.dataset is None
            else:
                assert scenario.dataset == dataset

    @pytest.mark.parametrize(
        "dataset, dataset_sample_size, should_raise",
        [
            (None, None, False),
            (None, 1, False),  # will be ignored
            ("datasetA", 5, False),
            ("datasetA", -1, False),
            ("datasetA", None, True),
        ],
    )
    def test_validate_dataset_sample_size(
        self,
        dataset,
        dataset_sample_size,
        should_raise,
    ):
        input_data = {
            "scenario": "Test Scenario",
            "scenario_type": (
                ScenarioType.PROMPT_INJECTION if dataset else ScenarioType.POLICY
            ),
            "dataset": dataset,
            "dataset_sample_size": dataset_sample_size,
        }

        if should_raise:
            with pytest.raises(
                ValidationError,
                match="`dataset_sample_size` must be set",
            ):
                Scenario(**input_data)
        else:
            scenario = Scenario(**input_data)
            assert scenario.dataset_sample_size == (
                dataset_sample_size if dataset else None
            )


class TestScenarios:
    @pytest.mark.parametrize(
        "scenario_types, filter_type, expected_count",
        [
            (
                [ScenarioType.POLICY, ScenarioType.PROMPT_INJECTION],
                ScenarioType.POLICY,
                1,
            ),
            (
                [ScenarioType.PROMPT_INJECTION, ScenarioType.PROMPT_INJECTION],
                ScenarioType.PROMPT_INJECTION,
                2,
            ),
            ([ScenarioType.POLICY], ScenarioType.PROMPT_INJECTION, 0),
        ],
    )
    def test_get_scenarios_by_type(self, scenario_types, filter_type, expected_count):
        scenarios = [
            Scenario(
                scenario=f"Scenario {i}",
                scenario_type=stype,
                dataset="data" if stype == ScenarioType.PROMPT_INJECTION else None,
                dataset_sample_size=(
                    1 if stype == ScenarioType.PROMPT_INJECTION else None
                ),
            )
            for i, stype in enumerate(scenario_types)
        ]
        collection = Scenarios(scenarios=scenarios)
        filtered = collection.get_scenarios_by_type(filter_type)
        assert len(filtered.scenarios) == expected_count

    def test_get_policy_scenarios(self):
        s1 = Scenario(
            scenario="policy1",
            scenario_type=ScenarioType.POLICY,
        )
        s2 = Scenario(
            scenario="prompt_injection1",
            scenario_type=ScenarioType.PROMPT_INJECTION,
            dataset="some",
            dataset_sample_size=1,
        )
        collection = Scenarios(scenarios=[s1, s2])
        result = collection.get_policy_scenarios()
        assert len(result.scenarios) == 1
        assert result.scenarios[0].scenario_type == ScenarioType.POLICY

    def test_get_prompt_injection_scenarios(self):
        s1 = Scenario(
            scenario="prompt_injection1",
            scenario_type=ScenarioType.PROMPT_INJECTION,
            dataset="some",
            dataset_sample_size=1,
        )
        s2 = Scenario(
            scenario="policy1",
            scenario_type=ScenarioType.POLICY,
        )
        collection = Scenarios(scenarios=[s1, s2])
        result = collection.get_prompt_injection_scenarios()
        assert len(result.scenarios) == 1
        assert result.scenarios[0].scenario_type == ScenarioType.PROMPT_INJECTION


class TestAuthType:
    @pytest.mark.parametrize(
        "auth_type, auth_credentials, expected_header",
        [
            (AuthType.NO_AUTH, "should be ignored", {}),
            (AuthType.API_KEY, "key123", {"X-API-Key": "key123"}),
            (AuthType.BEARER_TOKEN, "token456", {"Authorization": "Bearer token456"}),
            (AuthType.BASIC_AUTH, "user:pass", {"Authorization": "Basic user:pass"}),
            (AuthType.NO_AUTH, None, {}),
            (AuthType.API_KEY, None, {}),
            (AuthType.BEARER_TOKEN, None, {}),
            (AuthType.BASIC_AUTH, None, {}),
        ],
    )
    def test_get_auth_header(self, auth_type, auth_credentials, expected_header):
        header = auth_type.get_auth_header(auth_credentials)
        assert header == expected_header


class TestAgentConfig:
    @pytest.mark.parametrize(
        "auth_type, auth_credentials, should_raise",
        [
            (AuthType.NO_AUTH, "should be ignored", False),
            (AuthType.API_KEY, "abc123", False),
            (AuthType.BEARER_TOKEN, "token456", False),
            (AuthType.BASIC_AUTH, "user:pass", False),
            (AuthType.NO_AUTH, None, False),
            (AuthType.API_KEY, None, True),
            (AuthType.BEARER_TOKEN, None, True),
            (AuthType.BASIC_AUTH, None, True),
        ],
    )
    def test_check_auth_credentials(
        self,
        auth_type: str,
        auth_credentials: str | None,
        should_raise: bool,
    ):
        config_data = {
            "evaluated_agent_url": "https://example.com",
            "evaluated_agent_auth_type": auth_type,
            "evaluated_agent_credentials": auth_credentials,
        }

        if should_raise:
            with pytest.raises(
                ValidationError,
                match="Authentication Credentials cannot be empty",
            ):
                AgentConfig(**config_data)  # type: ignore
        else:
            config = AgentConfig(**config_data)  # type: ignore
            assert config.evaluated_agent_auth_type == auth_type
            assert config.evaluated_agent_credentials == auth_credentials
