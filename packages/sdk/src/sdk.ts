/**
 * Functional TypeScript SDK for Rogue Agent Evaluator
 * 
 * More idiomatic TypeScript approach using factory functions
 * instead of classes.
 */

import { RogueHttpClient } from './client';
import { RogueWebSocketClient } from './websocket';
import {
  RogueClientConfig,
  EvaluationRequest,
  EvaluationResponse,
  EvaluationJob,
  JobListResponse,
  HealthResponse,
  EvaluationStatus,
  AgentConfig,
  Scenario,
  AuthType,
  ScenarioType
} from './types';

// Core client interface
export interface RogueClient {
  readonly config: RogueClientConfig;
  health(): Promise<HealthResponse>;
  createEvaluation(request: EvaluationRequest): Promise<EvaluationResponse>;
  getEvaluation(jobId: string): Promise<EvaluationJob>;
  listEvaluations(status?: EvaluationStatus, limit?: number, offset?: number): Promise<JobListResponse>;
  cancelEvaluation(jobId: string): Promise<{ message: string }>;
  waitForEvaluation(jobId: string, pollInterval?: number, maxWaitTime?: number): Promise<EvaluationJob>;
  runEvaluationWithUpdates(
    request: EvaluationRequest,
    onUpdate?: (job: EvaluationJob) => void,
    onChat?: (chatData: any) => void
  ): Promise<EvaluationJob>;
  quickEvaluate(
    agentUrl: string,
    scenarios: string[],
    options?: {
      judgeModel?: string;
      authType?: AuthType;
      authCredentials?: string;
      deepTest?: boolean;
    }
  ): Promise<EvaluationJob>;
}

/**
 * Create a Rogue client instance
 */
export function createRogueClient(config: RogueClientConfig): RogueClient {
  const httpClient = new RogueHttpClient(config);
  let wsClient: RogueWebSocketClient | null = null;

  return {
    config,

    async health() {
      return httpClient.health();
    },

    async createEvaluation(request: EvaluationRequest) {
      return httpClient.createEvaluation(request);
    },

    async getEvaluation(jobId: string) {
      return httpClient.getEvaluation(jobId);
    },

    async listEvaluations(status?: EvaluationStatus, limit?: number, offset?: number) {
      return httpClient.listEvaluations(status, limit, offset);
    },

    async cancelEvaluation(jobId: string) {
      return httpClient.cancelEvaluation(jobId);
    },

    async waitForEvaluation(jobId: string, pollInterval?: number, maxWaitTime?: number) {
      return httpClient.waitForEvaluation(jobId, pollInterval, maxWaitTime);
    },

    async runEvaluationWithUpdates(
      request: EvaluationRequest,
      onUpdate?: (job: EvaluationJob) => void,
      onChat?: (chatData: any) => void
    ) {
      // Create evaluation
      const response = await httpClient.createEvaluation(request);
      const jobId = response.job_id;

      // Connect WebSocket for updates
      if (wsClient) {
        wsClient.disconnect();
      }
      wsClient = new RogueWebSocketClient(config.baseUrl, jobId);
      await wsClient.connect();

      return new Promise<EvaluationJob>((resolve, reject) => {
        if (!wsClient) {
          reject(new Error('WebSocket connection failed'));
          return;
        }

        // Set up event handlers
        wsClient.on('job_update', (event, data) => {
          if (onUpdate) {
            onUpdate(data);
          }

          // Check if job is complete
          if (data.status === EvaluationStatus.COMPLETED ||
              data.status === EvaluationStatus.FAILED ||
              data.status === EvaluationStatus.CANCELLED) {
            wsClient?.disconnect();
            wsClient = null;
            resolve(data);
          }
        });

        if (onChat) {
          wsClient.on('chat_update', (event, data) => {
            onChat(data);
          });
        }

        wsClient.on('error', (event, data) => {
          wsClient?.disconnect();
          wsClient = null;
          reject(new Error(`WebSocket error: ${data.error}`));
        });

        // Set timeout
        setTimeout(() => {
          wsClient?.disconnect();
          wsClient = null;
          reject(new Error('Evaluation timed out'));
        }, 300000); // 5 minutes
      });
    },

    async quickEvaluate(
      agentUrl: string,
      scenarios: string[],
      options: {
        judgeModel?: string;
        authType?: AuthType;
        authCredentials?: string;
        deepTest?: boolean;
      } = {}
    ) {
      const agentConfig: AgentConfig = {
        evaluated_agent_url: agentUrl,
        evaluated_agent_auth_type: options.authType || AuthType.NO_AUTH,
        evaluated_agent_credentials: options.authCredentials,
        judge_llm_model: options.judgeModel || 'openai/gpt-4o-mini',
        deep_test_mode: options.deepTest || false,
        interview_mode: true,
        parallel_runs: 1
      };

      const scenarioObjects: Scenario[] = scenarios.map(scenario => ({
        scenario,
        scenario_type: ScenarioType.POLICY
      }));

      const request: EvaluationRequest = {
        agent_config: agentConfig,
        scenarios: scenarioObjects,
        max_retries: 3,
        timeout_seconds: 300
      };

      const response = await httpClient.createEvaluation(request);
      return httpClient.waitForEvaluation(response.job_id);
    }
  };
}

// Convenience functions for one-off operations
export async function quickEvaluate(
  config: RogueClientConfig,
  agentUrl: string,
  scenarios: string[],
  options?: {
    judgeModel?: string;
    authType?: AuthType;
    authCredentials?: string;
    deepTest?: boolean;
  }
): Promise<EvaluationJob> {
  const client = createRogueClient(config);
  return client.quickEvaluate(agentUrl, scenarios, options);
}

export async function createEvaluation(
  config: RogueClientConfig,
  request: EvaluationRequest
): Promise<EvaluationResponse> {
  const client = createRogueClient(config);
  return client.createEvaluation(request);
}

export async function getEvaluation(
  config: RogueClientConfig,
  jobId: string
): Promise<EvaluationJob> {
  const client = createRogueClient(config);
  return client.getEvaluation(jobId);
}

// Export everything for flexibility
export * from './types';
export { RogueHttpClient } from './client';
export { RogueWebSocketClient } from './websocket';
