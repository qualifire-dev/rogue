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
  business_context?: string;
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

export interface RedTeamConversationMessage {
  role: string;
  content: string;
  [k: string]: unknown;
}

/** Judge verdict on a single attack attempt. */
export interface RedTeamAttackEvaluation {
  vulnerability_detected: boolean;
  severity?: string | null;
  /** Free-text reasoning from the judge / metric — what we render under each
   * conversation, mirroring `ConversationEvaluation.reason` on the eval side. */
  reason?: string | null;
  [k: string]: unknown;
}

/** One round-trip of attack → response → judge verdict from the orchestrator. */
export interface RedTeamConversationRecord {
  vulnerability_id: string;
  attack_id: string;
  attempt: number;
  session_id?: string | null;
  is_multi_turn?: boolean;
  is_premium?: boolean;
  turn?: number;
  message: string;
  response: string;
  evaluation: RedTeamAttackEvaluation;
}

/** Subset of the server's RedTeamResults that the SPA reads. */
export interface RedTeamResultsPayload {
  total_vulnerabilities_tested?: number;
  total_vulnerabilities_found?: number;
  overall_score?: number;
  conversations?: RedTeamConversationRecord[];
  vulnerability_results?: Array<{
    vulnerability_id: string;
    vulnerability_name: string;
    passed: boolean;
    severity?: string | null;
  }>;
  [k: string]: unknown;
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
  results?: RedTeamResultsPayload | null;
  // Captured chat-update events from the orchestrator (server appends each
  // one as the scan runs so the report's Conversations tab has data even
  // after a server restart). Used for the LIVE view; the structured
  // `results.conversations` is what the report renders post-completion.
  conversations?: RedTeamConversationMessage[];
}

// Shape of GET /api/v1/red-team/{id}/report (server's tui_formatter.format_for_tui).
export interface RedTeamReportSeverityCounts {
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  total_vulnerabilities_tested: number;
  total_vulnerabilities_found: number;
  overall_score: number;
  severity_colors?: Record<string, string>;
}

export interface RedTeamReportKeyFinding {
  vulnerability_id: string;
  vulnerability_name: string;
  cvss_score: number;
  severity: string | null;
  summary: string;
  attack_ids: string[];
  success_rate: number;
  color?: string;
}

export interface RedTeamReportVulnerabilityRow {
  vulnerability_id: string;
  vulnerability_name: string;
  severity: string | null;
  attacks_used: string[];
  attacks_attempted: number;
  attacks_successful: number;
  success_rate: number;
  passed: boolean;
  color?: string;
  status_icon?: string;
}

export interface RedTeamReportFrameworkCard {
  framework_id: string;
  framework_name: string;
  compliance_score: number;
  tested_count: number;
  total_count: number;
  passed_count: number;
  status: string;
  color?: string;
  icon?: string;
}

export interface RedTeamReport {
  metadata: {
    scan_date?: string | null;
    scan_type?: string | null;
    frameworks_tested?: string[];
    attacks_used?: string[];
    random_seed?: number | null;
  };
  highlights: RedTeamReportSeverityCounts;
  key_findings: RedTeamReportKeyFinding[];
  vulnerability_table: RedTeamReportVulnerabilityRow[];
  framework_coverage: RedTeamReportFrameworkCard[];
  export_paths?: {
    conversations_csv?: string | null;
    summary_csv?: string | null;
  };
}

export interface RedTeamJobListResponse {
  jobs: RedTeamJob[];
  total: number;
}

export interface InterviewMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ScenarioGenerationRequest {
  business_context: string;
  model: string;
  api_key?: string;
  api_base?: string;
  count?: number;
}

export interface ScenarioGenerationResponse {
  scenarios: { scenarios: Scenario[] };
  message: string;
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
