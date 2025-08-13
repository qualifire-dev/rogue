"use strict";
/**
 * HTTP Client for Rogue Agent Evaluator API
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.RogueHttpClient = void 0;
const types_1 = require("./types");
class RogueHttpClient {
    constructor(config) {
        this.baseUrl = config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
        this.apiKey = config.apiKey;
        this.timeout = config.timeout || 30000; // 30 seconds default
        this.retries = config.retries || 3;
    }
    /**
     * Make HTTP request with retry logic
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };
        if (this.apiKey) {
            headers['Authorization'] = `Bearer ${this.apiKey}`;
        }
        const requestOptions = {
            ...options,
            headers,
            signal: AbortSignal.timeout(this.timeout)
        };
        let lastError;
        for (let attempt = 1; attempt <= this.retries; attempt++) {
            try {
                const response = await fetch(url, requestOptions);
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`HTTP ${response.status}: ${errorText}`);
                }
                const data = await response.json();
                return data;
            }
            catch (error) {
                lastError = error;
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
    async health() {
        return this.request('/api/v1/health');
    }
    /**
     * Create a new evaluation job
     */
    async createEvaluation(request) {
        return this.request('/api/v1/evaluations', {
            method: 'POST',
            body: JSON.stringify(request)
        });
    }
    /**
     * Get evaluation job by ID
     */
    async getEvaluation(jobId) {
        return this.request(`/api/v1/evaluations/${jobId}`);
    }
    /**
     * List evaluation jobs
     */
    async listEvaluations(status, limit = 50, offset = 0) {
        const params = new URLSearchParams();
        if (status)
            params.append('status', status);
        params.append('limit', limit.toString());
        params.append('offset', offset.toString());
        const query = params.toString();
        const endpoint = `/api/v1/evaluations${query ? `?${query}` : ''}`;
        return this.request(endpoint);
    }
    /**
     * Cancel evaluation job
     */
    async cancelEvaluation(jobId) {
        return this.request(`/api/v1/evaluations/${jobId}`, {
            method: 'DELETE'
        });
    }
    /**
     * Wait for evaluation to complete
     */
    async waitForEvaluation(jobId, pollInterval = 2000, maxWaitTime = 300000 // 5 minutes
    ) {
        const startTime = Date.now();
        while (Date.now() - startTime < maxWaitTime) {
            const job = await this.getEvaluation(jobId);
            if (job.status === types_1.EvaluationStatus.COMPLETED ||
                job.status === types_1.EvaluationStatus.FAILED ||
                job.status === types_1.EvaluationStatus.CANCELLED) {
                return job;
            }
            await new Promise(resolve => setTimeout(resolve, pollInterval));
        }
        throw new Error(`Evaluation ${jobId} did not complete within ${maxWaitTime}ms`);
    }
}
exports.RogueHttpClient = RogueHttpClient;
//# sourceMappingURL=client.js.map
