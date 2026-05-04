/**
 * Lightweight client for https://models.dev/api.json — same data the TUI uses
 * to populate its model picker (see packages/tui/internal/modelcache/).
 *
 * - 24h localStorage cache to avoid refetching on every dialog open
 * - Filters embeddings / codex / deep-research / -chat-latest aliases
 * - Sorts by release_date desc (newest first)
 */

import { useEffect, useState } from "react";

const API_URL = "https://models.dev/api.json";
const CACHE_KEY = "rogue:models-dev:v1";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

type ModalityList = string[];

interface ModelEntry {
  id: string;
  name?: string;
  family?: string;
  release_date?: string;
  modalities?: { input?: ModalityList; output?: ModalityList };
}

interface ProviderEntry {
  id: string;
  name?: string;
  models: Record<string, ModelEntry>;
}

type ApiResponse = Record<string, ProviderEntry>;

interface CachedShape {
  fetchedAt: number;
  byProvider: Record<string, string[]>;
}

const TARGET_PROVIDERS = ["openai", "anthropic", "google", "openrouter"] as const;

function isChatModel(m: ModelEntry): boolean {
  if (!(m.modalities?.output ?? []).includes("text")) return false;
  if ((m.family ?? "") === "text-embedding") return false;
  if (m.id.includes("embedding")) return false;
  if ((m.family ?? "").includes("codex")) return false;
  if (m.id.endsWith("-deep-research")) return false;
  if (m.id.endsWith("-chat-latest")) return false;
  return true;
}

function sortAndId(models: ModelEntry[]): string[] {
  const sorted = [...models].sort((a, b) => {
    const ad = a.release_date ?? "";
    const bd = b.release_date ?? "";
    if (ad !== bd) return ad < bd ? 1 : -1;
    return a.id < b.id ? -1 : 1;
  });
  return sorted.map((m) => m.id);
}

function processResponse(api: ApiResponse): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  for (const pid of TARGET_PROVIDERS) {
    const entry = api[pid];
    if (!entry) continue;
    const all = Object.values(entry.models);
    const filtered =
      pid === "openrouter"
        ? all.filter((m) => (m.modalities?.output ?? []).includes("text"))
        : all.filter(isChatModel);
    if (filtered.length > 0) out[pid] = sortAndId(filtered);
  }
  return out;
}

function readCache(): CachedShape | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as CachedShape;
  } catch {
    return null;
  }
}

function writeCache(value: CachedShape) {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(value));
  } catch {
    /* quota or private mode — ignore */
  }
}

async function fetchModelsDev(): Promise<Record<string, string[]>> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 15_000);
  try {
    const res = await fetch(API_URL, { signal: ctrl.signal });
    if (!res.ok) throw new Error(`models.dev returned ${res.status}`);
    const json = (await res.json()) as ApiResponse;
    return processResponse(json);
  } finally {
    clearTimeout(t);
  }
}

export interface RecommendedModelsResult {
  byProvider: Record<string, string[]>;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useRecommendedModels(): RecommendedModelsResult {
  const [byProvider, setByProvider] = useState<Record<string, string[]>>(
    () => readCache()?.byProvider ?? {},
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchModelsDev();
      setByProvider(data);
      writeCache({ fetchedAt: Date.now(), byProvider: data });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const cached = readCache();
    const stale = !cached || Date.now() - cached.fetchedAt > CACHE_TTL_MS;
    if (stale) {
      void refresh();
    }
  }, []);

  return { byProvider, loading, error, refresh };
}

/** Map our internal provider id → models.dev provider id. */
export function modelsDevProviderId(providerId: string): string | null {
  switch (providerId) {
    case "openai":
      return "openai";
    case "anthropic":
      return "anthropic";
    case "google":
      return "google";
    case "openrouter":
      return "openrouter";
    default:
      return null;
  }
}
