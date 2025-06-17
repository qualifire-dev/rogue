from pathlib import Path

import pandas as pd

from ..evaluator_agent.run_evaluator_agent import run_evaluator_agent
from ..models.config import AuthType
from ..models.scenario import Scenarios


class ScenarioEvaluationService:
    def __init__(
        self,
        evaluated_agent_url: str,
        evaluated_agent_auth_type: AuthType,
        evaluated_agent_auth_credentials: str | None,
        judge_llm: str,
        judge_llm_api_key: str | None,
        scenarios: Scenarios,
        workdir: Path,
    ):
        self._evaluated_agent_url = evaluated_agent_url
        self._evaluated_agent_auth_type = evaluated_agent_auth_type
        self._evaluated_agent_auth_credentials = evaluated_agent_auth_credentials
        self._judge_llm = judge_llm
        self._judge_llm_api_key = judge_llm_api_key
        self._scenarios = scenarios
        self._workdir = workdir

    def _evaluate_policy_scenarios(self) -> pd.DataFrame:
        policy_scenarios = self._scenarios.get_policy_scenarios()
        return run_evaluator_agent(
            evaluated_agent_url=str(self._evaluated_agent_url),
            auth_type=self._evaluated_agent_auth_type,
            auth_credentials=self._evaluated_agent_auth_credentials,
            judge_llm=self._judge_llm,
            judge_llm_api_key=self._judge_llm_api_key,
            scenarios=policy_scenarios,
            workdir=self._workdir,
        )

    def _evaluate_prompt_injection_scenarios(self) -> pd.DataFrame:
        pass

    def _evaluate_safety_scenarios(self) -> pd.DataFrame:
        pass

    def _evaluate_grounding_scenarios(self) -> pd.DataFrame:
        pass

    def evaluate_scenarios(self) -> pd.DataFrame:
        policy_df = self._evaluate_policy_scenarios()
        prompt_injection_df = self._evaluate_prompt_injection_scenarios()
        safety_df = self._evaluate_safety_scenarios()
        grounding_df = self._evaluate_grounding_scenarios()

        dfs = [policy_df, prompt_injection_df, safety_df, grounding_df]
        dfs = [df for df in dfs if df is not None]

        return pd.concat(dfs, ignore_index=True)
