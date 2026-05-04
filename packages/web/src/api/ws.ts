import { useEffect, useReducer, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { wsUrlFor } from "./client";
import { qk } from "./queries";
import type { ChatUpdate, EvaluationJob, JobUpdate, RedTeamJob, WebSocketMessage } from "./types";

export type ConnectionState = "connecting" | "open" | "closed" | "polling";

/**
 * Which TanStack Query cache key the live stream's WS updates should patch.
 * The hook is shared between the evaluation and red-team detail pages, but
 * the two have separate query keys (`qk.evaluation` vs `qk.redTeam`); writing
 * to the wrong one leaves the other page reading stale cached state and
 * misses the auto-redirect to /report on terminal status.
 */
export type JobStreamKind = "evaluation" | "red-team";

export type TimelineEvent =
  | { kind: "status"; at: string; update: JobUpdate }
  | { kind: "chat"; at: string; chat: ChatUpdate };

interface State {
  connection: ConnectionState;
  events: TimelineEvent[];
  latest: JobUpdate | null;
  attempts: number;
}

type Action =
  | { type: "connect" }
  | { type: "open" }
  | { type: "status"; update: JobUpdate }
  | { type: "chat"; chat: ChatUpdate }
  | { type: "close" }
  | { type: "polling" };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "connect":
      return { ...state, connection: "connecting", attempts: state.attempts + 1 };
    case "open":
      return { ...state, connection: "open", attempts: 0 };
    case "status": {
      const last = state.events[state.events.length - 1];
      const now = new Date().toISOString();
      // Coalesce repeated status events that don't change state.
      if (
        last &&
        last.kind === "status" &&
        last.update.status === action.update.status &&
        last.update.progress === action.update.progress &&
        last.update.error_message === action.update.error_message
      ) {
        return { ...state, latest: action.update };
      }
      const event: TimelineEvent = { kind: "status", at: now, update: action.update };
      return {
        ...state,
        latest: action.update,
        events: state.events.length > 5000 ? state.events : [...state.events, event],
      };
    }
    case "chat": {
      const event: TimelineEvent = {
        kind: "chat",
        at: new Date().toISOString(),
        chat: action.chat,
      };
      return {
        ...state,
        events: state.events.length > 5000 ? state.events : [...state.events, event],
      };
    }
    case "close":
      return { ...state, connection: "closed" };
    case "polling":
      return { ...state, connection: "polling" };
  }
}

const BACKOFF_MS = [200, 500, 1000, 2000, 5000];

export function useJobStream(jobId: string | undefined, kind: JobStreamKind = "evaluation") {
  const qc = useQueryClient();
  const [state, dispatch] = useReducer(reducer, {
    connection: "closed",
    events: [],
    latest: null,
    attempts: 0,
  });
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const pollTimeoutRef = useRef<number | null>(null);
  // `state.attempts` from the reducer is captured by closure on the first
  // effect run and never updates, so reading it inside `ws.onclose` always
  // sees zero — the backoff stays at 200 ms forever, hammering the server
  // on flapping connections. Track attempts in a ref instead.
  const attemptsRef = useRef(0);

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;
    // Reset attempts when (jobId, kind) changes — otherwise stale counts
    // from the previous job inflate the backoff for the new one.
    attemptsRef.current = 0;

    // Resolve the cache key once per (jobId, kind). The two job-detail pages
    // store their job under separate keys; writing to the wrong one leaves the
    // calling page reading stale data and breaks the auto-redirect on
    // terminal status.
    const queryKey = kind === "red-team" ? qk.redTeam(jobId) : qk.evaluation(jobId);

    const patchCache = (update: JobUpdate) => {
      // If the GET hasn't seeded the cache yet, drop the WS update — the
      // imminent fetch will produce a complete job object. Constructing a
      // fake stub here would set required fields (`request`, `progress`)
      // to undefined and crash any downstream code that dereferences them
      // (e.g. `job.request.red_team_config?.scan_type`).
      if (kind === "red-team") {
        qc.setQueryData<RedTeamJob | undefined>(queryKey, (prev) =>
          prev ? { ...prev, ...update } : prev,
        );
      } else {
        qc.setQueryData<EvaluationJob | undefined>(queryKey, (prev) =>
          prev ? { ...prev, ...update } : prev,
        );
      }
    };

    const startPolling = () => {
      dispatch({ type: "polling" });
      const tick = async () => {
        if (cancelled) return;
        await qc.invalidateQueries({ queryKey });
        pollTimeoutRef.current = window.setTimeout(tick, 2000);
      };
      tick();
    };

    const connect = () => {
      if (cancelled) return;
      dispatch({ type: "connect" });
      const url = wsUrlFor(`/api/v1/ws/${jobId}`);
      let opened = false;

      const failOver = window.setTimeout(() => {
        if (!opened) startPolling();
      }, 5000);

      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          opened = true;
          // Successful connect → next disconnect starts from the smallest
          // backoff. Without this reset, repeated drops keep escalating
          // even after stretches of stable connectivity.
          attemptsRef.current = 0;
          window.clearTimeout(failOver);
          dispatch({ type: "open" });
        };
        ws.onmessage = (e) => {
          if (typeof e.data !== "string") return; // ignore binary keepalive pings
          try {
            const msg = JSON.parse(e.data) as WebSocketMessage;
            if (msg.type === "job_update" && msg.data) {
              const update = msg.data as JobUpdate;
              dispatch({ type: "status", update });
              patchCache(update);
              // Terminal status: pull the full job from the server so the
              // cached entry includes terminal-only payload (evaluation
              // `evaluation_results` / red-team `results` + `conversations`)
              // that the WS update doesn't carry. Skip the invalidate when
              // the cached job was *already* terminal — a tab that
              // re-mounts on a long-finished job hits this WS-replay path
              // and would otherwise refetch on every visit.
              if (
                update.status === "completed" ||
                update.status === "failed" ||
                update.status === "cancelled"
              ) {
                const cached = qc.getQueryData<{ status?: string } | undefined>(queryKey);
                const wasTerminal =
                  cached?.status === "completed" ||
                  cached?.status === "failed" ||
                  cached?.status === "cancelled";
                if (!wasTerminal) {
                  qc.invalidateQueries({ queryKey });
                }
              }
            } else if (msg.type === "chat_update" && msg.data) {
              const chat = msg.data as ChatUpdate;
              if (typeof chat.content === "string" && chat.content.length > 0) {
                dispatch({ type: "chat", chat });
              }
            }
          } catch {
            /* ignore non-JSON keepalives */
          }
        };
        ws.onclose = () => {
          window.clearTimeout(failOver);
          dispatch({ type: "close" });
          if (!cancelled) {
            const idx = Math.min(attemptsRef.current, BACKOFF_MS.length - 1);
            const delay = BACKOFF_MS[idx] ?? BACKOFF_MS[BACKOFF_MS.length - 1] ?? 5000;
            attemptsRef.current += 1;
            reconnectTimeoutRef.current = window.setTimeout(connect, delay);
          }
        };
        ws.onerror = () => {
          ws.close();
        };
      } catch {
        startPolling();
      }
    };

    connect();

    return () => {
      cancelled = true;
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeoutRef.current) window.clearTimeout(reconnectTimeoutRef.current);
      if (pollTimeoutRef.current) window.clearTimeout(pollTimeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId]);

  return state;
}
