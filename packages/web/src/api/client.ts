import { useConfig } from "@/stores/config";

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  signal?: AbortSignal;
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getServerUrl(): string {
  return useConfig.getState().serverUrl.replace(/\/$/, "");
}

export async function api<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const url = `${getServerUrl()}${path}`;
  const res = await fetch(url, {
    method: opts.method ?? (opts.body ? "POST" : "GET"),
    headers: opts.body ? { "content-type": "application/json" } : undefined,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    signal: opts.signal,
  });

  if (!res.ok) {
    let detail: unknown = undefined;
    try {
      detail = await res.json();
    } catch {
      try {
        detail = await res.text();
      } catch {
        /* ignore */
      }
    }
    throw new ApiError(res.status, `${res.status} ${res.statusText}`, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export function wsUrlFor(path: string): string {
  const base = getServerUrl();
  const wsBase = base.replace(/^http/, "ws");
  return `${wsBase}${path}`;
}
