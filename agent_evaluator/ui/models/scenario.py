from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ScenarioCategory(Enum):
    FUNCTIONAL = "functional"
    EDGE_CASE = "edge_case"
    ERROR_HANDLING = "error_handling"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ScenarioInput(BaseModel):
    input_type: str  # text, file, json
    content: Any
    metadata: Dict[str, Any] = {}


class ExpectedOutput(BaseModel):
    output_type: str
    expected_content: Any
    tolerance: Optional[float] = None


class EvaluationCriterion(BaseModel):
    criterion: str
    weight: float


class TestScenario(BaseModel):
    scenario_id: str
    name: str
    description: str
    category: ScenarioCategory
    priority: Priority
    inputs: List[ScenarioInput]
    expected_outputs: List[ExpectedOutput]
    evaluation_criteria: List[EvaluationCriterion]
