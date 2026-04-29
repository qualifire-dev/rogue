import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";
import type {
  EvaluationJob,
  EvaluationRequest,
  GetConversationResponse,
  JobListResponse,
  RedTeamJob,
  RedTeamJobListResponse,
  RedTeamReport,
  RedTeamRequest,
  ScenarioGenerationRequest,
  ScenarioGenerationResponse,
  SendMessageResponse,
  StartInterviewResponse,
  SummaryGenerationResponse,
} from "./types";

export const qk = {
  health: () => ["health"] as const,
  evaluations: (filters?: Record<string, unknown>) => ["evaluations", filters] as const,
  evaluation: (jobId: string) => ["evaluations", jobId] as const,
  redTeams: (filters?: Record<string, unknown>) => ["red-team", filters] as const,
  redTeam: (jobId: string) => ["red-team", jobId] as const,
  redTeamReport: (jobId: string) => ["red-team", jobId, "report"] as const,
  interviewConversation: (sessionId: string) => ["interview", sessionId, "conversation"] as const,
};

export function useHealth() {
  return useQuery({
    queryKey: qk.health(),
    queryFn: () => api<{ status: string; timestamp: string }>("/api/v1/health"),
    refetchInterval: 30_000,
  });
}

export function useEvaluations() {
  return useQuery({
    queryKey: qk.evaluations(),
    queryFn: () => api<JobListResponse>("/api/v1/evaluations?limit=50"),
    refetchInterval: 5_000,
  });
}

export function useEvaluation(jobId: string | undefined) {
  return useQuery({
    queryKey: qk.evaluation(jobId ?? ""),
    queryFn: () => api<EvaluationJob>(`/api/v1/evaluations/${jobId}`),
    enabled: !!jobId,
    // The WS stream patches status/progress into this cache entry but never
    // populates `evaluation_results` (terminal payload only lives on the GET).
    // Force a refetch on every mount so /report always reads a fresh job.
    staleTime: 0,
    refetchOnMount: "always",
  });
}

export function useStartEvaluation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: EvaluationRequest) =>
      api<{ job_id: string; status: string; message?: string }>("/api/v1/evaluations", {
        body: req,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evaluations"] }),
  });
}

export function useCancelEvaluation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) =>
      api<{ message: string }>(`/api/v1/evaluations/${jobId}`, {
        method: "DELETE",
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evaluations"] }),
  });
}

export function useRedTeamJobs() {
  return useQuery({
    queryKey: qk.redTeams(),
    queryFn: () => api<RedTeamJobListResponse>("/api/v1/red-team?limit=50"),
    refetchInterval: 5_000,
  });
}

export function useRedTeamJob(jobId: string | undefined) {
  return useQuery({
    queryKey: qk.redTeam(jobId ?? ""),
    queryFn: () => api<RedTeamJob>(`/api/v1/red-team/${jobId}`),
    enabled: !!jobId,
    // Mirror useEvaluation: WS patches don't carry results / conversations,
    // so always refetch on mount to surface the post-completion data.
    staleTime: 0,
    refetchOnMount: "always",
  });
}

export function useRedTeamReport(jobId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: qk.redTeamReport(jobId ?? ""),
    queryFn: () => api<RedTeamReport>(`/api/v1/red-team/${jobId}/report`),
    enabled: !!jobId && enabled,
    staleTime: 30_000,
  });
}

export function useStartRedTeam() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: RedTeamRequest) =>
      api<{ job_id: string; status: string; message?: string }>("/api/v1/red-team", {
        body: req,
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["red-team"] }),
  });
}

export interface GenerateSummaryArgs {
  job_id: string;
  results: unknown;
  model: string;
  api_key?: string;
  api_base?: string;
  judge_model?: string;
  rogue_security_api_key?: string;
  rogue_security_base_url?: string;
}

export function useGenerateSummary() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: GenerateSummaryArgs) =>
      api<SummaryGenerationResponse>("/api/v1/llm/summary", { body }),
    // Server now persists the summary on the job, so refresh that cache
    // entry — future report visits will read it without re-mutating.
    onSuccess: (_data, vars) => qc.invalidateQueries({ queryKey: qk.evaluation(vars.job_id) }),
  });
}

export function useGenerateScenarios() {
  return useMutation({
    mutationFn: (body: ScenarioGenerationRequest) =>
      api<ScenarioGenerationResponse>("/api/v1/llm/scenarios", { body }),
  });
}

export function useStartInterview() {
  return useMutation({
    mutationFn: (body: { business_context?: string; model?: string; api_key?: string }) =>
      api<StartInterviewResponse>("/api/v1/interview/start", { body }),
  });
}

export function useSendInterviewMessage() {
  return useMutation({
    mutationFn: (body: { session_id: string; message: string }) =>
      api<SendMessageResponse>("/api/v1/interview/message", { body }),
  });
}

export function useDeleteInterviewSession() {
  return useMutation({
    mutationFn: (sessionId: string) =>
      api<{ message: string }>(`/api/v1/interview/session/${sessionId}`, {
        method: "DELETE",
      }),
  });
}

export function useInterviewConversation(sessionId: string | undefined) {
  return useQuery({
    queryKey: qk.interviewConversation(sessionId ?? ""),
    queryFn: () => api<GetConversationResponse>(`/api/v1/interview/conversation/${sessionId}`),
    enabled: !!sessionId,
  });
}
