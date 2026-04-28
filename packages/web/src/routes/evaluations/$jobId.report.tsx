import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useRef, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { motion } from "framer-motion";
import {
  IconAlertTriangle,
  IconCheck,
  IconCircleCheck,
  IconCircleX,
  IconMessages,
  IconShieldCheck,
} from "@tabler/icons-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { useEvaluation, useGenerateSummary } from "@/api/queries";
import { useConfig } from "@/stores/config";
import { RogueSecuritySuggestion } from "@/components/rogue-security-suggestion";
import { cn, formatRelative } from "@/lib/utils";
import type { ConversationEvaluation, ScenarioResult, StructuredSummary } from "@/api/types";

export const Route = createFileRoute("/evaluations/$jobId/report")({
  component: EvaluationReportPage,
});

function EvaluationReportPage() {
  const { jobId } = Route.useParams();
  const job = useEvaluation(jobId);
  const cfg = useConfig();
  const summaryMutation = useGenerateSummary();
  const triggeredRef = useRef(false);

  const status = job.data?.status;
  const isTerminal = status === "completed" || status === "failed" || status === "cancelled";

  const evaluationResults = job.data?.evaluation_results ?? null;
  const scenarioResults: ScenarioResult[] = evaluationResults?.results ?? [];

  // Server persists the summary on the job after the first /llm/summary call,
  // so prefer the cached value over the in-component mutation result.
  const summary: StructuredSummary | null =
    job.data?.summary ?? summaryMutation.data?.summary ?? null;

  const judgeKey = cfg.apiKeys[cfg.judgeProvider];
  const judgeKeyMissing = !judgeKey;
  const needsGeneration = isTerminal && !!evaluationResults && !summary && !judgeKeyMissing;

  useEffect(() => {
    if (triggeredRef.current) return;
    if (!needsGeneration) return;
    if (summaryMutation.isPending) return;

    triggeredRef.current = true;
    summaryMutation.mutate({
      job_id: jobId,
      results: evaluationResults,
      model: cfg.judgeModel,
      api_key: judgeKey,
      api_base: cfg.judgeApiBase,
      judge_model: cfg.judgeModel,
      rogue_security_api_key: cfg.rogueSecurityEnabled ? cfg.rogueSecurityApiKey : undefined,
      rogue_security_base_url: cfg.rogueSecurityEnabled ? cfg.rogueSecurityBaseUrl : undefined,
    });
  }, [
    needsGeneration,
    jobId,
    evaluationResults,
    cfg.judgeModel,
    cfg.judgeApiBase,
    judgeKey,
    cfg.rogueSecurityEnabled,
    cfg.rogueSecurityApiKey,
    cfg.rogueSecurityBaseUrl,
    summaryMutation,
  ]);

  const stats = useMemo(() => computeStats(scenarioResults), [scenarioResults]);

  return (
    <div className="space-y-4">
      <Hero
        jobId={jobId}
        completedAt={job.data?.completed_at}
        status={status ?? "pending"}
        judgeModel={job.data?.judge_model ?? job.data?.request?.agent_config?.judge_llm}
        stats={stats}
      />

      <RogueSecuritySuggestion />

      <Tabs defaultValue="report" className="w-full">
        <TabsList>
          <TabsTrigger value="report">Report</TabsTrigger>
          <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
          <TabsTrigger value="conversations">
            Conversations
            {stats.totalConversations > 0 && (
              <span className="ml-1.5 rounded-full bg-muted px-1.5 py-px text-[10px] tabular-nums text-muted-foreground">
                {stats.totalConversations}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="report" className="mt-4">
          <ReportTab
            jobLoading={job.isLoading}
            jobError={job.error as Error | null}
            isTerminal={isTerminal}
            status={status}
            hasResults={!!evaluationResults}
            judgeKeyMissing={judgeKeyMissing}
            summaryPending={summaryMutation.isPending}
            summaryError={summaryMutation.error as Error | null}
            summary={summary}
          />
        </TabsContent>

        <TabsContent value="breakdown" className="mt-4">
          <BreakdownTab summary={summary} scenarioResults={scenarioResults} />
        </TabsContent>

        <TabsContent value="conversations" className="mt-4">
          <ConversationsTab scenarioResults={scenarioResults} />
        </TabsContent>
      </Tabs>

      <div className="flex justify-end">
        <Button asChild variant="outline" size="sm">
          <Link to="/evaluations/$jobId" params={{ jobId }}>
            Back to live view
          </Link>
        </Button>
      </div>
    </div>
  );
}

// ─── Hero ────────────────────────────────────────────────────────────────────

interface Stats {
  totalScenarios: number;
  passedScenarios: number;
  failedScenarios: number;
  totalConversations: number;
  passedConversations: number;
  failedConversations: number;
  passRate: number;
}

function computeStats(results: ScenarioResult[]): Stats {
  let totalConv = 0;
  let passedConv = 0;
  let passedScen = 0;
  for (const r of results) {
    if (r.passed) passedScen += 1;
    for (const c of r.conversations ?? []) {
      totalConv += 1;
      if (c.passed) passedConv += 1;
    }
  }
  const passRate = totalConv === 0 ? 0 : passedConv / totalConv;
  return {
    totalScenarios: results.length,
    passedScenarios: passedScen,
    failedScenarios: results.length - passedScen,
    totalConversations: totalConv,
    passedConversations: passedConv,
    failedConversations: totalConv - passedConv,
    passRate,
  };
}

function Hero({
  jobId,
  completedAt,
  status,
  judgeModel,
  stats,
}: {
  jobId: string;
  completedAt?: string | null;
  status: string;
  judgeModel?: string | null;
  stats: Stats;
}) {
  const passPct = Math.round(stats.passRate * 100);
  const passTone =
    stats.totalConversations === 0
      ? "muted"
      : passPct >= 80
        ? "success"
        : passPct >= 50
          ? "warn"
          : "danger";

  return (
    <Card className="overflow-hidden">
      <div className="grid gap-0 lg:grid-cols-[1fr_auto]">
        <div className="space-y-1.5 p-5">
          <h1 className="text-2xl font-semibold tracking-tight">Evaluation report</h1>
          <p className="text-xs text-muted-foreground">
            {completedAt
              ? `${new Date(completedAt).toLocaleString()} · ${formatRelative(completedAt)}`
              : "—"}
          </p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            <Badge variant="outline" className="font-mono">
              {jobId.slice(0, 12)}…
            </Badge>
            <Badge variant="secondary" className="capitalize">
              {status}
            </Badge>
            {judgeModel && (
              <Badge variant="outline">
                <span className="text-muted-foreground">judge ·</span>&nbsp;{judgeModel}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap items-stretch gap-3 p-5 lg:border-l lg:border-border/60">
          <StatCard
            tone={passTone}
            icon={<IconShieldCheck className="h-5 w-5" />}
            label="Pass rate"
            value={stats.totalConversations === 0 ? "—" : `${passPct}%`}
          />
          <StatCard
            tone={stats.failedConversations > 0 ? "danger" : "success"}
            icon={<IconAlertTriangle className="h-5 w-5" />}
            label="Failures"
            value={`${stats.failedConversations} / ${stats.totalConversations}`}
            sub={`${stats.totalScenarios} scenarios`}
          />
        </div>
      </div>
    </Card>
  );
}

function StatCard({
  tone,
  icon,
  label,
  value,
  sub,
}: {
  tone: "success" | "danger" | "warn" | "muted";
  icon: ReactNode;
  label: string;
  value: string;
  sub?: string;
}) {
  const palette =
    tone === "success"
      ? "border-[var(--chart-2)]/40 bg-[var(--chart-2)]/10 text-[var(--chart-2)]"
      : tone === "danger"
        ? "border-destructive/40 bg-destructive/10 text-destructive"
        : tone === "warn"
          ? "border-[var(--chart-3)]/40 bg-[var(--chart-3)]/10 text-[var(--chart-3)]"
          : "border-border/60 bg-muted/40 text-muted-foreground";
  return (
    <div
      className={cn(
        "flex min-w-[180px] flex-col justify-between gap-2 rounded-xl border px-4 py-3",
        palette,
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-[0.14em] opacity-80">
          {label}
        </span>
        <span className="opacity-80">{icon}</span>
      </div>
      <div className="space-y-0.5">
        <div className="text-3xl font-semibold tabular-nums leading-none">{value}</div>
        {sub && <div className="text-[11px] opacity-70">{sub}</div>}
      </div>
    </div>
  );
}

// ─── Report tab ──────────────────────────────────────────────────────────────

function ReportTab({
  jobLoading,
  jobError,
  isTerminal,
  status,
  hasResults,
  judgeKeyMissing,
  summaryPending,
  summaryError,
  summary,
}: {
  jobLoading: boolean;
  jobError: Error | null;
  isTerminal: boolean;
  status?: string;
  hasResults: boolean;
  judgeKeyMissing: boolean;
  summaryPending: boolean;
  summaryError: Error | null;
  summary: StructuredSummary | null;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Summary</CardTitle>
      </CardHeader>
      <CardContent className="prose prose-invert max-w-none">
        {jobLoading ? (
          <p className="not-prose text-sm text-muted-foreground">Loading evaluation…</p>
        ) : jobError ? (
          <p className="not-prose text-sm text-destructive">
            Failed to load evaluation: {jobError.message}
          </p>
        ) : !isTerminal ? (
          <p className="not-prose text-sm text-muted-foreground">
            The evaluation is still {status ?? "running"}. The summary will be generated once it
            finishes.
          </p>
        ) : !hasResults ? (
          <p className="not-prose text-sm text-muted-foreground">
            No results were produced for this run, so a summary can't be generated.
          </p>
        ) : summary ? (
          <SummaryBody summary={summary} />
        ) : judgeKeyMissing ? (
          <div className="not-prose space-y-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
            <p className="font-medium">Judge API key required to generate the summary.</p>
            <p>
              Add a key for the configured judge provider in{" "}
              <Link to="/settings" className="underline">
                Settings
              </Link>
              , then refresh this page.
            </p>
          </div>
        ) : summaryPending ? (
          <p className="not-prose text-sm text-muted-foreground">Generating summary…</p>
        ) : summaryError ? (
          <p className="not-prose text-sm text-destructive">
            Failed to generate summary: {summaryError.message}
          </p>
        ) : (
          <p className="not-prose text-sm text-muted-foreground">Waiting for results…</p>
        )}
      </CardContent>
    </Card>
  );
}

function SummaryBody({ summary }: { summary: StructuredSummary }) {
  return (
    <>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{summary.overall_summary}</ReactMarkdown>
      {summary.key_findings.length > 0 && (
        <>
          <h3>Key findings</h3>
          <ul>
            {summary.key_findings.map((f, i) => (
              <li key={i}>{f}</li>
            ))}
          </ul>
        </>
      )}
      {summary.recommendations.length > 0 && (
        <>
          <h3>Recommendations</h3>
          <ul>
            {summary.recommendations.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}

// ─── Breakdown tab ───────────────────────────────────────────────────────────

function BreakdownTab({
  summary,
  scenarioResults,
}: {
  summary: StructuredSummary | null;
  scenarioResults: ScenarioResult[];
}) {
  // Prefer LLM-generated breakdown when present (it's a better one-line outcome
  // per scenario). Fall back to the raw scenario results so we always show
  // something even before the summary lands.
  const rows = useMemo(() => {
    if (summary?.detailed_breakdown && summary.detailed_breakdown.length > 0) {
      return summary.detailed_breakdown.map((r) => ({
        scenario: r.scenario,
        passed: parseStatus(r.status),
        outcome: r.outcome,
      }));
    }
    return scenarioResults.map((r) => ({
      scenario: r.scenario.scenario,
      passed: r.passed,
      outcome: r.conversations?.[0]?.reason ?? "",
    }));
  }, [summary, scenarioResults]);

  if (rows.length === 0) {
    return (
      <Card>
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          No scenarios to report yet.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">Per-scenario breakdown</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/60 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <th className="px-4 py-2 font-medium">Scenario</th>
                <th className="w-[120px] px-4 py-2 font-medium">Result</th>
                <th className="px-4 py-2 font-medium">Outcome</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr
                  key={i}
                  className={cn("border-b border-border/40 last:border-b-0", "hover:bg-muted/30")}
                >
                  <td className="px-4 py-3 align-top text-foreground/90">{r.scenario}</td>
                  <td className="px-4 py-3 align-top">
                    {r.passed === null ? (
                      <Badge variant="outline">unknown</Badge>
                    ) : r.passed ? (
                      <span className="inline-flex items-center gap-1.5 rounded-md border border-[var(--chart-2)]/40 bg-[var(--chart-2)]/10 px-2 py-0.5 text-xs font-medium text-[var(--chart-2)]">
                        <IconCircleCheck className="h-3.5 w-3.5" /> Passed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 rounded-md border border-destructive/40 bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive">
                        <IconCircleX className="h-3.5 w-3.5" /> Failed
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 align-top text-muted-foreground">{r.outcome || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function parseStatus(s: string): boolean | null {
  if (!s) return null;
  // The LLM returns ✅/❌ per the prompt, but be lenient.
  const v = s.toLowerCase();
  if (s.includes("✅") || v.includes("pass")) return true;
  if (s.includes("❌") || v.includes("fail")) return false;
  return null;
}

// ─── Conversations tab ───────────────────────────────────────────────────────

function ConversationsTab({ scenarioResults }: { scenarioResults: ScenarioResult[] }) {
  if (scenarioResults.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
          <IconMessages className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm font-medium">No conversations recorded</p>
          <p className="text-xs text-muted-foreground">
            This evaluation didn't produce any transcripts.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {scenarioResults.map((r, i) => (
        <ScenarioCard key={i} result={r} index={i} />
      ))}
    </div>
  );
}

function ScenarioCard({ result, index }: { result: ScenarioResult; index: number }) {
  const passed = result.passed;
  return (
    <Card className="overflow-hidden">
      <CardHeader className="flex flex-row items-start justify-between gap-3 border-b border-border/60 py-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-muted-foreground">
            <span>Scenario {index + 1}</span>
            {result.scenario.scenario_type && (
              <span className="rounded-sm bg-muted px-1.5 py-px">
                {result.scenario.scenario_type}
              </span>
            )}
          </div>
          <CardTitle className="text-sm font-medium leading-snug text-foreground/90">
            {result.scenario.scenario}
          </CardTitle>
        </div>
        {passed ? (
          <span className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-[var(--chart-2)]/40 bg-[var(--chart-2)]/10 px-2 py-0.5 text-xs font-medium text-[var(--chart-2)]">
            <IconCheck className="h-3.5 w-3.5" /> Passed
          </span>
        ) : (
          <span className="inline-flex shrink-0 items-center gap-1.5 rounded-md border border-destructive/40 bg-destructive/10 px-2 py-0.5 text-xs font-medium text-destructive">
            <IconCircleX className="h-3.5 w-3.5" /> Failed
          </span>
        )}
      </CardHeader>
      <CardContent className="space-y-4 p-4">
        {result.conversations.map((c, i) => (
          <ConversationBlock key={i} conv={c} index={i} />
        ))}
      </CardContent>
    </Card>
  );
}

function ConversationBlock({ conv, index }: { conv: ConversationEvaluation; index: number }) {
  const messages = conv.messages?.messages ?? [];
  return (
    <div className="space-y-2">
      {index > 0 && <Separator />}
      <div className="space-y-2">
        {messages.map((m, i) => {
          const r = (m.role || "").toLowerCase();
          const isRogue = r === "user" || r.includes("rogue");
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.12, delay: i * 0.02 }}
              className={cn("flex w-full", isRogue ? "justify-end" : "justify-start")}
            >
              <div
                className={cn(
                  "flex max-w-[85%] flex-col gap-1",
                  isRogue ? "items-end" : "items-start",
                )}
              >
                <span
                  className={cn(
                    "text-[10px] font-semibold uppercase tracking-wider",
                    isRogue ? "text-primary" : "text-[var(--chart-2)]",
                  )}
                >
                  {isRogue ? "Rogue" : "Agent under test"}
                </span>
                <div
                  className={cn(
                    "whitespace-pre-wrap rounded-lg border px-3 py-2 text-sm leading-relaxed",
                    isRogue ? "border-primary/30 bg-primary/10" : "border-border/60 bg-card",
                  )}
                >
                  {m.content}
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
      <div
        className={cn(
          "rounded-md border px-3 py-2 text-xs",
          conv.passed
            ? "border-[var(--chart-2)]/30 bg-[var(--chart-2)]/5 text-[var(--chart-2)]"
            : "border-destructive/30 bg-destructive/5 text-destructive",
        )}
      >
        <span className="font-semibold uppercase tracking-wider">
          Judge · {conv.passed ? "passed" : "failed"}
        </span>
        <p className="mt-1 whitespace-pre-wrap text-foreground/85">{conv.reason}</p>
      </div>
    </div>
  );
}
