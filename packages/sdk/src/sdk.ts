/**
 * Main Rogue Agent Evaluator SDK
 * 
 * Combines HTTP client and WebSocket client for complete functionality.
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
  WebSocketEventType,
  WebSocketEventHandler,
  AgentConfig,
  Scenario,
  AuthType,
  ScenarioType
} from './types';

export class RogueSDK {
  private httpClient: RogueHttpClient;
  private wsClient?: RogueWebSocketClient;

  constructor(config: RogueClientConfig) {
    this.httpClient = new RogueHttpClient(config);
  }

  // HTTP Client Methods
  
  /**
   * Check server health
   */
  async health(): Promise<HealthResponse> {
    return this.httpClient.health();
  }

  /**
   * Create and start an evaluation job
   */
  async createEvaluation(request: EvaluationRequest): Promise<EvaluationResponse> {
    return this.httpClient.createEvaluation(request);
  }

  /**
   * Get evaluation job details
   */
  async getEvaluation(jobId: string): Promise<EvaluationJob> {
    return this.httpClient.getEvaluation(jobId);
  }

  /**
   * List evaluation jobs
   */
  async listEvaluations(
    status?: EvaluationStatus,
    limit?: number,
    offset?: number
  ): Promise<JobListResponse> {
    return this.httpClient.listEvaluations(status, limit, offset);
  }

  /**
   * Cancel evaluation job
   */
  async cancelEvaluation(jobId: string): Promise<{ message: string }> {
    return this.httpClient.cancelEvaluation(jobId);
  }

  /**
   * Wait for evaluation to complete (polling)
   */
  async waitForEvaluation(
    jobId: string,
    pollInterval?: number,
    maxWaitTime?: number
  ): Promise<EvaluationJob> {
    return this.httpClient.waitForEvaluation(jobId, pollInterval, maxWaitTime);
  }

  // WebSocket Methods

  /**
   * Connect to WebSocket for real-time updates
   */
  async connectWebSocket(jobId?: string): Promise<void> {
    if (this.wsClient) {
      this.wsClient.disconnect();
    }

    const baseUrl = this.httpClient['baseUrl']; // Access private property
    this.wsClient = new RogueWebSocketClient(baseUrl, jobId);
    await this.wsClient.connect();
  }

  /**
   * Disconnect WebSocket
   */
  disconnectWebSocket(): void {
    if (this.wsClient) {
      this.wsClient.disconnect();
      this.wsClient = undefined;
    }
  }

  /**
   * Add WebSocket event handler
   */
  onWebSocketEvent(event: WebSocketEventType, handler: WebSocketEventHandler): void {
    if (!this.wsClient) {
      throw new Error('WebSocket not connected. Call connectWebSocket() first.');
    }
    this.wsClient.on(event, handler);
  }

  /**
   * Remove WebSocket event handler
   */
  offWebSocketEvent(event: WebSocketEventType, handler: WebSocketEventHandler): void {
    if (this.wsClient) {
      this.wsClient.off(event, handler);
    }
  }

  /**
   * Check if WebSocket is connected
   */
  get isWebSocketConnected(): boolean {
    return this.wsClient?.isConnected || false;
  }

  // High-level convenience methods

  /**
   * Run evaluation with real-time updates
   */
  async runEvaluationWithUpdates(
    request: EvaluationRequest,
    onUpdate?: (job: EvaluationJob) => void,
    onChat?: (chatData: any) => void
  ): Promise<EvaluationJob> {
    // Create evaluation
    const response = await this.createEvaluation(request);
    const jobId = response.job_id;

    // Connect WebSocket for updates
    await this.connectWebSocket(jobId);

    return new Promise((resolve, reject) => {
      // Set up event handlers
      this.onWebSocketEvent('job_update', (event, data) => {
        if (onUpdate) {
          onUpdate(data);
        }

        // Check if job is complete
        if (data.status === EvaluationStatus.COMPLETED ||
            data.status === EvaluationStatus.FAILED ||
            data.status === EvaluationStatus.CANCELLED) {
          this.disconnectWebSocket();
          resolve(data);
        }
      });

      if (onChat) {
        this.onWebSocketEvent('chat_update', (event, data) => {
          onChat(data);
        });
      }

      this.onWebSocketEvent('error', (event, data) => {
        this.disconnectWebSocket();
        reject(new Error(`WebSocket error: ${data.error}`));
      });

      // Set timeout
      setTimeout(() => {
        this.disconnectWebSocket();
        reject(new Error('Evaluation timed out'));
      }, 300000); // 5 minutes
    });
  }

  /**
   * Quick evaluation helper
   */
  async quickEvaluate(
    agentUrl: string,
    scenarios: string[],
    options: {
      judgeModel?: string;
      authType?: AuthType;
      authCredentials?: string;
      deepTest?: boolean;
    } = {}
  ): Promise<EvaluationJob> {
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

    const response = await this.createEvaluation(request);
    return this.waitForEvaluation(response.job_id);
  }
}
