import type { Provider } from "@/stores/config";

export interface ProviderInfo {
  id: Provider;
  name: string;
  description: string;
  /** Suggested models — user can also type a custom model id. */
  models: string[];
  /** Field schema for the credential step. */
  fields: ProviderField[];
  /** Format for the model id the server expects (litellm convention). */
  modelPrefix: string;
}

export interface ProviderField {
  key:
    | "apiKey"
    | "apiBase"
    | "awsAccessKeyId"
    | "awsSecretAccessKey"
    | "awsRegion"
    | "azureEndpoint"
    | "azureApiVersion"
    | "azureDeployment";
  label: string;
  type: "password" | "text";
  required: boolean;
  placeholder?: string;
}

export const PROVIDERS: ProviderInfo[] = [
  {
    id: "openai",
    name: "OpenAI",
    description: "Direct OpenAI API",
    modelPrefix: "openai/",
    models: [
      "openai/gpt-4o",
      "openai/gpt-4o-mini",
      "openai/gpt-4-turbo",
      "openai/o1",
      "openai/o1-mini",
      "openai/o3-mini",
    ],
    fields: [
      { key: "apiKey", label: "API key", type: "password", required: true, placeholder: "sk-…" },
      {
        key: "apiBase",
        label: "Base URL",
        type: "text",
        required: false,
        placeholder: "https://api.openai.com/v1 (optional)",
      },
    ],
  },
  {
    id: "anthropic",
    name: "Anthropic",
    description: "Claude models",
    modelPrefix: "anthropic/",
    models: [
      "anthropic/claude-opus-4-7",
      "anthropic/claude-sonnet-4-6",
      "anthropic/claude-haiku-4-5",
      "anthropic/claude-3-5-sonnet-latest",
    ],
    fields: [
      {
        key: "apiKey",
        label: "API key",
        type: "password",
        required: true,
        placeholder: "sk-ant-…",
      },
      {
        key: "apiBase",
        label: "Base URL",
        type: "text",
        required: false,
        placeholder: "https://api.anthropic.com (optional)",
      },
    ],
  },
  {
    id: "google",
    name: "Google",
    description: "Gemini models via AI Studio / Vertex",
    modelPrefix: "gemini/",
    models: ["gemini/gemini-2.5-pro", "gemini/gemini-2.5-flash", "gemini/gemini-2.0-flash"],
    fields: [
      { key: "apiKey", label: "API key", type: "password", required: true, placeholder: "AIza…" },
    ],
  },
  {
    id: "aws-bedrock",
    name: "AWS Bedrock",
    description: "Claude / Llama / Titan via Bedrock",
    modelPrefix: "bedrock/",
    models: [
      "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
      "bedrock/anthropic.claude-3-haiku-20240307-v1:0",
      "bedrock/meta.llama3-1-70b-instruct-v1:0",
    ],
    fields: [
      {
        key: "awsAccessKeyId",
        label: "Access key ID",
        type: "text",
        required: true,
        placeholder: "AKIA…",
      },
      { key: "awsSecretAccessKey", label: "Secret access key", type: "password", required: true },
      { key: "awsRegion", label: "Region", type: "text", required: true, placeholder: "us-east-1" },
    ],
  },
  {
    id: "azure",
    name: "Azure OpenAI",
    description: "OpenAI models hosted on Azure",
    modelPrefix: "azure/",
    models: ["azure/gpt-4o", "azure/gpt-4o-mini"],
    fields: [
      { key: "apiKey", label: "API key", type: "password", required: true },
      {
        key: "azureEndpoint",
        label: "Endpoint",
        type: "text",
        required: true,
        placeholder: "https://<name>.openai.azure.com",
      },
      {
        key: "azureApiVersion",
        label: "API version",
        type: "text",
        required: true,
        placeholder: "2024-08-01-preview",
      },
      {
        key: "azureDeployment",
        label: "Deployment",
        type: "text",
        required: true,
        placeholder: "gpt-4o",
      },
    ],
  },
  {
    id: "openrouter",
    name: "OpenRouter",
    description: "Unified access to 100+ models",
    modelPrefix: "openrouter/",
    models: [
      "openrouter/anthropic/claude-3.5-sonnet",
      "openrouter/openai/gpt-4o",
      "openrouter/meta-llama/llama-3.1-405b-instruct",
    ],
    fields: [
      { key: "apiKey", label: "API key", type: "password", required: true, placeholder: "sk-or-…" },
      {
        key: "apiBase",
        label: "Base URL",
        type: "text",
        required: false,
        placeholder: "https://openrouter.ai/api/v1 (optional)",
      },
    ],
  },
  {
    id: "litellm",
    name: "LiteLLM Proxy",
    description: "Self-hosted LiteLLM proxy",
    modelPrefix: "",
    models: [],
    fields: [
      {
        key: "apiBase",
        label: "Base URL",
        type: "text",
        required: true,
        placeholder: "http://localhost:4000",
      },
      { key: "apiKey", label: "API key", type: "password", required: false },
    ],
  },
];

export function findProvider(id: Provider): ProviderInfo {
  const p = PROVIDERS.find((x) => x.id === id);
  return p ?? PROVIDERS[0]!;
}
