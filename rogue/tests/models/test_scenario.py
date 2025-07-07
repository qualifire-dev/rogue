import pytest
from pydantic import ValidationError

from rogue.models.scenario import (
    Scenario,
    ScenarioType,
    Scenarios,
)


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
        self, dataset, dataset_sample_size, should_raise
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
                ValidationError, match="`dataset_sample_size` must be set"
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
