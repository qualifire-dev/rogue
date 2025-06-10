from enum import Enum

from loguru import logger
from pydantic import BaseModel, model_validator


class ScenarioType(Enum):
    POLICY = "policy"  # default
    PROMPT_INJECTION = "prompt_injection"
    SAFETY = "safety"
    GROUNDING = "grounding"


class Scenario(BaseModel):
    scenario: str
    scenario_type: ScenarioType = ScenarioType.POLICY
    dataset: str | None = None  # None if scenario_type in [policy, grounding]

    @model_validator(mode="after")
    def validate_dataset_for_type(self) -> "Scenario":
        non_dataset_types = [
            ScenarioType.POLICY,
            ScenarioType.GROUNDING,
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
