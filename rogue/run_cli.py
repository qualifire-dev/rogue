from argparse import ArgumentParser, Namespace
from pathlib import Path

from .models.config import AuthType
from .models.evaluation_result import EvaluationResults


def set_cli_args(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--evaluated-agent-url",
        required=True,
        help="URL of the agent to evaluate",
    )
    parser.add_argument(
        "--evaluated-agent-auth-type",
        required=False,
        type=AuthType,
        default=AuthType.NO_AUTH,
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
        required=True,
        type=Path,
        help="Path to input scenarios file",
    )
    parser.add_argument(
        "--output-report-file",
        required=True,
        type=Path,
        help="Path to output report file",
    )
    parser.add_argument(
        "--model",
        required=True,
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
    business_context_group = parser.add_mutually_exclusive_group(required=True)
    business_context_group.add_argument(
        "--business-context",
        help="A description of the business context of the evaluated agent",
    )
    business_context_group.add_argument(
        "--business-context-file",
        type=Path,
        help="A path to a file containing the business context of the evaluated agent",
    )


async def run_scenarios() -> EvaluationResults:
    # TODO: implement
    return EvaluationResults()


async def create_report(results: EvaluationResults, output_report_file: Path):
    # TODO: implement
    return


async def run_cli(args: Namespace):
    evaluated_agent_url: str = args.evaluated_agent_url
    evaluated_agent_auth_type: AuthType = args.evaluated_agent_auth_type
    evaluated_agent_credentials: str = args.evaluated_agent_credentials
    input_scenarios_file: Path = args.input_scenarios_file
    output_report_file: Path = args.output_report_file
    model: str = args.model
    llm_provider_api_key: str | None = args.llm_provider_api_key
    deep_test_mode: bool = args.deep_test_mode
    business_context: str | None = args.business_context
    business_context_file = args.business_context_file

    if business_context_file:
        business_context = business_context_file.read_text()

    # TODO: implement
    results = await run_scenarios()
    await create_report(results, output_report_file)
    return
