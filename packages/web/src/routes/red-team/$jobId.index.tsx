import { Navigate, createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { type ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { LiveConversation } from "@/components/live-conversation";
import { RogueSecuritySuggestion } from "@/components/rogue-security-suggestion";
import { useRedTeamJob } from "@/api/queries";
import { useJobStream } from "@/api/ws";
import { cn, formatRelative } from "@/lib/utils";
import { StatusBadge } from "@/routes/index";

export const Route = createFileRoute("/red-team/$jobId/")({
  component: RedTeamDetailPage,
});

function RedTeamDetailPage() {
  const { jobId } = Route.useParams();
  const job = useRedTeamJob(jobId);
  // `kind` is what tells useJobStream which TanStack Query cache to patch.
  // Without it, terminal-status invalidates land on the evaluation key and
  // the auto-redirect to /report never fires until a manual page refresh.
  const stream = useJobStream(jobId, "red-team");

  const status = job.data?.status;
  const isTerminal = status === "completed" || status === "failed" || status === "cancelled";

  if (job.isLoading && !job.data) {
    return <LoadingShell />;
  }
  // Once a scan is finished it's no longer "live" — send the user to the
  // report. Mirrors the evaluation-side redirect so old scans never land on
  // a frozen live console.
  if (isTerminal) {
    return <Navigate to="/red-team/$jobId/report" params={{ jobId }} replace />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            <span className="text-muted-foreground">Red team</span>{" "}
            <span className="font-mono text-base">{jobId.slice(0, 12)}…</span>
          </h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Created {formatRelative(job.data?.created_at)} · Started{" "}
            {formatRelative(job.data?.started_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ConnectionPill state={stream.connection} />
        </div>
      </div>

      <RogueSecuritySuggestion />

      <ProgressBar value={stream.latest?.progress ?? job.data?.progress ?? 0} />

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <LiveConversation events={stream.events} flavour="red-team" />
        <ProgressRail
          status={(stream.latest?.status ?? job.data?.status) as string | undefined}
          startedAt={stream.latest?.started_at ?? job.data?.started_at}
          completedAt={stream.latest?.completed_at ?? job.data?.completed_at}
          error={stream.latest?.error_message ?? job.data?.error_message}
          eventCount={stream.events.length}
          chatCount={stream.events.filter((e) => e.kind === "chat").length}
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
  eventCount,
  chatCount,
}: {
  status?: string;
  startedAt?: string | null;
  completedAt?: string | null;
  error?: string | null;
  eventCount: number;
  chatCount: number;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <Row label="State">
          {status ? <StatusBadge status={status} /> : <Badge variant="outline">unknown</Badge>}
        </Row>
        <Separator />
        <Row label="Started">{formatRelative(startedAt) ?? "—"}</Row>
        <Row label="Completed">{formatRelative(completedAt) ?? "—"}</Row>
        <Separator />
        <Row label="Messages">{chatCount}</Row>
        <Row label="Events">{eventCount}</Row>
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
