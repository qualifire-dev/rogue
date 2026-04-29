import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { IconWand } from "@tabler/icons-react";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  useDeleteInterviewSession,
  useGenerateScenarios,
  useSendInterviewMessage,
  useStartInterview,
} from "@/api/queries";
import { useConfig } from "@/stores/config";
import { useScenariosStore } from "@/stores/scenarios";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/scenarios/interview")({
  component: InterviewPage,
});

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function InterviewPage() {
  const cfg = useConfig();
  const navigate = useNavigate();
  const start = useStartInterview();
  const send = useSendInterviewMessage();
  const del = useDeleteInterviewSession();
  const genScenarios = useGenerateScenarios();
  const setBusinessContext = useConfig((s) => s.setBusinessContext);
  const addScenarios = useScenariosStore((s) => s.setAll);
  const existingScenarios = useScenariosStore((s) => s.scenarios);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [bootError, setBootError] = useState<string | null>(null);
  // The server returns is_complete=true once the interviewer has gathered
  // enough info (currently >= 3 user replies). Once true, the Finish button
  // unlocks; before that it's hinted but disabled to discourage thin context.
  const [isComplete, setIsComplete] = useState(false);

  const endRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (sessionId && !send.isPending) inputRef.current?.focus();
  }, [sessionId, send.isPending, messages]);

  const beginSession = async () => {
    setBootError(null);
    setIsComplete(false);
    const apiKey = cfg.apiKeys[cfg.interviewProvider];
    if (!apiKey) {
      setBootError(
        `No API key configured for "${cfg.interviewProvider}". Set one in Settings → Models or Settings → API keys.`,
      );
      return null;
    }
    try {
      const res = await start.mutateAsync({
        business_context: cfg.businessContext || undefined,
        model: cfg.interviewModel,
        api_key: apiKey,
      });
      setSessionId(res.session_id);
      setMessages([{ role: "assistant", content: res.initial_message }]);
      return res.session_id;
    } catch (e) {
      const msg = (e as Error).message;
      setBootError(msg);
      toast.error(`Failed to start interview: ${msg}`);
      return null;
    }
  };

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    void beginSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const restartSession = async () => {
    if (sessionId) {
      try {
        await del.mutateAsync(sessionId);
      } catch {
        /* server may already have cleaned the session */
      }
    }
    setSessionId(null);
    setMessages([]);
    setInput("");
    setIsComplete(false);
    await beginSession();
    toast.success("Interview restarted");
  };

  const sendMessage = async () => {
    if (!sessionId || !input.trim()) return;
    const userMsg: ChatMessage = { role: "user", content: input.trim() };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    try {
      const res = await send.mutateAsync({ session_id: sessionId, message: userMsg.content });
      setMessages((m) => [...m, { role: "assistant", content: res.response }]);
      // Server signals when the interviewer has gathered enough context.
      if (res.is_complete) setIsComplete(true);
    } catch (e) {
      toast.error(`Send failed: ${(e as Error).message}`);
    }
  };

  // Treat the user's own replies as the canonical business-context source —
  // they describe their agent in their own words, which generates better
  // scenarios than including the assistant's clarifying questions.
  const buildBusinessContext = (): string => {
    const userReplies = messages
      .filter((m) => m.role === "user")
      .map((m) => m.content.trim())
      .filter(Boolean);
    if (userReplies.length === 0) return cfg.businessContext;
    // Prepend any existing context the user had already typed in the
    // BusinessContextCard so we don't lose it.
    const prior = cfg.businessContext.trim();
    const interview = userReplies.join("\n\n");
    return prior ? `${prior}\n\n${interview}` : interview;
  };

  const finish = async () => {
    const apiKey = cfg.apiKeys[cfg.scenarioGenProvider];
    if (!apiKey) {
      toast.error(
        `No API key configured for "${cfg.scenarioGenProvider}" — set one in Settings → Models.`,
      );
      return;
    }
    const ctx = buildBusinessContext();
    if (!ctx.trim()) {
      toast.error("Reply to the interview a few times before finishing.");
      return;
    }
    try {
      // Persist the assembled context in the config store so subsequent
      // eval/red-team runs pick it up automatically.
      setBusinessContext(ctx);
      const res = await genScenarios.mutateAsync({
        business_context: ctx,
        model: cfg.scenarioGenModel,
        api_key: apiKey,
        api_base: cfg.scenarioGenApiBase,
        count: 10,
      });
      const generated = res.scenarios?.scenarios ?? [];
      if (generated.length === 0) {
        toast.error("The model returned no scenarios. Try refining the interview.");
        return;
      }
      // Append onto whatever the user had — drop dupes by scenario text so
      // re-running interview doesn't pile copies into the library.
      const existingTexts = new Set(existingScenarios.map((s) => s.scenario.trim()));
      const merged = [
        ...existingScenarios,
        ...generated.filter((s) => !existingTexts.has(s.scenario.trim())),
      ];
      addScenarios(merged);
      toast.success(
        `Added ${merged.length - existingScenarios.length} scenario${
          merged.length - existingScenarios.length === 1 ? "" : "s"
        } from the interview.`,
      );
      navigate({ to: "/scenarios" });
    } catch (e) {
      toast.error(`Couldn't generate scenarios: ${(e as Error).message}`);
    }
  };

  const userMessageCount = messages.filter((m) => m.role === "user").length;
  const finishHint = isComplete
    ? "The interviewer has enough context — generate scenarios and head to the library."
    : `Reply ${Math.max(0, 3 - userMessageCount)} more time${
        Math.max(0, 3 - userMessageCount) === 1 ? "" : "s"
      } to unlock scenario generation.`;

  return (
    <div className="flex min-h-[calc(100svh-8rem)] w-full flex-1 flex-col">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Interview</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Chat with the AI to derive business context and scenario candidates.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={restartSession}
            disabled={del.isPending || start.isPending}
          >
            {del.isPending || start.isPending ? "Restarting…" : "Restart"}
          </Button>
          <Button
            onClick={finish}
            disabled={!isComplete || genScenarios.isPending}
            title={finishHint}
          >
            <IconWand className="mr-1.5 h-4 w-4" />
            {genScenarios.isPending ? "Generating…" : "Finish & generate"}
          </Button>
        </div>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between gap-3 border-b border-border/60 py-3">
          <CardTitle className="text-sm">
            {sessionId
              ? `Session ${sessionId.slice(0, 8)}…`
              : start.isPending
                ? "Starting session…"
                : "No active session"}
          </CardTitle>
          <span
            className={cn(
              "rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
              isComplete
                ? "border-[var(--chart-2)]/40 bg-[var(--chart-2)]/10 text-[var(--chart-2)]"
                : "border-border/60 bg-muted/40 text-muted-foreground",
            )}
            title={finishHint}
          >
            {isComplete ? "Ready to generate" : `Replies ${userMessageCount} / 3`}
          </span>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4">
          {bootError ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <div className="rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {bootError}
              </div>
              <Button onClick={beginSession} disabled={start.isPending}>
                Retry
              </Button>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              {start.isPending ? "Starting interview…" : "Loading…"}
            </div>
          ) : (
            <div className="space-y-3">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={cn(
                    "max-w-[85%] rounded-lg border px-3 py-2 text-sm",
                    m.role === "user"
                      ? "ml-auto border-primary/30 bg-primary/10"
                      : "border-border/60 bg-card",
                  )}
                >
                  {m.content}
                </div>
              ))}
              <div ref={endRef} />
            </div>
          )}
        </CardContent>
        <div className="border-t border-border/60 p-3">
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              sendMessage();
            }}
          >
            <Input
              ref={inputRef}
              placeholder={sessionId ? "Type a reply…" : "Waiting for session…"}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={!sessionId || send.isPending}
              autoFocus
            />
            <Button type="submit" disabled={!sessionId || send.isPending || !input.trim()}>
              Send
            </Button>
          </form>
        </div>
      </Card>
    </div>
  );
}
