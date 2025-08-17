/**
 * Rogue Agent Evaluator TypeScript SDK
 * 
 * A functional TypeScript SDK for interacting with the Rogue Agent Evaluator API.
 * 
 * @example Factory function approach
 * ```typescript
 * import { createRogueClient } from '@rogue/sdk';
 * 
 * const client = createRogueClient({ baseUrl: 'http://localhost:8000' });
 * const result = await client.quickEvaluate(agentUrl, scenarios);
 * 
 * // Destructuring works perfectly
 * const { quickEvaluate, createEvaluation } = client;
 * await quickEvaluate(agentUrl, scenarios);
 * ```
 * 
 * @example Pure functions approach
 * ```typescript
 * import { quickEvaluate, createEvaluation } from '@rogue/sdk';
 * 
 * const config = { baseUrl: 'http://localhost:8000' };
 * const result = await quickEvaluate(config, agentUrl, scenarios);
 * ```
 * 
 * @example Real-time updates
 * ```typescript
 * const client = createRogueClient(config);
 * 
 * const result = await client.runEvaluationWithUpdates(
 *   request,
 *   (job) => console.log(`Progress: ${(job.progress * 100).toFixed(1)}%`),
 *   (chat) => console.log(`Chat: ${chat.content}`)
 * );
 * ```
 */

// Main functional API
export { 
  createRogueClient, 
  quickEvaluate, 
  createEvaluation, 
  getEvaluation,
  type RogueClient 
} from './sdk';

// Low-level clients
export { RogueHttpClient } from './client';
export { RogueWebSocketClient } from './websocket';

// All types
export * from './types';

// Default export
export { createRogueClient as default } from './sdk';
