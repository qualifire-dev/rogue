/**
 * HTTP Client for Rogue Agent Evaluator API
 */

import {
  RogueClientConfig,
  EvaluationRequest,
  EvaluationResponse,
  EvaluationJob,
  JobListResponse,
  HealthResponse,
  EvaluationStatus
} from './types';

export class RogueHttpClient {
  private baseUrl: string;
  private apiKey?: string;
  private timeout: number;
  private retries: number;

  constructor(config: RogueClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000; // 30 seconds default
    this.retries = config.retries || 3;
  }

  /**
   * Make HTTP request with retry logic
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...((options.headers as Record<string, string>) || {})
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const requestOptions: RequestInit = {
      ...options,
      headers,
      signal: AbortSignal.timeout(this.timeout)
    };

    let lastError: Error;

    for (let attempt = 1; attempt <= this.retries; attempt++) {
      try {
        const response = await fetch(url, requestOptions);
        
        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        return data as T;
      } catch (error) {
        lastError = error as Error;
        
        if (attempt === this.retries) {
          break;
        }

        // Exponential backoff
        const delay = Math.pow(2, attempt - 1) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }

    throw new Error(`Request failed after ${this.retries} attempts: ${lastError.message}`);
  }

  /**
   * Check server health
   */
  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/v1/health');
  }

  /**
   * Create a new evaluation job
   */
  async createEvaluation(request: EvaluationRequest): Promise<EvaluationResponse> {
    return this.request<EvaluationResponse>('/api/v1/evaluations', {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  /**
   * Get evaluation job by ID
   */
  async getEvaluation(jobId: string): Promise<EvaluationJob> {
    return this.request<EvaluationJob>(`/api/v1/evaluations/${jobId}`);
  }

  /**
   * List evaluation jobs
   */
  async listEvaluations(
    status?: EvaluationStatus,
    limit: number = 50,
    offset: number = 0
  ): Promise<JobListResponse> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const query = params.toString();
    const endpoint = `/api/v1/evaluations${query ? `?${query}` : ''}`;
    
    return this.request<JobListResponse>(endpoint);
  }

  /**
   * Cancel evaluation job
   */
  async cancelEvaluation(jobId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/v1/evaluations/${jobId}`, {
      method: 'DELETE'
    });
  }

  /**
   * Wait for evaluation to complete
   */
  async waitForEvaluation(
    jobId: string,
    pollInterval: number = 2000,
    maxWaitTime: number = 300000 // 5 minutes
  ): Promise<EvaluationJob> {
    const startTime = Date.now();
    
    while (Date.now() - startTime < maxWaitTime) {
      const job = await this.getEvaluation(jobId);
      
      if (job.status === EvaluationStatus.COMPLETED || 
          job.status === EvaluationStatus.FAILED || 
          job.status === EvaluationStatus.CANCELLED) {
        return job;
      }

      await new Promise(resolve => setTimeout(resolve, pollInterval));
    }

    throw new Error(`Evaluation ${jobId} did not complete within ${maxWaitTime}ms`);
  }
}
