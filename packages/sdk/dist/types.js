"use strict";
/**
 * TypeScript types for Rogue Agent Evaluator API
 *
 * These types mirror the Pydantic models from the FastAPI server.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.EvaluationStatus = exports.ScenarioType = exports.AuthType = void 0;
// Enums
var AuthType;
(function (AuthType) {
    AuthType["NO_AUTH"] = "no_auth";
    AuthType["API_KEY"] = "api_key";
    AuthType["BEARER_TOKEN"] = "bearer_token";
    AuthType["BASIC_AUTH"] = "basic";
})(AuthType || (exports.AuthType = AuthType = {}));
var ScenarioType;
(function (ScenarioType) {
    ScenarioType["POLICY"] = "policy";
    ScenarioType["PROMPT_INJECTION"] = "prompt_injection";
})(ScenarioType || (exports.ScenarioType = ScenarioType = {}));
var EvaluationStatus;
(function (EvaluationStatus) {
    EvaluationStatus["PENDING"] = "pending";
    EvaluationStatus["RUNNING"] = "running";
    EvaluationStatus["COMPLETED"] = "completed";
    EvaluationStatus["FAILED"] = "failed";
    EvaluationStatus["CANCELLED"] = "cancelled";
})(EvaluationStatus || (exports.EvaluationStatus = EvaluationStatus = {}));
//# sourceMappingURL=types.js.map
