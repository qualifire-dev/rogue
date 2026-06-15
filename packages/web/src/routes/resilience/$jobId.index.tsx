import { Navigate, createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { type ReactNode } from "react";

import { LiveTraceViewer } from "@/components/resilience/trace-timeline";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useResilienceJob } from "@/api/queries";
import { useJobStream } from "@/api/ws";
import { cn, formatRelative } from "@/lib/utils";
import { StatusBadge } from "@/routes/index";

export const Route = createFileRoute("/resilience/$jobId/")({
  component: ResilienceDetailPage,
});

function ResilienceDetailPage() {
  const { jobId } = Route.useParams();
  const job = useResilienceJob(jobId);
  const stream = useJobStream(jobId, "resilience");

  const status = job.data?.status;
  const isTerminal = status === "completed" || status === "failed" || status === "cancelled";
  const streamError =
    stream.connection === "closed" && !isTerminal
      ? "WebSocket disconnected. Reconnecting or falling back to polling…"
      : job.data?.error_message ?? null;

  if (job.isLoading && !job.data) {
    return <LoadingShell />;
  }
  if (isTerminal) {
    return <Navigate to="/resilience/$jobId/report" params={{ jobId }} replace />;
  }

  const traceCount = stream.events.filter((e) => e.kind === "trace").length;

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            <span className="text-muted-foreground">Resilience</span>{" "}
            <span className="font-mono text-base">{jobId.slice(0, 12)}…</span>
          </h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Created {formatRelative(job.data?.created_at)} · Architecture{" "}
            {job.data?.request?.resilience_config?.architecture ?? "—"}
          </p>
        </div>
        <ConnectionPill state={stream.connection} />
      </div>

      <ProgressBar value={stream.latest?.progress ?? job.data?.progress ?? 0} />

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[2fr_1fr]">
        <LiveTraceViewer
          events={stream.events}
          loading={job.isLoading}
          error={streamError}
          waiting={!isTerminal && stream.events.filter((e) => e.kind === "trace").length === 0}
        />
        <ProgressRail
          status={(stream.latest?.status ?? job.data?.status) as string | undefined}
          startedAt={stream.latest?.started_at ?? job.data?.started_at}
          completedAt={stream.latest?.completed_at ?? job.data?.completed_at}
          error={stream.latest?.error_message ?? job.data?.error_message}
          traceCount={traceCount}
          injectors={job.data?.request?.resilience_config?.injectors ?? []}
        />
      </div>
    </div>
  );
}

function LoadingShell() {
  return (
    <div className="space-y-4">
      <div className="h-6 w-48 animate-pulse rounded-md bg-muted/60" />
      <div className="h-1 w-full animate-pulse rounded-full bg-muted/60" />
      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="h-[28rem] animate-pulse rounded-xl bg-muted/40" />
        <div className="h-[28rem] animate-pulse rounded-xl bg-muted/40" />
      </div>
    </div>
  );
}

function ProgressBar({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(1, value)) * 100;
  return (
    <div className="h-1 w-full overflow-hidden rounded-full bg-muted">
      <motion.div
        className="h-full bg-primary"
        initial={false}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      />
    </div>
  );
}

function ConnectionPill({ state }: { state: string }) {
  const tone =
    state === "open"
      ? "bg-[var(--chart-2)] text-white"
      : state === "polling"
        ? "bg-[var(--chart-3)] text-black"
        : state === "connecting"
          ? "bg-muted text-muted-foreground"
          : "bg-destructive text-destructive-foreground";
  return (
    <span
      className={cn(
        "rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        tone,
      )}
    >
      {state}
    </span>
  );
}

function ProgressRail({
  status,
  startedAt,
  completedAt,
  error,
  traceCount,
  injectors,
}: {
  status?: string;
  startedAt?: string | null;
  completedAt?: string | null;
  error?: string | null;
  traceCount: number;
  injectors: string[];
}) {
  return (
    <Card className="flex h-full min-h-0 flex-col">
      <CardHeader>
        <CardTitle className="text-sm">Status</CardTitle>
      </CardHeader>
      <CardContent className="min-h-0 flex-1 space-y-4 overflow-y-auto text-sm">
        <Row label="State">
          {status ? <StatusBadge status={status} /> : <Badge variant="outline">unknown</Badge>}
        </Row>
        <Separator />
        <Row label="Started">{formatRelative(startedAt) ?? "—"}</Row>
        <Row label="Completed">{formatRelative(completedAt) ?? "—"}</Row>
        <Separator />
        <Row label="Trace events">{traceCount}</Row>
        <Row label="Injectors">{injectors.length}</Row>
        {error && (
          <>
            <Separator />
            <div className="rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive">
              {error}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-[11px] uppercase tracking-wider text-muted-foreground">{label}</span>
      <span>{children}</span>
    </div>
  );
}
