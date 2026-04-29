/**
 * Sync the Zustand config store with the server-side TOML the TUI uses
 * (``<UserConfigDir>/rogue/config.toml``).
 *
 * - On hydration, GET /api/v1/config and merge into the store. localStorage
 *   acts as the offline cache; the server is authoritative when reachable.
 * - On every store change, debounce 500 ms and PUT the snake_case payload
 *   back to the server so the TUI sees the same values on next launch.
 *
 * The server merges the payload into the existing TOML (keys not sent are
 * preserved), so we only need to send the fields we own.
 */

import { api, ApiError } from "@/api/client";
import { useConfig, type ConfigState, type Provider } from "@/stores/config";

interface ServerConfig {
  config: Record<string, unknown>;
  path: string;
}

const PROVIDERS: Provider[] = [
  "openai",
  "anthropic",
  "google",
  "aws-bedrock",
  "azure",
  "openrouter",
  "litellm",
];

function asProvider(value: unknown, fallback: Provider): Provider {
  return PROVIDERS.includes(value as Provider) ? (value as Provider) : fallback;
}

function asString(value: unknown): string | undefined {
  return typeof value === "string" && value.length > 0 ? value : undefined;
}

function asBool(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function asStringMap(value: unknown): Partial<Record<Provider, string>> {
  if (!value || typeof value !== "object") return {};
  const out: Partial<Record<Provider, string>> = {};
  for (const [key, v] of Object.entries(value as Record<string, unknown>)) {
    if (typeof v === "string" && PROVIDERS.includes(key as Provider)) {
      out[key as Provider] = v;
    }
  }
  return out;
}

/** Map TOML (snake_case) → Zustand (camelCase). */
function toZustand(server: Record<string, unknown>): Partial<ConfigState> {
  const draft: Partial<ConfigState> = {};
  const serverUrl = asString(server.server_url);
  if (serverUrl) draft.serverUrl = serverUrl;

  const apiKeys = asStringMap(server.api_keys);
  if (Object.keys(apiKeys).length) draft.apiKeys = apiKeys;
  const apiBases = asStringMap(server.api_bases);
  if (Object.keys(apiBases).length) draft.apiBases = apiBases;

  if (server.selected_provider !== undefined)
    draft.selectedProvider = asProvider(server.selected_provider, "openai");
  if (server.selected_model !== undefined)
    draft.selectedModel = asString(server.selected_model) ?? "openai/gpt-4o";

  if (server.judge_provider !== undefined)
    draft.judgeProvider = asProvider(server.judge_provider, "openai");
  if (server.judge_model !== undefined)
    draft.judgeModel = asString(server.judge_model) ?? "openai/gpt-4o";
  draft.judgeApiBase = asString(server.judge_api_base);

  if (server.attacker_provider !== undefined)
    draft.attackerProvider = asProvider(server.attacker_provider, "openai");
  if (server.attacker_model !== undefined)
    draft.attackerModel = asString(server.attacker_model) ?? "openai/gpt-4o";
  draft.attackerApiBase = asString(server.attacker_api_base);

  if (server.interview_provider !== undefined)
    draft.interviewProvider = asProvider(server.interview_provider, "openai");
  if (server.interview_model !== undefined)
    draft.interviewModel = asString(server.interview_model) ?? "openai/gpt-4o";
  draft.interviewApiBase = asString(server.interview_api_base);

  if (server.scenario_gen_provider !== undefined)
    draft.scenarioGenProvider = asProvider(server.scenario_gen_provider, "openai");
  if (server.scenario_gen_model !== undefined)
    draft.scenarioGenModel = asString(server.scenario_gen_model) ?? "openai/gpt-4o";
  draft.scenarioGenApiBase = asString(server.scenario_gen_api_base);

  const businessContext = asString(server.business_context);
  if (businessContext !== undefined) draft.businessContext = businessContext;

  draft.rogueSecurityEnabled = asBool(server.rogue_security_enabled, false);
  draft.rogueSecurityApiKey = asString(server.rogue_security_api_key);
  draft.rogueSecurityBaseUrl = asString(server.rogue_security_base_url);

  return draft;
}

/** Map Zustand (camelCase) → TOML (snake_case). */
function toToml(state: ConfigState): Record<string, unknown> {
  return {
    server_url: state.serverUrl,
    api_keys: state.apiKeys,
    api_bases: state.apiBases,
    selected_provider: state.selectedProvider,
    selected_model: state.selectedModel,
    judge_provider: state.judgeProvider,
    judge_model: state.judgeModel,
    judge_api_base: state.judgeApiBase ?? "",
    attacker_provider: state.attackerProvider,
    attacker_model: state.attackerModel,
    attacker_api_base: state.attackerApiBase ?? "",
    interview_provider: state.interviewProvider,
    interview_model: state.interviewModel,
    interview_api_base: state.interviewApiBase ?? "",
    scenario_gen_provider: state.scenarioGenProvider,
    scenario_gen_model: state.scenarioGenModel,
    scenario_gen_api_base: state.scenarioGenApiBase ?? "",
    business_context: state.businessContext ?? "",
    rogue_security_enabled: state.rogueSecurityEnabled,
    rogue_security_api_key: state.rogueSecurityApiKey ?? "",
    rogue_security_base_url: state.rogueSecurityBaseUrl ?? "",
  };
}

let started = false;
let pendingSaveTimer: number | null = null;
let suppressNextSave = false;
// Push gating: ``toToml`` always serialises the WHOLE state, including
// fields the user hasn't touched (their DEFAULTS). If we let pushes fire
// before the initial pull completes, we'd race with the server: the user
// changes one field, the debounced PUT sends DEFAULTS for every *other*
// field, and the server's previously-persisted values (from a TUI run or
// a prior session) get clobbered with the SPA's hard-coded defaults. The
// pull then resolves with the now-corrupted values and the UI snaps to
// them — looking exactly like the settings "didn't persist". Block all
// outbound pushes until pull has resolved (success OR failure) so the
// store is up-to-date with the authoritative server state first.
let initialPullSettled = false;

async function pullFromServer(): Promise<void> {
  try {
    const res = await api<ServerConfig>("/api/v1/config", { method: "GET" });
    const overlay = toZustand(res.config);
    if (Object.keys(overlay).length === 0) return;
    suppressNextSave = true;
    useConfig.setState(overlay);
  } catch (e) {
    if (e instanceof ApiError) {
      // Older server without the /config route — nothing to sync.
      if (e.status !== 404) {
        console.warn("config-sync: pull failed", e);
      }
    } else {
      console.warn("config-sync: pull failed", e);
    }
  } finally {
    initialPullSettled = true;
    // If the user managed to change something while we were fetching, the
    // subscriber tucked that intent into the debounce timer (or dropped
    // it). Either way we now flush eagerly: any pending edit reflects the
    // post-pull state (since the pull just finished) and is safe to push.
    if (pendingSaveTimer !== null) {
      window.clearTimeout(pendingSaveTimer);
      pendingSaveTimer = null;
      pushToServer();
    }
  }
}

function pushToServer(): void {
  const payload = toToml(useConfig.getState());
  // Best effort — failure is non-fatal, the local store stays valid.
  void api("/api/v1/config", { method: "PUT", body: payload }).catch((e) => {
    console.warn("config-sync: push failed", e);
  });
}

export function startConfigSync(): void {
  if (started) return;
  started = true;

  // Pull server → local first, then start watching for outbound changes.
  void pullFromServer();

  useConfig.subscribe(() => {
    if (suppressNextSave) {
      suppressNextSave = false;
      return;
    }
    if (pendingSaveTimer !== null) window.clearTimeout(pendingSaveTimer);
    pendingSaveTimer = window.setTimeout(() => {
      pendingSaveTimer = null;
      // Wait for the initial pull. If the user beat the network, defer
      // — pullFromServer's ``finally`` block will flush this push once
      // it has the authoritative state to merge against.
      if (!initialPullSettled) return;
      pushToServer();
    }, 500);
  });

  // Flush pending edits if the tab is being unloaded, so a quick
  // change-then-close doesn't lose the last value to the debounce timer.
  // ``pagehide`` fires for both navigation and bfcache; ``visibilitychange``
  // covers the mobile-Safari case where ``beforeunload`` is unreliable.
  const flushIfPending = () => {
    if (pendingSaveTimer === null) return;
    window.clearTimeout(pendingSaveTimer);
    pendingSaveTimer = null;
    if (initialPullSettled) pushToServer();
  };
  window.addEventListener("pagehide", flushIfPending);
  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flushIfPending();
  });
}
