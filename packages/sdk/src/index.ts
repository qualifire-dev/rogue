/**
 * Rogue Agent Evaluator TypeScript SDK
 * 
 * A comprehensive SDK for interacting with the Rogue Agent Evaluator API.
 * 
 * @example
 * ```typescript
 * import { RogueSDK, AuthType, ScenarioType } from '@rogue/sdk';
 * 
 * const client = new RogueSDK({
 *   baseUrl: 'http://localhost:8000'
 * });
 * 
 * // Quick evaluation
 * const result = await client.quickEvaluate(
 *   'http://localhost:3000',
 *   ['The agent should be polite', 'The agent should not give discounts']
 * );
 * 
 * // Evaluation with real-time updates
 * const job = await client.runEvaluationWithUpdates(
 *   {
 *     agent_config: {
 *       evaluated_agent_url: 'http://localhost:3000',
 *       evaluated_agent_auth_type: AuthType.NO_AUTH,
 *       judge_llm_model: 'openai/gpt-4o-mini'
 *     },
 *     scenarios: [{
 *       scenario: 'Test scenario',
 *       scenario_type: ScenarioType.POLICY
 *     }]
 *   },
 *   (job) => console.log('Job update:', job.status),
 *   (chat) => console.log('Chat update:', chat)
 * );
 * ```
 */

// Main SDK class
export { RogueSDK } from './sdk';

// HTTP and WebSocket clients
export { RogueHttpClient } from './client';
export { RogueWebSocketClient } from './websocket';

// All types
export * from './types';

// Default export
export { RogueSDK as default } from './sdk';
