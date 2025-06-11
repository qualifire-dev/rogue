from typing import List, Dict, Any
from pydantic import BaseModel


class InterviewResponse(BaseModel):
    question_id: str
    question_text: str
    user_response: str
    extracted_entities: Dict[str, Any]
    confidence_score: float


class BusinessContext(BaseModel):
    domain: str
    use_cases: List[str]
    user_types: List[str]
    data_formats: List[str]
    success_criteria: List[str]
    edge_cases: List[str]
    integration_points: List[str]


class Conversation(BaseModel):
    history: List[InterviewResponse]
    business_context: BusinessContext
