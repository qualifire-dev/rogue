# Rogue Agent Evaluator TypeScript SDK

A comprehensive TypeScript/JavaScript SDK for interacting with the Rogue Agent Evaluator API.

## Installation

```bash
npm install @rogue/sdk
# or
yarn add @rogue/sdk
```

## Quick Start

```typescript
import { RogueSDK, AuthType, ScenarioType } from '@rogue/sdk';

const client = new RogueSDK({
  baseUrl: 'http://localhost:8000'
});

// Quick evaluation
const result = await client.quickEvaluate(
  'http://localhost:3000',
  ['The agent should be polite', 'The agent should not give discounts']
);

console.log(`Evaluation completed: ${result.status}`);
console.log(`Results: ${result.results?.length} scenarios evaluated`);
```

## Features

- **HTTP Client**: Full REST API support with automatic retries
- **WebSocket Client**: Real-time updates during evaluations  
- **Type Safety**: Comprehensive TypeScript type definitions
- **Promise-based**: Modern async/await support
- **Error Handling**: Robust error handling and retry logic
- **High-level Methods**: Convenient methods for common operations

## API Reference

### RogueSDK

Main SDK class that combines HTTP and WebSocket functionality.

#### Configuration

```typescript
import { RogueSDK, RogueClientConfig } from '@rogue/sdk';

const config: RogueClientConfig = {
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key',  // Optional
  timeout: 30000,          // Request timeout in milliseconds
  retries: 3               // Number of retry attempts
};

const client = new RogueSDK(config);
```

#### Basic Operations

```typescript
// Health check
const health = await client.health();

// Create evaluation
const response = await client.createEvaluation(request);

// Get evaluation status
const job = await client.getEvaluation(jobId);

// List evaluations
const jobs = await client.listEvaluations();

// Cancel evaluation
await client.cancelEvaluation(jobId);
```

#### Real-time Updates

```typescript
const result = await client.runEvaluationWithUpdates(
  request,
  (job) => {
    console.log(`Job ${job.job_id}: ${job.status} (${(job.progress * 100).toFixed(1)}%)`);
  },
  (chatData) => {
    console.log(`Chat: ${chatData}`);
  }
);
```

### Data Models

#### AgentConfig

```typescript
import { AgentConfig, AuthType } from '@rogue/sdk';

const agentConfig: AgentConfig = {
  evaluated_agent_url: 'http://localhost:3000',
  evaluated_agent_auth_type: AuthType.NO_AUTH,
  judge_llm_model: 'openai/gpt-4o-mini',
  interview_mode: true,
  deep_test_mode: false,
  parallel_runs: 1
};
```

#### Scenario

```typescript
import { Scenario, ScenarioType } from '@rogue/sdk';

const scenario: Scenario = {
  scenario: 'The agent should be polite',
  scenario_type: ScenarioType.POLICY,
  expected_outcome: 'Agent responds politely'
};
```

#### EvaluationRequest

```typescript
import { EvaluationRequest } from '@rogue/sdk';

const request: EvaluationRequest = {
  agent_config: agentConfig,
  scenarios: [scenario],
  max_retries: 3,
  timeout_seconds: 300
};
```

## Advanced Usage

### Custom HTTP Client

```typescript
import { RogueHttpClient } from '@rogue/sdk';

const httpClient = new RogueHttpClient(config);
const health = await httpClient.health();
const response = await httpClient.createEvaluation(request);
```

### WebSocket Client

```typescript
import { RogueWebSocketClient } from '@rogue/sdk';

const wsClient = new RogueWebSocketClient('http://localhost:8000', jobId);

wsClient.on('job_update', (event, data) => {
  console.log('Update:', data);
});

await wsClient.connect();
```

### Error Handling

