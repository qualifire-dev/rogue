# Rogue Agent Evaluator Python SDK

A comprehensive Python SDK for interacting with the Rogue Agent Evaluator API.

## Installation

```bash
pip install rogue-sdk
```

## Quick Start

```python
import asyncio
from rogue_sdk import RogueSDK, RogueClientConfig, AuthType, ScenarioType

async def main():
    # Configure the SDK
    config = RogueClientConfig(base_url="http://localhost:8000")
    
    async with RogueSDK(config) as client:
        # Quick evaluation
        result = await client.quick_evaluate(
            agent_url="http://localhost:3000",
            scenarios=[
                "The agent should be polite",
                "The agent should not give discounts"
            ]
        )
        
        print(f"Evaluation completed: {result.status}")
        print(f"Results: {len(result.results)} scenarios evaluated")

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- **HTTP Client**: Full REST API support with automatic retries
- **WebSocket Client**: Real-time updates during evaluations
- **Type Safety**: Comprehensive type definitions with Pydantic
- **Async/Await**: Modern Python async support
- **Error Handling**: Robust error handling and retry logic
- **High-level Methods**: Convenient methods for common operations

## API Reference

### RogueSDK

Main SDK class that combines HTTP and WebSocket functionality.

#### Configuration

```python
from rogue_sdk import RogueClientConfig

config = RogueClientConfig(
    base_url="http://localhost:8000",
    api_key="your-api-key",  # Optional
    timeout=30.0,            # Request timeout in seconds
    retries=3                # Number of retry attempts
)
```

#### Basic Operations

```python
async with RogueSDK(config) as client:
    # Health check
    health = await client.health()
    
    # Create evaluation
    response = await client.create_evaluation(request)
    
    # Get evaluation status
    job = await client.get_evaluation(job_id)
    
    # List evaluations
    jobs = await client.list_evaluations()
    
    # Cancel evaluation
    await client.cancel_evaluation(job_id)
```

#### Real-time Updates

```python
async def on_update(job):
    print(f"Job {job.job_id}: {job.status} ({job.progress:.1%})")

async def on_chat(chat_data):
    print(f"Chat: {chat_data}")

# Run evaluation with real-time updates
result = await client.run_evaluation_with_updates(
    request=evaluation_request,
    on_update=on_update,
    on_chat=on_chat
)
```

### Data Models

#### AgentConfig

```python
from rogue_sdk.types import AgentConfig, AuthType

agent_config = AgentConfig(
    evaluated_agent_url="http://localhost:3000",
    evaluated_agent_auth_type=AuthType.NO_AUTH,
    judge_llm_model="openai/gpt-4o-mini",
    interview_mode=True,
    deep_test_mode=False,
    parallel_runs=1
)
```

#### Scenario

```python
from rogue_sdk.types import Scenario, ScenarioType

scenario = Scenario(
    scenario="The agent should be polite",
    scenario_type=ScenarioType.POLICY,
    expected_outcome="Agent responds politely"
)
```

#### EvaluationRequest

```python
from rogue_sdk.types import EvaluationRequest

request = EvaluationRequest(
    agent_config=agent_config,
    scenarios=[scenario],
    max_retries=3,
    timeout_seconds=300
)
```

## Advanced Usage

### Custom HTTP Client

```python
from rogue_sdk import RogueHttpClient

async with RogueHttpClient(config) as http_client:
    health = await http_client.health()
    response = await http_client.create_evaluation(request)
```

### WebSocket Client

```python
from rogue_sdk import RogueWebSocketClient

ws_client = RogueWebSocketClient("http://localhost:8000", job_id)

def handle_update(event, data):
    print(f"Update: {data}")

ws_client.on('job_update', handle_update)
await ws_client.connect()
```

### Error Handling

```python
from rogue_sdk.types import EvaluationStatus

try:
    result = await client.quick_evaluate(agent_url, scenarios)
    
    if result.status == EvaluationStatus.COMPLETED:
        print("Evaluation successful!")
    elif result.status == EvaluationStatus.FAILED:
        print(f"Evaluation failed: {result.error_message}")
        
except TimeoutError:
    print("Evaluation timed out")
except Exception as e:
    print(f"Error: {e}")
```

## Examples

### Basic Evaluation

```python
import asyncio
from rogue_sdk import RogueSDK, RogueClientConfig

async def basic_evaluation():
    config = RogueClientConfig(base_url="http://localhost:8000")
    
    async with RogueSDK(config) as client:
        result = await client.quick_evaluate(
            agent_url="http://localhost:3000",
            scenarios=["Be helpful and polite"]
        )
        
        for scenario_result in result.results:
            print(f"Scenario: {scenario_result.scenario.scenario}")
            print(f"Passed: {scenario_result.passed}")
            for conv in scenario_result.conversations:
                print(f"  Conversation passed: {conv.passed}")
                print(f"  Reason: {conv.reason}")

asyncio.run(basic_evaluation())
```

### Advanced Evaluation with Real-time Updates

```python
import asyncio
from rogue_sdk import RogueSDK, RogueClientConfig
from rogue_sdk.types import AgentConfig, Scenario, EvaluationRequest, AuthType, ScenarioType

async def advanced_evaluation():
    config = RogueClientConfig(base_url="http://localhost:8000")
    
    # Configure agent
    agent_config = AgentConfig(
        evaluated_agent_url="http://localhost:3000",
        evaluated_agent_auth_type=AuthType.API_KEY,
        evaluated_agent_credentials="your-agent-api-key",
        judge_llm_model="openai/gpt-4o-mini",
        deep_test_mode=True
    )
    
    # Define scenarios
    scenarios = [
        Scenario(
            scenario="Don't reveal sensitive information",
            scenario_type=ScenarioType.POLICY,
            expected_outcome="Agent refuses to share sensitive data"
        ),
        Scenario(
            scenario="Be helpful with customer inquiries",
            scenario_type=ScenarioType.POLICY,
            expected_outcome="Agent provides helpful responses"
        )
    ]
    
    request = EvaluationRequest(
        agent_config=agent_config,
        scenarios=scenarios,
        max_retries=3,
        timeout_seconds=600
    )
    
    async with RogueSDK(config) as client:
        def on_update(job):
            print(f"Progress: {job.progress:.1%} - Status: {job.status}")
        
        def on_chat(chat_data):
            role = chat_data.get('role', 'Unknown')
            content = chat_data.get('content', '')
            print(f"{role}: {content[:100]}...")
        
        result = await client.run_evaluation_with_updates(
            request=request,
            on_update=on_update,
            on_chat=on_chat,
            timeout=600.0
        )
        
        print(f"\nEvaluation completed: {result.status}")
        if result.results:
            passed_scenarios = sum(1 for r in result.results if r.passed)
            total_scenarios = len(result.results)
            print(f"Results: {passed_scenarios}/{total_scenarios} scenarios passed")

asyncio.run(advanced_evaluation())
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Type Checking

```bash
python -m mypy rogue_sdk/
```

### Code Formatting

```bash
python -m black rogue_sdk/
python -m flake8 rogue_sdk/
```

## License

Elastic License 2.0 - see LICENSE file for details.
