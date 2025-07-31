from argparse import ArgumentParser, Namespace
from pathlib import Path

import requests
from a2a.types import AgentCard
from loguru import logger
from pydantic import ValidationError, SecretStr
from rich.console import Console
from rich.markdown import Markdown

from .models.cli_input import CLIInput, PartialCLIInput
from .models.config import AuthType, AgentConfig
from .models.evaluation_result import EvaluationResults
from .models.scenario import Scenarios
from .services.llm_service import LLMService

# Import the Python SDK

from sdks.python.rogue_client import RogueSDK, RogueClientConfig
from sdks.python.rogue_client.types import AuthType as SDKAuthType


def _convert_auth_type(auth_type: AuthType) -> SDKAuthType:
    """Convert legacy AuthType to SDK AuthType."""
    mapping = {
        AuthType.NO_AUTH: SDKAuthType.NO_AUTH,
        AuthType.API_KEY: SDKAuthType.API_KEY,
        AuthType.BEARER_TOKEN: SDKAuthType.BEARER_TOKEN,
        AuthType.BASIC_AUTH: SDKAuthType.BASIC_AUTH,
    }
    return mapping.get(auth_type, SDKAuthType.NO_AUTH)


def _convert_sdk_results_to_legacy(sdk_results) -> EvaluationResults:
    """Convert SDK results to legacy EvaluationResults format."""
    # For now, create a basic conversion - this would need to be expanded
    # based on the actual SDK results structure
    try:
        if hasattr(sdk_results, "model_dump"):
            results_dict = sdk_results.model_dump()
        else:
            results_dict = sdk_results

        return EvaluationResults.model_validate(results_dict)
    except Exception as e:
        logger.warning(f"Failed to convert SDK results to legacy format: {e}")
        # Return empty results as fallback
        return EvaluationResults()


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
        help="Path to input scenarios file. defaults to `<workdir>/scenarios.json`",
    )
    parser.add_argument(
        "--output-report-file",
        required=False,
        type=Path,
        help="Path to output report file",
    )
    parser.add_argument(
        "-m",
        "--judge-llm-model",
        required=False,
        help="Model to use for scenario evaluation and report generation",
    )
    parser.add_argument(
        "--judge-llm-api-key",
        required=False,
        help="Api key to use when communicating with the LLM provider. "
        "Can be left unset if env is used.",
    )
    parser.add_argument(
        "--deep-test-mode",
        default=False,
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
    evaluated_agent_auth_credentials_secret: SecretStr | None,
    judge_llm: str,
    judge_llm_api_key_secret: SecretStr | None,
    scenarios: Scenarios,
    evaluation_results_output_path: Path,
    business_context: str,
    deep_test_mode: bool,
) -> EvaluationResults | None:
    evaluated_agent_auth_credentials = (
        evaluated_agent_auth_credentials_secret.get_secret_value()
        if evaluated_agent_auth_credentials_secret
        else None
    )
    judge_llm_api_key = (
        judge_llm_api_key_secret.get_secret_value()
        if judge_llm_api_key_secret
        else None
    )

    # Try SDK first, fallback to legacy service if server not available
    try:
        return await _run_scenarios_with_sdk(
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
    except Exception as e:
        logger.warning(f"SDK evaluation failed, falling back to legacy service: {e}")
        return await _run_scenarios_legacy(
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


async def _run_scenarios_with_sdk(
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
    """Run scenarios using the new SDK."""
    # Convert AuthType to SDK AuthType
    sdk_auth_type = _convert_auth_type(evaluated_agent_auth_type)

    # Initialize SDK
    sdk_config = RogueClientConfig(
        base_url="http://localhost:8000", timeout=300.0  # Default server URL
    )
    sdk = RogueSDK(sdk_config)

    try:
        # Check if server is available
        health = await sdk.health()
        if health.status != "healthy":
            raise Exception("Server not healthy")

        # Convert scenarios to list of strings for SDK
        scenario_strings = [scenario.scenario for scenario in scenarios.scenarios]

        # Use SDK's quick_evaluate method
        job = await sdk.quick_evaluate(
            agent_url=evaluated_agent_url,
            scenarios=scenario_strings,
            auth_type=sdk_auth_type,
            auth_credentials=evaluated_agent_auth_credentials,
            judge_model=judge_llm,
            deep_test=deep_test_mode,
        )

        logger.info(f"Started evaluation job {job.job_id} using SDK")

        # Wait for completion and get results
        final_job = await sdk.wait_for_evaluation(job.job_id)

        if final_job.results:
            # Convert SDK results to legacy format for backward compatibility
            results = _convert_sdk_results_to_legacy(final_job.results)

            # Write results to file for CLI compatibility
            evaluation_results_output_path.write_text(
                results.model_dump_json(indent=2, exclude_none=True),
                encoding="utf-8",
            )
            return results
        else:
            logger.error("Scenario evaluation completed but no results found.")
            return None

    finally:
        await sdk.close()


async def _run_scenarios_legacy(
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
    """Run scenarios using the legacy service (fallback)."""
    from .services.scenario_evaluation_service import ScenarioEvaluationService

    scenario_evaluation_service = ScenarioEvaluationService(
        evaluated_agent_url=evaluated_agent_url,
        evaluated_agent_auth_type=evaluated_agent_auth_type,
        evaluated_agent_auth_credentials=evaluated_agent_auth_credentials,
        judge_llm=judge_llm,
        judge_llm_api_key=judge_llm_api_key,
        scenarios=scenarios,
        business_context=business_context,
        deep_test_mode=deep_test_mode,
    )

    results = None
    async for status, data in scenario_evaluation_service.evaluate_scenarios():
        if status == "done":
            results = data
            break

    if results:
        # Write results to file for CLI compatibility
        evaluation_results_output_path.write_text(
            results.model_dump_json(indent=2, exclude_none=True),
            encoding="utf-8",
        )
        return results

    logger.error("Scenario evaluation failed. Results not found.")
    return None


def create_report(
    judge_llm: str,
    results: EvaluationResults,
    output_report_file: Path,
    judge_llm_api_key_secret: SecretStr | None = None,
) -> str:
    judge_llm_api_key = (
        judge_llm_api_key_secret.get_secret_value()
        if judge_llm_api_key_secret
        else None
    )
    summary = LLMService().generate_summary_from_results(
        model=judge_llm,
        results=results,
        llm_provider_api_key=judge_llm_api_key,
    )

    output_report_file.parent.mkdir(parents=True, exist_ok=True)
    output_report_file.write_text(summary)
    return summary


def get_exit_code(evaluation_results: EvaluationResults) -> int:
    for result in evaluation_results.results:
        if not result.passed:
            return 1
    return 0


def merge_config_with_cli(
    config_data: dict,
    cli_args: Namespace,
) -> CLIInput:
    # Convert CLI args Namespace to dict, removing None values
    cli_dict = {k: v for k, v in vars(cli_args).items() if v is not None}

    # Merge CLI > Config
    merged = {
        **config_data,
        **cli_dict,
    }

    partial = PartialCLIInput(**merged)

    # Handle business_context_file logic
    if (
        partial.business_context is None
        and partial.business_context_file is not None
        and partial.business_context_file.exists()
    ):
        logger.info("Using business context file")
        partial.business_context = partial.business_context_file.read_text()
    else:
        logger.info("Using business context str")

    # Remove file-specific fields not in final schema
    data = partial.model_dump(
        exclude={
            "business_context_file",
            "config_file",
        },
    )

    logger.debug(f"Running with parameters: {data}")

    # Finally, validate as full input
    return CLIInput(**data)


def read_config_file(config_file: Path) -> dict:
    if config_file.is_file():
        try:
            return AgentConfig.model_validate_json(
                config_file.read_text(),
            ).model_dump(
                by_alias=True,
                exclude_none=True,
            )
        except ValidationError:
            logger.exception("Failed to parse config as AgentConfig from file")

        try:
            return PartialCLIInput.model_validate_json(
                config_file.read_text(),
            ).model_dump(exclude_none=True)
        except ValidationError:
            logger.exception("Failed to parse config as PartialCLIInput from file")

    logger.info("Config file not found")
    return {}


def get_cli_input(cli_args: Namespace) -> CLIInput:
    config_file = cli_args.config_file or cli_args.workdir / "user_config.json"
    config = read_config_file(config_file)

    cli_input = merge_config_with_cli(config, cli_args)
    return cli_input


def get_agent_card(agent_url: str) -> AgentCard:
    try:
        response = requests.get(
            f"{agent_url}/.well-known/agent.json",
            timeout=5,
        )
        return AgentCard.model_validate(response.json())
    except Exception:
        logger.debug(
            "Failed to connect to agent",
            extra={"agent_url": agent_url},
            exc_info=True,
        )
        raise


async def run_cli(args: Namespace) -> int:
    cli_input = get_cli_input(args)
    logger.debug("Running CLI", extra=cli_input.model_dump())

    # fast fail if the agent is not reachable
    get_agent_card(cli_input.evaluated_agent_url.encoded_string())

    scenarios = cli_input.get_scenarios_from_file()

    logger.info(
        "Running scenarios",
        extra={
            "scenarios_length": len(scenarios.scenarios),
        },
    )
    results = await run_scenarios(
        evaluated_agent_url=cli_input.evaluated_agent_url.encoded_string(),
        evaluated_agent_auth_type=cli_input.evaluated_agent_auth_type,
        evaluated_agent_auth_credentials_secret=cli_input.evaluated_agent_credentials,
        judge_llm=cli_input.judge_llm_model,
        judge_llm_api_key_secret=cli_input.judge_llm_api_key,
        scenarios=scenarios,
        evaluation_results_output_path=args.workdir / "evaluation_results.json",
        business_context=cli_input.business_context,
        deep_test_mode=cli_input.deep_test_mode,
    )
    if not results:
        raise ValueError(
            f"No scenarios were evaluated for {cli_input.evaluated_agent_url}"
        )

    logger.info("Creating report")
    report_summary = create_report(
        judge_llm=cli_input.judge_llm_model,
        results=results,
        output_report_file=cli_input.output_report_file,
        judge_llm_api_key_secret=cli_input.judge_llm_api_key,
    )

    logger.info("Report saved", extra={"report_file": cli_input.output_report_file})

    console = Console()
    console.print(Markdown(report_summary))

    return get_exit_code(results)
