import json
from pathlib import Path

from rogue.models.scenario import Scenarios


def dump_business_context(state: dict, current_context: str):
    workdir: Path | None = state.get("workdir")
    if workdir is not None:
        output_file = workdir / "business_context.md"
        output_file.write_text(current_context)


def dump_scenarios(state: dict, scenarios: Scenarios):
    workdir: Path | None = state.get("workdir")
    if workdir is not None:
        output_file = workdir / "scenarios.json"
        output_file.write_text(scenarios.model_dump_json(indent=2))


def dump_config(state: dict, config: dict):
    workdir: Path | None = state.get("workdir")
    if workdir is not None:
        config_path = workdir / "user_config.json"
        config_path.write_text(json.dumps(config, indent=2))


def load_config(state: dict) -> dict:
    workdir: Path | None = state.get("workdir")
    if workdir is not None:
        config_path = workdir / "user_config.json"
        if config_path.exists():
            return json.loads(config_path.read_text())
    return {}
