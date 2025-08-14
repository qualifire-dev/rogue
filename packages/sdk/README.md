# Rogue Agent Evaluator TypeScript SDK

A modern, functional TypeScript SDK for interacting with the Rogue Agent Evaluator API.

## Installation

```bash
npm install @rogue/sdk
# or
yarn add @rogue/sdk
```

## Quick Start

```typescript
import { createRogueClient } from '@rogue/sdk';

const client = createRogueClient({
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

## Why Functional?

This SDK uses a functional approach instead of classes because it's more idiomatic TypeScript:

- ✅ **No `this` binding issues** - destructuring works perfectly
- ✅ **Better tree-shaking** - import only what you need  
- ✅ **Easier testing** - mock individual functions
- ✅ **More composable** - easy to extend and combine
- ✅ **Modern TypeScript** - follows current best practices

## API Styles

### 1. Factory Function (Recommended)

```typescript
import { createRogueClient } from '@rogue/sdk';

const client = createRogueClient({ baseUrl: 'http://localhost:8000' });

// All methods available, state maintained
await client.health();
await client.createEvaluation(request);

// Destructuring works perfectly - no `this` issues!
const { quickEvaluate, createEvaluation } = client;
await quickEvaluate(agentUrl, scenarios);
```

### 2. Pure Functions

```typescript
import { quickEvaluate, createEvaluation, getEvaluation } from '@rogue/sdk';

const config = { baseUrl: 'http://localhost:8000' };

// Each function is independent
await quickEvaluate(config, agentUrl, scenarios);
await createEvaluation(config, request);
await getEvaluation(config, jobId);

// Perfect for functional programming
const results = await Promise.all([
  quickEvaluate(config, url1, scenarios1),
  quickEvaluate(config, url2, scenarios2),
]);
```

## Configuration

```typescript
import { createRogueClient, type RogueClientConfig } from '@rogue/sdk';

const config: RogueClientConfig = {
  baseUrl: 'http://localhost:8000',
  apiKey: 'your-api-key',  // Optional
  timeout: 30000,          // Request timeout in milliseconds
  retries: 3               // Number of retry attempts
};

const client = createRogueClient(config);
```

## Core Operations

### Health Check

```typescript
const health = await client.health();
console.log(`Server status: ${health.status}`);
```

### Create Evaluation

```typescript
import { AgentConfig, Scenario, AuthType, ScenarioType } from '@rogue/sdk';

const agentConfig: AgentConfig = {
  evaluated_agent_url: 'http://localhost:3000',
  evaluated_agent_auth_type: AuthType.NO_AUTH,
  judge_llm: 'openai/gpt-4o-mini',
  interview_mode: true,
  deep_test_mode: false,
  parallel_runs: 1
};

const scenarios: Scenario[] = [
  {
    scenario: 'The agent should be polite',
    scenario_type: ScenarioType.POLICY,
    expected_outcome: 'Agent responds politely'
  }
];

const request = {
  agent_config: agentConfig,
  scenarios: scenarios,
  max_retries: 3,
  timeout_seconds: 300
};

const response = await client.createEvaluation(request);
console.log(`Evaluation started: ${response.job_id}`);
```

## Real-time Updates

```typescript
const result = await client.runEvaluationWithUpdates(
  request,
  (job) => {
    console.log(`Progress: ${(job.progress * 100).toFixed(1)}% - Status: ${job.status}`);
  },
  (chatData) => {
    console.log(`${chatData.role}: ${chatData.content}`);
  }
);

console.log(`Final result: ${result.status}`);
```

## Advanced Examples

### React Hook

```typescript
import { useState, useCallback } from 'react';
import { createRogueClient, type RogueClientConfig } from '@rogue/sdk';

function useRogueEvaluation(config: RogueClientConfig) {
  const [client] = useState(() => createRogueClient(config));
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const evaluate = useCallback(
    async (agentUrl: string, scenarios: string[]) => {
      setIsEvaluating(true);
      setProgress(0);
      
      try {
        return await client.runEvaluationWithUpdates(
          {
            agent_config: {
              evaluated_agent_url: agentUrl,
              evaluated_agent_auth_type: 'no_auth',
              judge_llm: 'openai/gpt-4o-mini'
            },
            scenarios: scenarios.map(s => ({ scenario: s, scenario_type: 'policy' }))
          },
          (job) => setProgress(job.progress)
        );
      } finally {
        setIsEvaluating(false);
      }
    },
    [client]
  );
  
  return { evaluate, isEvaluating, progress };
}
```

### Express.js Route Handler

```typescript
import express from 'express';
import { quickEvaluate, type RogueClientConfig } from '@rogue/sdk';

const app = express();
const config: RogueClientConfig = { baseUrl: process.env.ROGUE_URL! };

app.post('/evaluate', async (req, res) => {
  try {
    const { agentUrl, scenarios } = req.body;
    
    // Clean, functional approach
    const result = await quickEvaluate(config, agentUrl, scenarios);
    
    res.json({
      success: true,
      jobId: result.job_id,
      status: result.status,
      results: result.results
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});
```

### Composition and Extension

```typescript
// Easy to compose and extend
function createEnhancedClient(config: RogueClientConfig) {
  const baseClient = createRogueClient(config);
  
  return {
    ...baseClient,
    
    // Add retry logic
    async quickEvaluateWithRetry(agentUrl: string, scenarios: string[], retries = 3) {
      for (let i = 0; i < retries; i++) {
        try {
          return await baseClient.quickEvaluate(agentUrl, scenarios);
        } catch (error) {
          if (i === retries - 1) throw error;
          await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
      }
    },
    
    // Add logging
    async createEvaluationWithLogging(request: EvaluationRequest) {
      console.log('Creating evaluation:', request.agent_config.evaluated_agent_url);
      const result = await baseClient.createEvaluation(request);
      console.log('Evaluation created:', result.job_id);
      return result;
    }
  };
}
```

## Testing

The functional approach makes testing much easier:

```typescript
import { quickEvaluate } from '@rogue/sdk';

// Mock individual functions
jest.mock('@rogue/sdk', () => ({
  quickEvaluate: jest.fn(),
}));

const mockQuickEvaluate = quickEvaluate as jest.MockedFunction<typeof quickEvaluate>;

test('should evaluate agent', async () => {
  mockQuickEvaluate.mockResolvedValue({
    job_id: 'test-job',
    status: 'completed',
    results: []
  });
  
  const result = await quickEvaluate(config, agentUrl, scenarios);
  expect(result.status).toBe('completed');
});
```

## License

MIT License - see LICENSE file for details.
