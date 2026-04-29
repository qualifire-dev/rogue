import { create } from "zustand";
import { persist } from "zustand/middleware";

import { DEFAULT_TARGET_AGENT_VALUE, type TargetAgentValue } from "@/components/target-agent-form";

export type Provider =
  | "openai"
  | "anthropic"
  | "google"
  | "aws-bedrock"
  | "azure"
  | "openrouter"
  | "litellm";

export interface ModelChoice {
  provider: Provider;
  model: string;
  apiKey?: string;
  apiBase?: string;
}

export interface ConfigState {
  serverUrl: string;
  apiKeys: Partial<Record<Provider, string>>;
  apiBases: Partial<Record<Provider, string>>;

  // Per-role model configuration (each can target a different provider/model).
  judgeProvider: Provider;
  judgeModel: string;
  judgeApiBase?: string;

  attackerProvider: Provider;
  attackerModel: string;
  attackerApiBase?: string;

  interviewProvider: Provider;
  interviewModel: string;
  interviewApiBase?: string;

  scenarioGenProvider: Provider;
  scenarioGenModel: string;
  scenarioGenApiBase?: string;

  // Legacy aliases — referenced by older components, kept for compatibility.
  selectedProvider: Provider;
  selectedModel: string;

  /**
   * Free-text description of what the agent does, who its users are, and the
   * policy boundaries. Threaded through to eval/red-team `business_context`
   * on submit and pre-fed into the scenario generator. Persisted so users
   * don't have to retype it on every run.
   */
  businessContext: string;

  rogueSecurityEnabled: boolean;
  rogueSecurityApiKey?: string;
  rogueSecurityBaseUrl?: string;

  /**
   * Last-used target agent config per page. Persisted so the user doesn't
   * have to re-enter the URL / protocol / auth on every reload — see
   * ``setLastEvaluationAgent`` / ``setLastRedTeamAgent`` (called on
   * successful submit).
   */
  lastEvaluationAgent: TargetAgentValue;
  lastRedTeamAgent: TargetAgentValue;

  setServerUrl: (url: string) => void;
  setApiKey: (provider: Provider, key: string) => void;
  setApiBase: (provider: Provider, base: string) => void;
  setSelectedProvider: (p: Provider) => void;
  setSelectedModel: (m: string) => void;

  setJudgeProvider: (p: Provider) => void;
  setJudgeModel: (m: string) => void;
  setJudgeApiBase: (b: string | undefined) => void;

  setAttackerProvider: (p: Provider) => void;
  setAttackerModel: (m: string) => void;
  setAttackerApiBase: (b: string | undefined) => void;

  setInterviewProvider: (p: Provider) => void;
  setInterviewModel: (m: string) => void;
  setInterviewApiBase: (b: string | undefined) => void;

  setScenarioGenProvider: (p: Provider) => void;
  setScenarioGenModel: (m: string) => void;
  setScenarioGenApiBase: (b: string | undefined) => void;

  setBusinessContext: (ctx: string) => void;
  setRogueSecurity: (enabled: boolean, apiKey?: string, baseUrl?: string) => void;

  setLastEvaluationAgent: (v: TargetAgentValue) => void;
  setLastRedTeamAgent: (v: TargetAgentValue) => void;

  reset: () => void;
}

const DEFAULTS = {
  serverUrl: "http://127.0.0.1:8000",
  apiKeys: {} as Partial<Record<Provider, string>>,
  apiBases: {} as Partial<Record<Provider, string>>,

  judgeProvider: "openai" as Provider,
  judgeModel: "openai/gpt-4o",
  judgeApiBase: undefined as string | undefined,

  attackerProvider: "openai" as Provider,
  attackerModel: "openai/gpt-4o",
  attackerApiBase: undefined as string | undefined,

  interviewProvider: "openai" as Provider,
  interviewModel: "openai/gpt-4o",
  interviewApiBase: undefined as string | undefined,

  scenarioGenProvider: "openai" as Provider,
  scenarioGenModel: "openai/gpt-4o",
  scenarioGenApiBase: undefined as string | undefined,

  selectedProvider: "openai" as Provider,
  selectedModel: "openai/gpt-4o",

  businessContext: "",

  rogueSecurityEnabled: false,
  rogueSecurityApiKey: undefined as string | undefined,
  rogueSecurityBaseUrl: undefined as string | undefined,

  lastEvaluationAgent: { ...DEFAULT_TARGET_AGENT_VALUE },
  lastRedTeamAgent: { ...DEFAULT_TARGET_AGENT_VALUE },
};

export const useConfig = create<ConfigState>()(
  persist(
    (set) => ({
      ...DEFAULTS,
      setServerUrl: (serverUrl) => set({ serverUrl }),
      setApiKey: (provider, key) => set((s) => ({ apiKeys: { ...s.apiKeys, [provider]: key } })),
      setApiBase: (provider, base) =>
        set((s) => ({ apiBases: { ...s.apiBases, [provider]: base } })),
      setSelectedProvider: (selectedProvider) => set({ selectedProvider }),
      setSelectedModel: (selectedModel) => set({ selectedModel }),

      setJudgeProvider: (judgeProvider) => set({ judgeProvider }),
      setJudgeModel: (judgeModel) => set({ judgeModel }),
      setJudgeApiBase: (judgeApiBase) => set({ judgeApiBase }),

      setAttackerProvider: (attackerProvider) => set({ attackerProvider }),
      setAttackerModel: (attackerModel) => set({ attackerModel }),
      setAttackerApiBase: (attackerApiBase) => set({ attackerApiBase }),

      setInterviewProvider: (interviewProvider) => set({ interviewProvider }),
      setInterviewModel: (interviewModel) => set({ interviewModel }),
      setInterviewApiBase: (interviewApiBase) => set({ interviewApiBase }),

      setScenarioGenProvider: (scenarioGenProvider) => set({ scenarioGenProvider }),
      setScenarioGenModel: (scenarioGenModel) => set({ scenarioGenModel }),
      setScenarioGenApiBase: (scenarioGenApiBase) => set({ scenarioGenApiBase }),

      setBusinessContext: (businessContext) => set({ businessContext }),
      setRogueSecurity: (rogueSecurityEnabled, rogueSecurityApiKey, rogueSecurityBaseUrl) =>
        set({ rogueSecurityEnabled, rogueSecurityApiKey, rogueSecurityBaseUrl }),

      setLastEvaluationAgent: (lastEvaluationAgent) => set({ lastEvaluationAgent }),
      setLastRedTeamAgent: (lastRedTeamAgent) => set({ lastRedTeamAgent }),

      reset: () => set(DEFAULTS),
    }),
    { name: "rogue:config:v1" },
  ),
);
