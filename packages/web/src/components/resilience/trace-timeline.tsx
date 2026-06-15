import type { ResilienceReportTimelineEvent } from "@/api/types";
import {
  ResilienceEmptyPanel,
  ResilienceErrorPanel,
  ResilienceLoadingPanel,
} from "@/components/resilience/panel-states";
import { cn } from "@/lib/utils";

const EVENT_TONES: Record<string, string> = {
  baseline: "border-blue-500/40 bg-blue-500/10 text-blue-400",
  injection: "border-destructive/40 bg-destructive/10 text-destructive",
  message: "border-border/60 bg-muted/40 text-foreground",
  detection: "border-[var(--chart-2)]/40 bg-[var(--chart-2)]/10 text-[var(--chart-2)]",
  containment: "border-[var(--chart-3)]/40 bg-[var(--chart-3)]/10 text-[var(--chart-3)]",
  recovery: "border-emerald-500/40 bg-emerald-500/10 text-emerald-400",
  checkpoint: "border-violet-500/40 bg-violet-500/10 text-violet-400",
  error: "border-destructive/40 bg-destructive/10 text-destructive",
};

interface TraceTimelineProps {
  events: ResilienceReportTimelineEvent[];
  className?: string;
  maxItems?: number;
  loading?: boolean;
  error?: string | null;
}

export function TraceTimeline({
  events,
  className,
  maxItems,
  loading = false,
  error = null,
}: TraceTimelineProps) {
  if (loading) {
    return (
      <ResilienceLoadingPanel
        title="Loading trace events…"
        description="Fetching experiment timeline from the report."
      />
    );
  }

  if (error) {
    return (
      <ResilienceErrorPanel
        title="Trace unavailable"
        description={error}
      />
    );
  }

  const shown = maxItems ? events.slice(-maxItems) : events;
  if (shown.length === 0) {
    return (
      <ResilienceEmptyPanel
        title="No trace events yet"
        description="Events appear here during a live run or after the experiment completes."
      />
    );
  }

  return (
    <ol className={cn("space-y-2", className)}>
      {shown.map((event, i) => {
        const tone = EVENT_TONES[event.event_type] ?? EVENT_TONES.message;
        let detail = "";
        try {
          detail =
            event.event_type === "message"
              ? String(event.payload?.probe ?? event.payload?.response ?? "").slice(0, 120)
              : event.event_type === "checkpoint"
                ? `${event.payload?.operation ?? "checkpoint"}${event.payload?.success ? " ✓" : ""}`
                : "";
        } catch {
          detail = "";
        }
        let timeLabel = event.timestamp;
        try {
          timeLabel = new Date(event.timestamp).toLocaleTimeString();
        } catch {
          /* keep raw timestamp */
        }
        return (
          <li
            key={`${event.timestamp}-${event.event_type}-${i}`}
            className={cn("rounded-lg border px-3 py-2 text-xs", tone)}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="font-semibold uppercase tracking-wider">{event.label}</span>
              <span className="font-mono text-[10px] opacity-70">{event.agent_id}</span>
            </div>
            <div className="mt-1 flex flex-wrap gap-2 text-[10px] opacity-80">
              <span>{event.injector_id}</span>
              <span>{timeLabel}</span>
            </div>
            {detail && <p className="mt-1 truncate opacity-90">{detail}</p>}
          </li>
        );
      })}
    </ol>
  );
}

interface LiveTraceViewerProps {
  events: Array<{ kind: string; at: string; trace?: Record<string, unknown> }>;
  loading?: boolean;
  error?: string | null;
  waiting?: boolean;
}

/** Live experiment trace viewer for the job detail page. */
export function LiveTraceViewer({
  events,
  loading = false,
  error = null,
  waiting = false,
}: LiveTraceViewerProps) {
  const traceEvents = events
    .filter((e) => e.kind === "trace" && e.trace)
    .map((e) => {
      const t = e.trace!;
      const eventType = String(t.event_type ?? "message");
      return {
        timestamp: String(t.timestamp ?? e.at),
        experiment_id: "",
        injector_id: String(t.injector_id ?? ""),
        agent_id: String(t.agent_id ?? "default"),
        event_type: eventType,
        label: eventType.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        payload: (t.payload as Record<string, unknown>) ?? {},
      };
    });

  return (
    <div className="flex h-full min-h-0 flex-col rounded-xl border border-border/60 bg-card">
      <div className="border-b border-border/60 px-4 py-3">
        <h2 className="text-sm font-semibold">Live trace</h2>
        <p className="text-xs text-muted-foreground">
          {loading
            ? "Connecting to experiment stream…"
            : `${traceEvents.length} events streamed`}
        </p>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {loading ? (
          <ResilienceLoadingPanel
            title="Waiting for trace events…"
            description="The orchestrator streams baseline, injection, and recovery markers here."
          />
        ) : error ? (
          <ResilienceErrorPanel title="Live trace disconnected" description={error} />
        ) : waiting && traceEvents.length === 0 ? (
          <ResilienceEmptyPanel
            title="Experiment starting"
            description="Trace events will appear as injectors run against your agent."
          />
        ) : (
          <TraceTimeline events={traceEvents} />
        )}
      </div>
    </div>
  );
}
