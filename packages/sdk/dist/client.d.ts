/**
 * HTTP Client for Rogue Agent Evaluator API
 */
import { RogueClientConfig, EvaluationRequest, EvaluationResponse, EvaluationJob, JobListResponse, HealthResponse, EvaluationStatus } from './types';
export declare class RogueHttpClient {
    private baseUrl;
    private apiKey?;
    private timeout;
    private retries;
    constructor(config: RogueClientConfig);
    /**
     * Make HTTP request with retry logic
     */
    private request;
    /**
     * Check server health
     */
    health(): Promise<HealthResponse>;
    /**
     * Create a new evaluation job
     */
    createEvaluation(request: EvaluationRequest): Promise<EvaluationResponse>;
    /**
     * Get evaluation job by ID
     */
    getEvaluation(jobId: string): Promise<EvaluationJob>;
    /**
     * List evaluation jobs
     */
    listEvaluations(status?: EvaluationStatus, limit?: number, offset?: number): Promise<JobListResponse>;
    /**
     * Cancel evaluation job
     */
    cancelEvaluation(jobId: string): Promise<{
        message: string;
    }>;
    /**
     * Wait for evaluation to complete
     */
    waitForEvaluation(jobId: string, pollInterval?: number, maxWaitTime?: number): Promise<EvaluationJob>;
}
//# sourceMappingURL=client.d.ts.map
