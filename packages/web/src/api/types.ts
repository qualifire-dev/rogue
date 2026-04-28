// Hand-curated mirror of the FastAPI types used by the UI. Replace with
// generated `schema.d.ts` once `pnpm gen:api` is run against a live server.

export type Protocol = "a2a" | "mcp" | "python" | "openai_api";
export type Transport = "http" | "streamable_http" | "sse" | "chat_completions";
export type AuthType = "no_auth" | "api_key" | "bearer_token" | "basic";
export type ScanType = "basic" | "full" | "custom";
export type Severity = "critical" | "high" | "medium" | "low";
export type EvaluationStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface Scenario {
  scenario: string;
  scenario_type?: string;
  dataset?: string | null;
  expected_outcome?: string | null;
  multi_turn?: boolean;
  max_turns?: number;
}

export interface AgentConfig {
  // Server's AgentConfig uses unprefixed `protocol` / `transport`; only the
  // red-team request schema uses the `evaluated_agent_*` prefix.
  protocol: Protocol;
  transport?: Transport;
  evaluated_agent_url?: string;
  evaluated_agent_auth_type?: AuthType;
  evaluated_agent_credentials?: string;
  python_entrypoint_file?: string;
  judge_llm: string;
  judge_llm_api_key?: string;
  judge_llm_api_base?: string;
}

export interface EvaluationRequest {
  agent_config: AgentConfig;
  scenarios?: Scenario[];
  max_retries?: number;
  timeout_seconds?: number;
}

export interface EvaluationJob {
  job_id: string;
  status: EvaluationStatus;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  progress: number;
  request?: EvaluationRequest;
  results?: unknown[];
  evaluation_results?: EvaluationResultsPayload | null;
  judge_model?: string | null;
  /** Server-cached LLM summary, populated after the first /llm/summary call. */
  summary?: StructuredSummary | null;
}

export interface ConversationMessage {
  role: string;
  content: string;
  timestamp?: string | null;
}

export interface ConversationEvaluation {
  messages: { messages: ConversationMessage[] };
  passed: boolean;
  reason: string;
}

export interface ScenarioResult {
  scenario: Scenario;
  conversations: ConversationEvaluation[];
  passed: boolean;
}

export interface EvaluationResultsPayload {
  results?: ScenarioResult[];
  red_teaming_results?: unknown[] | null;
  owasp_summary?: Record<string, unknown> | null;
  vulnerability_scan_log?: unknown[] | null;
}

export interface JobListResponse {
  jobs: EvaluationJob[];
  total: number;
}

export interface RedTeamConfig {
  scan_type: ScanType;
  vulnerabilities: string[];
  attacks: string[];
  attacks_per_vulnerability: number;
  frameworks?: string[];
  random_seed?: number;
}

export interface RedTeamRequest {
  red_team_config: RedTeamConfig;
  evaluated_agent_url?: string;
  evaluated_agent_protocol: Protocol;
  evaluated_agent_transport?: Transport;
  evaluated_agent_auth_type?: AuthType;
  evaluated_agent_auth_credentials?: string;
  python_entrypoint_file?: string;
  judge_llm: string;
  judge_llm_api_key?: string;
  judge_llm_api_base?: string;
  attacker_llm: string;
  attacker_llm_api_key?: string;
  attacker_llm_api_base?: string;
  business_context?: string;
  rogue_security_api_key?: string;
  rogue_security_base_url?: string;
  max_retries?: number;
  timeout_seconds?: number;
}

export interface RedTeamJob {
  job_id: string;
  status: EvaluationStatus;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  progress: number;
  request?: RedTeamRequest;
  results?: unknown;
}

export interface RedTeamJobListResponse {
  jobs: RedTeamJob[];
  total: number;
}

export interface InterviewMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface StartInterviewResponse {
  session_id: string;
  initial_message: string;
  message: string;
}

export interface SendMessageResponse {
  session_id: string;
  response: string;
  is_complete: boolean;
  message_count: number;
}

export interface GetConversationResponse {
  session_id: string;
  messages: InterviewMessage[];
  is_complete: boolean;
  message_count: number;
}

export interface JobUpdate {
  status: EvaluationStatus;
  progress: number;
  started_at?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
}

export interface ChatUpdate {
  role: string;
  content: string;
}

export type WebSocketMessage =
  | { type: "job_update"; job_id: string; data: JobUpdate }
  | { type: "chat_update"; job_id: string; data: ChatUpdate }
  | { type: string; job_id: string; data: Record<string, unknown> };

export interface StructuredSummaryRow {
  scenario: string;
  status: string;
  outcome: string;
}

export interface StructuredSummary {
  overall_summary: string;
  key_findings: string[];
  recommendations: string[];
  detailed_breakdown?: StructuredSummaryRow[];
}

export interface SummaryGenerationResponse {
  summary: StructuredSummary;
  message: string;
}

// ─── Display labels ──────────────────────────────────────────────────────────

export const PROTOCOL_LABELS: Record<Protocol, string> = {
  a2a: "A2A",
  mcp: "MCP",
  python: "Python",
  openai_api: "OpenAI API",
};

export const TRANSPORT_LABELS: Record<Transport, string> = {
  http: "HTTP",
  streamable_http: "Streamable HTTP",
  sse: "SSE",
  chat_completions: "Chat Completions",
};

export const AUTH_TYPE_LABELS: Record<AuthType, string> = {
  no_auth: "No auth",
  api_key: "API key",
  bearer_token: "Bearer token",
  basic: "Basic (user:pass)",
};

export const SCAN_TYPE_LABELS: Record<ScanType, string> = {
  basic: "Basic",
  full: "Full",
  custom: "Custom",
};
