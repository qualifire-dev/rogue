import { useEffect, useMemo, useRef } from "react";
import { motion } from "framer-motion";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { TimelineEvent } from "@/api/ws";

/**
 * Job-flavour drives the wording on the synthesised system markers
 * ("Testing scenario N" vs "Running attack N", and the terminal
 * "Evaluation/Scan completed/failed/cancelled" lines).
 */
export type LiveConversationFlavour = "evaluation" | "red-team";

interface DisplayEvent {
  key: string;
  at: string;
  kind: "chat" | "system";
  role?: "rogue" | "agent";
  speaker?: string;
  content?: string;
  systemTone?: "info" | "success" | "danger" | "muted";
}

function buildDisplayEvents(
  events: TimelineEvent[],
  flavour: LiveConversationFlavour,
): DisplayEvent[] {
  const out: DisplayEvent[] = [];
  let lastChatRole: "rogue" | "agent" | null = null;
  let probeIdx = 0;
  // Track the (scenario_index, attempt_index) pair we last rendered a
  // marker for, so a new attempt of the SAME scenario also gets its own
  // divider — even if the underlying chat sequence happens to start with
  // a Rogue message twice in a row (which the heuristic alone would miss).
  let lastMarkerKey: string | null = null;
  const probeWord = flavour === "red-team" ? "attack" : "scenario";
  const noun = flavour === "red-team" ? "Scan" : "Evaluation";

  events.forEach((e, i) => {
    if (e.kind === "chat") {
      const raw = (e.chat.role || "").toLowerCase();
      const role: "rogue" | "agent" = raw.includes("agent") ? "agent" : "rogue";

      // Prefer the explicit (scenario_index, attempt_index, attempts_total)
      // metadata the multi-turn driver attaches to each chat event. Falls
      // back to the heuristic for older servers / the red-team flavour
      // (which doesn't yet supply attempt metadata).
      const sIdx = e.chat.scenario_index;
      const aIdx = e.chat.attempt_index;
      const aTotal = e.chat.attempts_total;
      const hasMeta = typeof sIdx === "number" && typeof aIdx === "number";

      if (hasMeta) {
        const markerKey = `${sIdx}/${aIdx}`;
        if (markerKey !== lastMarkerKey) {
          const label =
            (aTotal ?? 1) > 1
              ? `Testing ${probeWord} ${sIdx + 1}, attempt ${aIdx + 1} of ${aTotal}`
              : `Testing ${probeWord} ${sIdx + 1}`;
          out.push({
            key: `marker-${i}`,
            at: e.at,
            kind: "system",
            systemTone: "info",
            content: label,
          });
          lastMarkerKey = markerKey;
        }
      } else if (role === "rogue" && lastChatRole !== "rogue") {
        // Heuristic fallback: Rogue → Agent → Rogue alternation marks
        // a new probe boundary.
        probeIdx += 1;
        out.push({
          key: `marker-${i}`,
          at: e.at,
          kind: "system",
          systemTone: "info",
          content: `Testing ${probeWord} ${probeIdx}`,
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
      // Skip pre-terminal status churn — only render terminal-state markers.
      if (s === "running" || s === "pending") return;
      const tone: DisplayEvent["systemTone"] =
        s === "completed" ? "success" : s === "failed" || s === "cancelled" ? "danger" : "muted";
      const label =
        s === "completed"
          ? `${noun} completed`
          : s === "failed"
            ? `${noun} failed${e.update.error_message ? ` — ${e.update.error_message}` : ""}`
            : s === "cancelled"
              ? `${noun} cancelled`
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

interface Props {
  events: TimelineEvent[];
  flavour?: LiveConversationFlavour;
  emptyMessage?: string;
  title?: string;
}

/**
 * Shared chat-style live transcript. Used by both the live-evaluation and
 * live-red-team pages — they only differ in copy (scenario vs attack) and
 * the title noun.
 *
 * Layout: fills the parent flex cell. Wrap the consuming page in
 * ``<div className="flex h-full min-h-0 flex-1 flex-col">`` (with the
 * surrounding grid row also marked ``min-h-0 flex-1``) so the inner
 * scroll viewport can absorb all available vertical space.
 */
export function LiveConversation({
  events,
  flavour = "evaluation",
  emptyMessage,
  title = "Conversation",
}: Props) {
  const display = useMemo(() => buildDisplayEvents(events, flavour), [events, flavour]);
  const ref = useRef<HTMLDivElement | null>(null);

  // Auto-scroll to the bottom on new content.
  useEffect(() => {
    if (!ref.current) return;
    ref.current.scrollTop = ref.current.scrollHeight;
  }, [display.length]);

  return (
    <Card className="flex h-full min-h-0 flex-col overflow-hidden">
      <CardHeader className="border-b border-border/60 py-3">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="flex min-h-0 flex-1 flex-col p-0">
        <div ref={ref} className="min-h-0 flex-1 overflow-y-auto bg-background/40 px-4 py-4">
          {display.length === 0 ? (
            <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
              {emptyMessage ??
                (flavour === "red-team"
                  ? "Waiting for the first attack to fire…"
                  : "Waiting for the agent under test to respond…")}
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
