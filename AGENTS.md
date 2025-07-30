# Agent Instructions

This file provides instructions for AI agents working in this repository.

## Dependencies

- **Install**: `uv sync --dev --examples`

## Build, Lint, and Test

- **Build**: `uv build`
- **Lint**:
  - `uv run black --check .`
  - `uv run flake8 .`
  - `uv run mypy --config-file .mypy.ini .`
  - `uv run bandit -c .bandit.yaml -r .`
- **Test**:
  - Run all tests: `uv run pytest`
  - Run a single test file: `uv run pytest path/to/test_file.py`
  - Run a single test function: `uv run pytest path/to/test_file.py::test_function`
- **Codestyle**: `uv run black --check . && uv run flake8 . && uv run mypy --config-file .mypy.ini . && uv run bandit -c .bandit.yaml -r .`
- **Pre-commit**: `pre-commit run --all-files`
- **Lock check**: `uv lock --check`

## Code Style

- **Formatting**: Use `black` for code formatting.
- **Imports**: Use `isort` conventions (though not explicitly enforced).
- **Types**: Use type hints for all function signatures.
- **Naming**: Follow PEP 8 naming conventions (snake_case for variables and functions, PascalCase for classes).
- **Error Handling**: Use try/except blocks for code that may raise exceptions.
- **Dependencies**: Use `uv` for dependency management. Add new dependencies to `pyproject.toml`.

## Project Structure

- `rogue/`: The main Python package.
- `tests/`: Contains all tests.
- `examples/`: Example agent implementations.
- `.github/`: CI/CD workflows.

## Running the application

- **CLI**: `uv run python -m rogue`
- **UI**: `uv run gradio rogue/ui/app.py`

## Running the examples

- **T-Shirt Store**: `uv run python -m examples.tshirt_store_agent`
- **T-Shirt Store (LangGraph)**: `uv run python -m examples.tshirt_store_langgraph_agent`

## Running the evaluator

- **Evaluator Agent**: `uv run python -m rogue.evaluator_agent`
- **Prompt Injection Evaluator**: `uv run python -m rogue.prompt_injection_evaluator`

## Running the rogue agent

- **Rogue Agent**: `uv run python -m rogue.common.agent_model_wrapper`
- **Rogue Agent with specific model**: `uv run python -m rogue.common.agent_model_wrapper --model <model_name>`
- **Rogue Agent with specific model and scenario**: `uv run python -m rogue.common.agent_model_wrapper --model <model_name> --scenario <scenario_name>`
- **Rogue Agent with specific model, scenario and retries**: `uv run python -m rogue.common.agent_model_wrapper --model <model_name> --scenario <scenario_name> --retries <retries>`
- **Rogue Agent with specific model, scenario, retries and log file**: `uv run python -m rogue.common.agent_model_wrapper --model <model_name> --scenario <scenario_name> --retries <retries> --log-file <log_file>`
- **Rogue Agent with specific model, scenario, retries, log file and config file**: `uv run python -m rogue.common.agent_model_wrapper --model <model_name> --scenario <scenario_name> --retries <retries> --log-file <log_file> --config-file <config_file>`
- **Rogue Agent with specific model, scenario, retries, log file, config file and output file**: `uv run python -m rogue.common.agent_model_wrapper --model <model_name> --scenario <scenario_name> --retries <retries> --log-file <log_file> --config-file <config_file> --output-file <output_file>`
- **Rogue Agent with specific model, scenario, retries, log file, config file, output file and workdir**: `uv run python -m rogue.common.agent_model_wrapper --model <model_name> --scenario <scenario_name> --retries <retries> --log-file <log_file> --config-file <config_file> --output-file <output_file> --workdir <workdir>`
