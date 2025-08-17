import json
from pathlib import Path

from loguru import logger
from rogue_sdk.types import AgentConfig, Scenarios


def dump_business_context(state: dict, current_context: str):
    workdir: Path | None = state.get("workdir")
    if workdir is not None:
        workdir.mkdir(parents=True, exist_ok=True)
        output_file = workdir / "business_context.md"
        output_file.write_text(current_context)


def dump_scenarios(state: dict, scenarios: Scenarios):
    workdir: Path | None = state.get("workdir")
    if workdir is not None:
        workdir.mkdir(parents=True, exist_ok=True)
        output_file = workdir / "scenarios.json"
        output_file.write_text(scenarios.model_dump_json(indent=2))


def dump_config(state: dict, config: AgentConfig):
    workdir: Path | None = state.get("workdir")
    if not workdir:
        return

    config_dict = config.model_dump(mode="json")
    # Not storing any api keys or credentials
    sanitized_config = {
        k: v
        for k, v in config_dict.items()
        if not k.endswith("_key") and k != "auth_credentials"
    }

    workdir.mkdir(parents=True, exist_ok=True)
    config_path = workdir / "user_config.json"
    config_path.write_text(json.dumps(sanitized_config, indent=2))


def load_config(state: dict) -> dict:
    workdir: Path | None = state.get("workdir")
    if workdir is not None:
        config_path = workdir / "user_config.json"
        if config_path.exists():
            try:
                return json.loads(config_path.read_text())
            except json.JSONDecodeError:
                # If the file is empty or malformed, return an empty config
                logger.exception("Failed to load config from file")
                return {}
    return {}
