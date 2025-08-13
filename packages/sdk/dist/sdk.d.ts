/**
 * Functional TypeScript SDK for Rogue Agent Evaluator
 *
 * More idiomatic TypeScript approach using factory functions
 * instead of classes.
 */
import { RogueClientConfig, EvaluationRequest, EvaluationResponse, EvaluationJob, JobListResponse, HealthResponse, EvaluationStatus, AuthType } from './types';
export interface RogueClient {
    readonly config: RogueClientConfig;
    health(): Promise<HealthResponse>;
    createEvaluation(request: EvaluationRequest): Promise<EvaluationResponse>;
    getEvaluation(jobId: string): Promise<EvaluationJob>;
    listEvaluations(status?: EvaluationStatus, limit?: number, offset?: number): Promise<JobListResponse>;
    cancelEvaluation(jobId: string): Promise<{
        message: string;
    }>;
    waitForEvaluation(jobId: string, pollInterval?: number, maxWaitTime?: number): Promise<EvaluationJob>;
    runEvaluationWithUpdates(request: EvaluationRequest, onUpdate?: (job: EvaluationJob) => void, onChat?: (chatData: any) => void): Promise<EvaluationJob>;
    quickEvaluate(agentUrl: string, scenarios: string[], options?: {
        judgeModel?: string;
        authType?: AuthType;
        authCredentials?: string;
        deepTest?: boolean;
    }): Promise<EvaluationJob>;
}
/**
 * Create a Rogue client instance
 */
export declare function createRogueClient(config: RogueClientConfig): RogueClient;
export declare function quickEvaluate(config: RogueClientConfig, agentUrl: string, scenarios: string[], options?: {
    judgeModel?: string;
    authType?: AuthType;
    authCredentials?: string;
    deepTest?: boolean;
}): Promise<EvaluationJob>;
export declare function createEvaluation(config: RogueClientConfig, request: EvaluationRequest): Promise<EvaluationResponse>;
export declare function getEvaluation(config: RogueClientConfig, jobId: string): Promise<EvaluationJob>;
export * from './types';
export { RogueHttpClient } from './client';
export { RogueWebSocketClient } from './websocket';
//# sourceMappingURL=sdk.d.ts.map
