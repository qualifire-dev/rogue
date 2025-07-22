from enum import Enum

from loguru import logger
from pydantic import BaseModel, model_validator


class ScenarioType(Enum):
    POLICY = "policy"  # default
    PROMPT_INJECTION = "prompt_injection"


class Scenario(BaseModel):
    scenario: str
    scenario_type: ScenarioType = ScenarioType.POLICY
    dataset: str | None = None  # None if scenario_type in [policy]
    expected_outcome: str | None = None

    # None if dataset is None, negative for all items in the dataset
    dataset_sample_size: int | None = None

    @model_validator(mode="after")
    def validate_dataset_for_type(self) -> "Scenario":
        non_dataset_types = [
            ScenarioType.POLICY,
        ]

        dataset_required = self.scenario_type not in non_dataset_types

        if dataset_required and self.dataset is None:
            raise ValueError(
                f"`dataset` must be provided when scenario_type is "
                f"'{self.scenario_type.value}'"
            )
        elif not dataset_required and self.dataset is not None:
            logger.info(
                f"`dataset` is not required for scenario_type "
                f"'{self.scenario_type.value}', ignoring.",
            )
            self.dataset = None
        return self

    @model_validator(mode="after")
    def validate_dataset_sample_size(self) -> "Scenario":
        if self.dataset is None:
            self.dataset_sample_size = None
            return self

        if self.dataset_sample_size is None:
            raise ValueError("`dataset_sample_size` must be set when `dataset` is set")

        return self


class Scenarios(BaseModel):
    scenarios: list[Scenario]

    def get_scenarios_by_type(self, scenario_type: ScenarioType) -> "Scenarios":
        return Scenarios(
            scenarios=[
                scenario
                for scenario in self.scenarios
                if scenario.scenario_type == scenario_type
            ]
        )

    def get_policy_scenarios(self) -> "Scenarios":
        return self.get_scenarios_by_type(ScenarioType.POLICY)

    def get_prompt_injection_scenarios(self) -> "Scenarios":
        return self.get_scenarios_by_type(ScenarioType.PROMPT_INJECTION)
