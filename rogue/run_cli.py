import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from loguru import logger
from pydantic import ValidationError

from .models.config import AuthType, AgentConfig
from .models.evaluation_result import EvaluationResults
from .models.scenario import Scenarios
from .services.llm_service import LLMService
from .services.scenario_evaluation_service import ScenarioEvaluationService


def set_cli_args(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--config-file",
        type=Path,
        help="Path to config file",
    )
    parser.add_argument(
        "--evaluated-agent-url",
        required=False,
        help="URL of the agent to evaluate",
    )
    parser.add_argument(
        "--evaluated-agent-auth-type",
        required=False,
        type=AuthType,
        choices=[e.value for e in AuthType],
        help="How to authenticate with the evaluated agent (if needed)."
        f"Valid options are: {[e.value for e in AuthType]}",
    )
    parser.add_argument(
        "--evaluated-agent-credentials",
        required=False,
        help="credentials to use when authenticating with the evaluated agent "
        "(if needed).",
    )
    parser.add_argument(
        "--input-scenarios-file",
        required=False,
        type=Path,
        help="Path to input scenarios file",
    )
    parser.add_argument(
        "--output-report-file",
        required=False,
        type=Path,
        help="Path to output report file",
    )
    parser.add_argument(
        "--model",
        required=False,
        help="Model to use for scenario evaluation and report generation",
    )
    parser.add_argument(
        "--llm-provider-api-key",
        required=False,
        help="Api key to use when communicating with the LLM provider. "
        "Can be left unset if env is used.",
    )
    parser.add_argument(
        "--deep-test-mode",
        default=False,
        type=bool,
        action="store_true",
        help="Enable deep test mode",
    )
    business_context_group = parser.add_mutually_exclusive_group(required=False)
    business_context_group.add_argument(
        "--business-context",
        help="A description of the business context of the evaluated agent",
    )
    business_context_group.add_argument(
        "--business-context-file",
        type=Path,
        help="A path to a file containing the business context of the evaluated agent",
    )


async def run_scenarios(
    evaluated_agent_url: str,
    evaluated_agent_auth_type: AuthType,
    evaluated_agent_auth_credentials: str | None,
    judge_llm: str,
    judge_llm_api_key: str | None,
    scenarios: Scenarios,
    evaluation_results_output_path: Path,
    business_context: str,
    deep_test_mode: bool,
) -> EvaluationResults | None:
    scenario_evaluation_service = ScenarioEvaluationService(
        evaluated_agent_url=evaluated_agent_url,
        evaluated_agent_auth_type=evaluated_agent_auth_type,
        evaluated_agent_auth_credentials=evaluated_agent_auth_credentials,
        judge_llm=judge_llm,
        judge_llm_api_key=judge_llm_api_key,
        scenarios=scenarios,
        evaluation_results_output_path=evaluation_results_output_path,
        business_context=business_context,
        deep_test_mode=deep_test_mode,
    )
    async for status, data in scenario_evaluation_service.evaluate_scenarios():
        if status == "done":
            return data  # type: ignore

    logger.error("Scenario evaluation failed. Results not found.")
    return None


def create_report(
    model: str,
    results: EvaluationResults,
    output_report_file: Path,
    llm_provider_api_key: str | None = None,
):
    summary = LLMService().generate_summary_from_results(
        model=model,
        results=results,
        llm_provider_api_key=llm_provider_api_key,
    )

    output_report_file.write_text(summary)


def validate_args(
    evaluated_agent_url: str | None,
    evaluated_agent_auth_type: AuthType,
    evaluated_agent_credentials: str | None,
    model: str | None,
    input_scenarios_file: Path,
    business_context: str | None,
):
    required_args = {
        "evaluated_agent_url": evaluated_agent_url,
        "model": model,
        "input_scenarios_file": input_scenarios_file,
        "business_context": business_context,
    }
    for arg, value in required_args.items():
        if not value:
            raise ValueError(f"Missing required argument: {arg}")

    if (
        evaluated_agent_auth_type != AuthType.NO_AUTH
        and not evaluated_agent_credentials
    ):
        raise ValueError(
            "Authentication credentials are required for authenticated agents"
        )

    if not input_scenarios_file.exists():
        raise ValueError(f"Input scenarios file does not exist: {input_scenarios_file}")


def get_exit_code(evaluation_results: EvaluationResults) -> int:
    for result in evaluation_results.results:
        if not result.passed:
            return 1
    return 0


async def run_cli(args: Namespace):
    config_file = args.config_file or args.workdir / "user_config.json"

    config = {}
    if config_file.exists():
        try:
            config = AgentConfig.model_validate_json(
                config_file.read_text()
            ).model_dump()
        except ValidationError:
            logger.exception("Failed to load config from file")

    # CLI args override config file
    evaluated_agent_url: str | None = args.evaluated_agent_url or config.get(
        "agent_url",
    )
    evaluated_agent_auth_type: AuthType = args.evaluated_agent_auth_type or config.get(
        "auth_type",
        AuthType.NO_AUTH,
    )
    evaluated_agent_credentials: str | None = (
        args.evaluated_agent_credentials
        or config.get(
            "auth_credentials",
        )
    )
    model: str | None = args.model or config.get("judge_llm")
    llm_provider_api_key: str | None = args.llm_provider_api_key or config.get(
        "judge_llm_api_key",
    )
    deep_test_mode: bool = args.deep_test_mode or config.get("deep_test_mode", False)

    input_scenarios_file: Path = args.input_scenarios_file
    output_report_file: Path = args.output_report_file or args.workdir / "report.md"
    business_context: str | None = args.business_context
    business_context_file = args.business_context_file

    if business_context_file and business_context_file.exists():
        business_context = business_context_file.read_text()

    validate_args(
        evaluated_agent_url=evaluated_agent_url,
        evaluated_agent_auth_type=evaluated_agent_auth_type,
        evaluated_agent_credentials=evaluated_agent_credentials,
        model=model,
        input_scenarios_file=input_scenarios_file,
        business_context=business_context,
    )

    scenarios = Scenarios.model_validate_json(input_scenarios_file.read_text())

    results = await run_scenarios(
        evaluated_agent_url=str(evaluated_agent_url),
        evaluated_agent_auth_type=evaluated_agent_auth_type,
        evaluated_agent_auth_credentials=evaluated_agent_credentials,
        judge_llm=str(model),
        judge_llm_api_key=llm_provider_api_key,
        scenarios=scenarios,
        evaluation_results_output_path=args.workdir / "evaluation_results.json",
        business_context=str(business_context),
        deep_test_mode=deep_test_mode,
    )
    if not results:
        raise ValueError(f"No scenarios were evaluated for {evaluated_agent_url}")

    create_report(
        model=str(model),
        results=results,
        output_report_file=output_report_file,
        llm_provider_api_key=llm_provider_api_key,
    )

    sys.exit(get_exit_code(results))
