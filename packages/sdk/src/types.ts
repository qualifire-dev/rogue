/**
 * TypeScript types for Rogue Agent Evaluator API
 * 
 * These types mirror the Pydantic models from the FastAPI server.
 */

// Enums
export enum AuthType {
  NO_AUTH = "no_auth",
  API_KEY = "api_key",
  BEARER_TOKEN = "bearer_token",
  BASIC_AUTH = "basic"
}

export enum ScenarioType {
  POLICY = "policy",
  PROMPT_INJECTION = "prompt_injection"
}

export enum EvaluationStatus {
  PENDING = "pending",
  RUNNING = "running",
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled"
}

// Core Models
export interface AgentConfig {
  evaluated_agent_url: string;
  evaluated_agent_auth_type: AuthType;
  evaluated_agent_credentials?: string;
  service_llm?: string;
  judge_llm_model: string;
  interview_mode?: boolean;
  deep_test_mode?: boolean;
  parallel_runs?: number;
  judge_llm_api_key?: string;
}

export interface Scenario {
  scenario: string;
  scenario_type: ScenarioType;
  dataset?: string;
  expected_outcome?: string;
  dataset_sample_size?: number;
}

export interface ChatMessage {
  role: string;
  content: string;
  timestamp?: string;
}

export interface ConversationEvaluation {
  messages: ChatMessage[];
  passed: boolean;
  reason: string;
}

export interface EvaluationResult {
  scenario: Scenario;
  conversations: ConversationEvaluation[];
  passed: boolean;
}

// API Request/Response Models
export interface EvaluationRequest {
  agent_config: AgentConfig;
  scenarios: Scenario[];
  max_retries?: number;
  timeout_seconds?: number;
}

export interface EvaluationJob {
  job_id: string;
  status: EvaluationStatus;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  request: EvaluationRequest;
  results?: EvaluationResult[];
  error_message?: string;
  progress: number;
}

export interface EvaluationResponse {
  job_id: string;
  status: EvaluationStatus;
  message: string;
}

export interface JobListResponse {
  jobs: EvaluationJob[];
  total: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  python_version: string;
  platform: string;
}

// WebSocket Messages
export interface WebSocketMessage {
  type: string;
  job_id: string;
  data: Record<string, any>;
}

// SDK Configuration
export interface RogueClientConfig {
  baseUrl: string;
  apiKey?: string;
  timeout?: number;
  retries?: number;
}

// Event Types for WebSocket
export type WebSocketEventType = 
  | "job_update"
  | "chat_update"
  | "error"
  | "connected"
  | "disconnected";

export interface WebSocketEventHandler {
  (event: WebSocketEventType, data: any): void;
}
