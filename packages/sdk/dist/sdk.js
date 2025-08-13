"use strict";
/**
 * Functional TypeScript SDK for Rogue Agent Evaluator
 *
 * More idiomatic TypeScript approach using factory functions
 * instead of classes.
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RogueWebSocketClient = exports.RogueHttpClient = void 0;
exports.createRogueClient = createRogueClient;
exports.quickEvaluate = quickEvaluate;
exports.createEvaluation = createEvaluation;
exports.getEvaluation = getEvaluation;
const client_1 = require("./client");
const websocket_1 = require("./websocket");
const types_1 = require("./types");
/**
 * Create a Rogue client instance
 */
function createRogueClient(config) {
    const httpClient = new client_1.RogueHttpClient(config);
    let wsClient = null;
    return {
        config,
        async health() {
            return httpClient.health();
        },
        async createEvaluation(request) {
            return httpClient.createEvaluation(request);
        },
        async getEvaluation(jobId) {
            return httpClient.getEvaluation(jobId);
        },
        async listEvaluations(status, limit, offset) {
            return httpClient.listEvaluations(status, limit, offset);
        },
        async cancelEvaluation(jobId) {
            return httpClient.cancelEvaluation(jobId);
        },
        async waitForEvaluation(jobId, pollInterval, maxWaitTime) {
            return httpClient.waitForEvaluation(jobId, pollInterval, maxWaitTime);
        },
        async runEvaluationWithUpdates(request, onUpdate, onChat) {
            // Create evaluation
            const response = await httpClient.createEvaluation(request);
            const jobId = response.job_id;
            // Connect WebSocket for updates
            if (wsClient) {
                wsClient.disconnect();
            }
            wsClient = new websocket_1.RogueWebSocketClient(config.baseUrl, jobId);
            await wsClient.connect();
            return new Promise((resolve, reject) => {
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
                    if (data.status === types_1.EvaluationStatus.COMPLETED ||
                        data.status === types_1.EvaluationStatus.FAILED ||
                        data.status === types_1.EvaluationStatus.CANCELLED) {
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
        async quickEvaluate(agentUrl, scenarios, options = {}) {
            const agentConfig = {
                evaluated_agent_url: agentUrl,
                evaluated_agent_auth_type: options.authType || types_1.AuthType.NO_AUTH,
                evaluated_agent_credentials: options.authCredentials,
                judge_llm_model: options.judgeModel || 'openai/gpt-4o-mini',
                deep_test_mode: options.deepTest || false,
                interview_mode: true,
                parallel_runs: 1
            };
            const scenarioObjects = scenarios.map(scenario => ({
                scenario,
                scenario_type: types_1.ScenarioType.POLICY
            }));
            const request = {
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
async function quickEvaluate(config, agentUrl, scenarios, options) {
    const client = createRogueClient(config);
    return client.quickEvaluate(agentUrl, scenarios, options);
}
async function createEvaluation(config, request) {
    const client = createRogueClient(config);
    return client.createEvaluation(request);
}
async function getEvaluation(config, jobId) {
    const client = createRogueClient(config);
    return client.getEvaluation(jobId);
}
// Export everything for flexibility
__exportStar(require("./types"), exports);
var client_2 = require("./client");
Object.defineProperty(exports, "RogueHttpClient", { enumerable: true, get: function () { return client_2.RogueHttpClient; } });
var websocket_2 = require("./websocket");
Object.defineProperty(exports, "RogueWebSocketClient", { enumerable: true, get: function () { return websocket_2.RogueWebSocketClient; } });
//# sourceMappingURL=sdk.js.map
