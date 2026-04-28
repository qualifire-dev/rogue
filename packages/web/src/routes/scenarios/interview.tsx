import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  useDeleteInterviewSession,
  useSendInterviewMessage,
  useStartInterview,
} from "@/api/queries";
import { useConfig } from "@/stores/config";
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
  const start = useStartInterview();
  const send = useSendInterviewMessage();
  const del = useDeleteInterviewSession();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [bootError, setBootError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Refocus the input after every send / restart so the user can keep typing.
  useEffect(() => {
    if (sessionId && !send.isPending) inputRef.current?.focus();
  }, [sessionId, send.isPending, messages]);

  const beginSession = async () => {
    setBootError(null);
    const apiKey = cfg.apiKeys[cfg.interviewProvider];
    if (!apiKey) {
      setBootError(
        `No API key configured for "${cfg.interviewProvider}". Set one in Settings → Models or Settings → API keys.`,
      );
      return null;
    }
    try {
      const res = await start.mutateAsync({
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

  // Auto-start on first mount.
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
        /* ignore — server may already have cleaned the session */
      }
    }
    setSessionId(null);
    setMessages([]);
    setInput("");
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
    } catch (e) {
      toast.error(`Send failed: ${(e as Error).message}`);
    }
  };

  return (
    <div className="flex min-h-[calc(100svh-8rem)] w-full flex-1 flex-col">
      <div className="mb-4 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Interview</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Chat with the AI to derive business context and scenario candidates.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={restartSession}
          disabled={del.isPending || start.isPending}
        >
          {del.isPending || start.isPending ? "Restarting…" : "Restart session"}
        </Button>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardHeader className="border-b border-border/60 py-3">
          <CardTitle className="text-sm">
            {sessionId
              ? `Session ${sessionId.slice(0, 8)}…`
              : start.isPending
                ? "Starting session…"
                : "No active session"}
          </CardTitle>
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
