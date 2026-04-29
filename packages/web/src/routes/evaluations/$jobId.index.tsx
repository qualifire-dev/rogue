import { Navigate, createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, type ReactNode } from "react";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useCancelEvaluation, useEvaluation } from "@/api/queries";
import { useJobStream, type TimelineEvent } from "@/api/ws";
import { cn, formatRelative } from "@/lib/utils";
import { StatusBadge } from "@/routes/index";
import { RogueSecuritySuggestion } from "@/components/rogue-security-suggestion";

export const Route = createFileRoute("/evaluations/$jobId/")({
  component: EvaluationDetailPage,
});

function EvaluationDetailPage() {
  const { jobId } = Route.useParams();
  const job = useEvaluation(jobId);
  const stream = useJobStream(jobId);
  const cancel = useCancelEvaluation();

  const status = job.data?.status;
  const isTerminal = status === "completed" || status === "failed" || status === "cancelled";

  // The live view is only meaningful while the job is in flight. Once it
  // finishes we redirect to /report so a finished evaluation never opens
  // its live console (especially for runs from days/weeks ago).
  if (job.isLoading && !job.data) {
    return <LoadingShell />;
  }
  if (isTerminal) {
    return <Navigate to="/evaluations/$jobId/report" params={{ jobId }} replace />;
  }

  return (
    // Flex column that fills the parent's flex-1 region (see __root.tsx).
    // ``min-h-0`` is critical so the inner ``flex-1`` grid row is actually
    // allowed to shrink/grow inside the column instead of pushing the page
    // taller than the viewport.
    <div className="flex h-full min-h-0 flex-1 flex-col gap-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            <span className="text-muted-foreground">Evaluation</span>{" "}
            <span className="font-mono text-base">{jobId.slice(0, 12)}…</span>
          </h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Created {formatRelative(job.data?.created_at)} · Started{" "}
            {formatRelative(job.data?.started_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ConnectionPill state={stream.connection} />
          {job.data?.status === "running" && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => cancel.mutate(jobId)}
              disabled={cancel.isPending}
            >
              Cancel
            </Button>
          )}
        </div>
      </div>

      <RogueSecuritySuggestion />

      <ProgressBar value={stream.latest?.progress ?? job.data?.progress ?? 0} />

      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[2fr_1fr]">
        <ConversationView events={stream.events} />
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

interface DisplayEvent {
  key: string;
  at: string;
  kind: "chat" | "system";
  role?: "rogue" | "agent";
  speaker?: string;
  content?: string;
  systemTone?: "info" | "success" | "danger" | "muted";
}

function buildDisplayEvents(events: TimelineEvent[]): DisplayEvent[] {
  const out: DisplayEvent[] = [];
  let lastChatRole: "rogue" | "agent" | null = null;
  let scenarioIdx = 0;

  events.forEach((e, i) => {
    if (e.kind === "chat") {
      const raw = (e.chat.role || "").toLowerCase();
      const role: "rogue" | "agent" = raw.includes("agent") ? "agent" : "rogue";

      // Heuristic: a Rogue message immediately following an Agent reply,
      // or the very first Rogue message, marks the start of a new scenario.
      if (role === "rogue" && lastChatRole !== "rogue") {
        scenarioIdx += 1;
        out.push({
          key: `scenario-${i}`,
          at: e.at,
          kind: "system",
          systemTone: "info",
          content: `Testing scenario ${scenarioIdx}`,
        });
      }

      out.push({
        key: `chat-${i}`,
        at: e.at,
        kind: "chat",
        role,
        speaker: e.chat.role,
        content: e.chat.content,
      });
      lastChatRole = role;
    } else {
      const s = e.update.status;
      // Skip "running" — it just means the job started, no signal value.
      if (s === "running" || s === "pending") return;
      const tone: DisplayEvent["systemTone"] =
        s === "completed" ? "success" : s === "failed" || s === "cancelled" ? "danger" : "muted";
      const label =
        s === "completed"
          ? "Evaluation completed"
          : s === "failed"
            ? `Evaluation failed${e.update.error_message ? ` — ${e.update.error_message}` : ""}`
            : s === "cancelled"
              ? "Evaluation cancelled"
              : `Status: ${s}`;
      out.push({
        key: `status-${i}`,
        at: e.at,
        kind: "system",
        systemTone: tone,
        content: label,
      });
    }
  });

  return out;
}

function ConversationView({ events }: { events: TimelineEvent[] }) {
  const display = useMemo(() => buildDisplayEvents(events), [events]);
  const ref = useRef<HTMLDivElement | null>(null);

  // Auto-scroll on new content; users on touch/scroll wheels can still scroll
  // (browser preserves position when content is appended above the bottom).
  useEffect(() => {
    if (!ref.current) return;
    ref.current.scrollTop = ref.current.scrollHeight;
  }, [display.length]);

  return (
    // ``h-full`` makes the card occupy its grid cell; ``min-h-0`` so the
    // CardContent's flex-1 child can scroll instead of expanding the card.
    <Card className="flex h-full min-h-0 flex-col overflow-hidden">
      <CardHeader className="border-b border-border/60 py-3">
        <CardTitle className="text-sm">Conversation</CardTitle>
      </CardHeader>
      <CardContent className="flex min-h-0 flex-1 flex-col p-0">
        <div ref={ref} className="min-h-0 flex-1 overflow-y-auto bg-background/40 px-4 py-4">
          {display.length === 0 ? (
            <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
              Waiting for the agent under test to respond…
            </div>
          ) : (
            <div className="space-y-3">
              {display.map((e) =>
                e.kind === "chat" ? (
                  <ChatBubble
                    key={e.key}
                    role={e.role!}
                    speaker={e.speaker ?? ""}
                    at={e.at}
                    content={e.content ?? ""}
                  />
                ) : (
                  <SystemDivider
                    key={e.key}
                    tone={e.systemTone ?? "muted"}
                    content={e.content ?? ""}
                    at={e.at}
                  />
                ),
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ChatBubble({
  role,
  speaker,
  content,
  at,
}: {
  role: "rogue" | "agent";
  speaker: string;
  content: string;
  at: string;
}) {
  const isRogue = role === "rogue";
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.16, ease: "easeOut" }}
      className={cn("flex w-full", isRogue ? "justify-end" : "justify-start")}
    >
      <div className={cn("flex max-w-[85%] flex-col gap-1", isRogue ? "items-end" : "items-start")}>
        <div
          className={cn(
            "flex items-center gap-2 text-[10px] uppercase tracking-wider",
            isRogue ? "text-primary" : "text-[var(--chart-2)]",
          )}
        >
          <span className="font-semibold">
            {speaker || (isRogue ? "Rogue" : "Agent under test")}
          </span>
          <span className="text-muted-foreground">{new Date(at).toLocaleTimeString()}</span>
        </div>
        <div
          className={cn(
            "whitespace-pre-wrap rounded-lg border px-3 py-2 text-sm leading-relaxed",
            isRogue
              ? "border-primary/30 bg-primary/10 text-foreground"
              : "border-border/60 bg-card text-foreground",
          )}
        >
          {content}
        </div>
      </div>
    </motion.div>
  );
}

function SystemDivider({
  tone,
  content,
  at,
}: {
  tone: "info" | "success" | "danger" | "muted";
  content: string;
  at: string;
}) {
  const ring =
    tone === "success"
      ? "border-[var(--chart-2)]/40 bg-[var(--chart-2)]/10 text-[var(--chart-2)]"
      : tone === "danger"
        ? "border-destructive/40 bg-destructive/10 text-destructive"
        : tone === "info"
          ? "border-primary/40 bg-primary/10 text-primary"
          : "border-border/60 bg-muted/50 text-muted-foreground";
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.18 }}
      className="my-1 flex items-center gap-2"
    >
      <span className="h-px flex-1 bg-border/60" />
      <span
        className={cn(
          "rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
          ring,
        )}
        title={new Date(at).toLocaleTimeString()}
      >
        {content}
      </span>
      <span className="h-px flex-1 bg-border/60" />
    </motion.div>
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
