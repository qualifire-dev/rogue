#!/usr/bin/env node
"use strict";
/*
 A small CLI that uses the SDK to start an evaluation and streams NDJSON events
 to stdout for consumption by the Go TUI.

 Usage:
   node dist/scripts/eval-runner.js \
     --server-url=http://localhost:8000 \
     --agent-url=http://localhost:3000 \
     --judge-model=openai/gpt-4o-mini \
     --parallel-runs=1 \
     --scenarios-path=.rogue/scenarios.json \
     [--auth-type=no_auth|api_key|bearer_token|basic] \
     [--auth-credentials=...]
*/
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const sdk_1 = require("../sdk");
function parseArgs(argv) {
    const args = {};
    for (const a of argv.slice(2)) {
        const m = a.match(/^--([^=]+)=(.*)$/);
        if (m) {
            args[m[1]] = m[2];
        }
    }
    return args;
}
function println(obj) {
    process.stdout.write(JSON.stringify(obj) + '\n');
}
function toAuthType(v) {
    switch ((v || 'no_auth').toLowerCase()) {
        case 'api_key':
            return sdk_1.AuthType.API_KEY;
        case 'bearer_token':
            return sdk_1.AuthType.BEARER_TOKEN;
        case 'basic':
            return sdk_1.AuthType.BASIC_AUTH;
        default:
            return sdk_1.AuthType.NO_AUTH;
    }
}
function readScenarios(p) {
    const full = path_1.default.resolve(process.cwd(), p);
    const data = fs_1.default.readFileSync(full, 'utf-8');
    const json = JSON.parse(data);
    if (Array.isArray(json)) {
        // assume array of strings
        return json;
    }
    if (json && Array.isArray(json.scenarios)) {
        const items = json.scenarios;
        return items.map((s) => (typeof s === 'string' ? s : (s.scenario ?? ''))).filter(Boolean);
    }
    return [];
}
async function main() {
    const args = parseArgs(process.argv);
    const baseUrl = args['server-url'] || process.env.ROGUE_URL || 'http://localhost:8000';
    const agentUrl = args['agent-url'] || 'http://localhost:3000';
    const judgeModel = args['judge-model'] || 'openai/gpt-4o-mini';
    const scenariosPath = args['scenarios-path'] || path_1.default.join('.rogue', 'scenarios.json');
    const parallelRuns = Math.max(1, parseInt(args['parallel-runs'] || '1', 10));
    const authType = toAuthType(args['auth-type']);
    const authCredentials = args['auth-credentials'];
    const deepTest = (args['deep-test'] || 'false').toLowerCase() === 'true';
    try {
        const client = (0, sdk_1.createRogueClient)({ baseUrl });
        const health = await client.health();
        println({ type: 'health', status: health.status });
        const scenarioStrings = readScenarios(scenariosPath);
        if (scenarioStrings.length === 0) {
            println({ type: 'error', message: 'No scenarios found' });
            process.exit(2);
            return;
        }
        const agentConfig = {
            evaluated_agent_url: agentUrl,
            evaluated_agent_auth_type: authType,
            evaluated_agent_credentials: authCredentials,
            judge_llm_model: judgeModel,
            deep_test_mode: deepTest,
            interview_mode: true,
            parallel_runs: parallelRuns,
        };
        const scenarios = scenarioStrings.map((s) => ({ scenario: s, scenario_type: sdk_1.ScenarioType.POLICY }));
        const request = {
            agent_config: agentConfig,
            scenarios,
            max_retries: 3,
            timeout_seconds: 600,
        };
        println({ type: 'start', total: scenarios.length, parallelRuns });
        const result = await client.runEvaluationWithUpdates(request, (job) => {
            println({ type: 'status', status: job.status, progress: job.progress ?? 0 });
        }, (chat) => {
            // chat shape is server-defined; forward role/content
            println({ type: 'chat', role: chat.role, content: chat.content });
        });
        println({ type: 'eval', status: result.status, resultsCount: result.results?.length ?? 0 });
        process.exit(0);
    }
    catch (err) {
        println({ type: 'error', message: err?.message || String(err) });
        process.exit(1);
    }
}
main();
//# sourceMappingURL=eval-runner.js.map