```typescript
import { EvaluationStatus } from '@rogue/sdk';

try {
  const result = await client.quickEvaluate(agentUrl, scenarios);
  
  if (result.status === EvaluationStatus.COMPLETED) {
    console.log('Evaluation successful!');
  } else if (result.status === EvaluationStatus.FAILED) {
    console.log(`Evaluation failed: ${result.error_message}`);
  }
} catch (error) {
  if (error.message.includes('timeout')) {
    console.log('Evaluation timed out');
  } else {
    console.log(`Error: ${error.message}`);
  }
}
```

## Examples

### Basic Evaluation

```typescript
import { RogueSDK } from '@rogue/sdk';

async function basicEvaluation() {
  const client = new RogueSDK({
    baseUrl: 'http://localhost:8000'
  });
  
  const result = await client.quickEvaluate(
    'http://localhost:3000',
    ['Be helpful and polite']
  );
  
  if (result.results) {
    for (const scenarioResult of result.results) {
      console.log(`Scenario: ${scenarioResult.scenario.scenario}`);
      console.log(`Passed: ${scenarioResult.passed}`);
      
      for (const conv of scenarioResult.conversations) {
        console.log(`  Conversation passed: ${conv.passed}`);
        console.log(`  Reason: ${conv.reason}`);
      }
    }
  }
}

basicEvaluation().catch(console.error);
```

### Advanced Evaluation with Real-time Updates

```typescript
import { 
  RogueSDK, 
  AgentConfig, 
  Scenario, 
  EvaluationRequest,
  AuthType,
  ScenarioType 
} from '@rogue/sdk';

async function advancedEvaluation() {
  const client = new RogueSDK({
    baseUrl: 'http://localhost:8000'
  });
  
  // Configure agent
  const agentConfig: AgentConfig = {
    evaluated_agent_url: 'http://localhost:3000',
    evaluated_agent_auth_type: AuthType.API_KEY,
    evaluated_agent_credentials: 'your-agent-api-key',
    judge_llm_model: 'openai/gpt-4o-mini',
    deep_test_mode: true
  };
  
  // Define scenarios
  const scenarios: Scenario[] = [
    {
      scenario: "Don't reveal sensitive information",
      scenario_type: ScenarioType.POLICY,
      expected_outcome: "Agent refuses to share sensitive data"
    },
    {
      scenario: "Be helpful with customer inquiries", 
      scenario_type: ScenarioType.POLICY,
      expected_outcome: "Agent provides helpful responses"
    }
  ];
  
  const request: EvaluationRequest = {
    agent_config: agentConfig,
    scenarios: scenarios,
    max_retries: 3,
    timeout_seconds: 600
  };
  
  const result = await client.runEvaluationWithUpdates(
    request,
    (job) => {
      console.log(`Progress: ${(job.progress * 100).toFixed(1)}% - Status: ${job.status}`);
    },
    (chatData) => {
      const role = chatData.role || 'Unknown';
      const content = chatData.content || '';
      console.log(`${role}: ${content.substring(0, 100)}...`);
    }
  );
  
  console.log(`\nEvaluation completed: ${result.status}`);
  if (result.results) {
    const passedScenarios = result.results.filter(r => r.passed).length;
    const totalScenarios = result.results.length;
    console.log(`Results: ${passedScenarios}/${totalScenarios} scenarios passed`);
  }
}

advancedEvaluation().catch(console.error);
```

### Node.js Usage

```typescript
// For Node.js environments, you may need to install ws for WebSocket support
import WebSocket from 'ws';

// The SDK will automatically use the WebSocket implementation
const client = new RogueSDK({
  baseUrl: 'http://localhost:8000'
});
```

### Browser Usage

```typescript
// In browser environments, the native WebSocket API is used automatically
const client = new RogueSDK({
  baseUrl: 'http://localhost:8000'
});

// Use with modern bundlers like Vite, Webpack, etc.
```

## Development

### Building

```bash
npm run build
```

### Type Checking

```bash
npm run type-check
```

### Testing

```bash
npm test
```

## License

MIT License - see LICENSE file for details.
