"use strict";
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
exports.default = exports.RogueWebSocketClient = exports.RogueHttpClient = exports.getEvaluation = exports.createEvaluation = exports.quickEvaluate = exports.createRogueClient = void 0;
// Main functional API
var sdk_1 = require("./sdk");
Object.defineProperty(exports, "createRogueClient", { enumerable: true, get: function () { return sdk_1.createRogueClient; } });
Object.defineProperty(exports, "quickEvaluate", { enumerable: true, get: function () { return sdk_1.quickEvaluate; } });
Object.defineProperty(exports, "createEvaluation", { enumerable: true, get: function () { return sdk_1.createEvaluation; } });
Object.defineProperty(exports, "getEvaluation", { enumerable: true, get: function () { return sdk_1.getEvaluation; } });
// Low-level clients
var client_1 = require("./client");
Object.defineProperty(exports, "RogueHttpClient", { enumerable: true, get: function () { return client_1.RogueHttpClient; } });
var websocket_1 = require("./websocket");
Object.defineProperty(exports, "RogueWebSocketClient", { enumerable: true, get: function () { return websocket_1.RogueWebSocketClient; } });
// All types
__exportStar(require("./types"), exports);
// Default export
var sdk_2 = require("./sdk");
Object.defineProperty(exports, "default", { enumerable: true, get: function () { return sdk_2.createRogueClient; } });
//# sourceMappingURL=index.js.map
