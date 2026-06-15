import { Navigate, createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { type ReactNode } from "react";
import {
  IconAlertTriangle,
  IconBolt,
  IconCircleCheck,
  IconShieldCheck,
} from "@tabler/icons-react";

import { AgentGraph } from "@/components/resilience/agent-graph";
import { CheckpointScrubber } from "@/components/resilience/checkpoint-scrubber";
import { MetricsRadar } from "@/components/resilience/metrics-radar";
import { TraceTimeline } from "@/components/resilience/trace-timeline";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useResilienceJob, useResilienceReport } from "@/api/queries";
import type {
  ResilienceReport,
  ResilienceReportExperimentRow,
  ResilienceReportHighlights,
  ResilienceReportKeyFinding,
} from "@/api/types";
import { cn, formatRelative } from "@/lib/utils";

export const Route = createFileRoute("/resilience/$jobId/report")({
  component: ResilienceReportPage,
});

type ScoreTone = "excellent" | "good" | "fair" | "poor";

function scoreTone(score: number): ScoreTone {
  if (score >= 80) return "excellent";
  if (score >= 60) return "good";
  if (score >= 40) return "fair";
  return "poor";
}

function tonePalette(tone: ScoreTone): string {
  switch (tone) {
    case "excellent":
      return "border-emerald-500/40 bg-emerald-500/10 text-emerald-400";
    case "good":
      return "border-blue-500/40 bg-blue-500/10 text-blue-400";
    case "fair":
      return "border-[var(--chart-3)]/40 bg-[var(--chart-3)]/10 text-[var(--chart-3)]";
    case "poor":
    default:
      return "border-destructive/40 bg-destructive/10 text-destructive";
  }
}

function ResilienceReportPage() {
  const { jobId } = Route.useParams();
  const job = useResilienceJob(jobId);
  const status = job.data?.status;
  const isTerminal = status === "completed" || status === "failed" || status === "cancelled";
  const report = useResilienceReport(jobId, isTerminal);
  const reportError =
    report.error instanceof Error ? report.error.message : report.error ? String(report.error) : null;

  if (job.isLoading && !job.data) return <ReportLoadingShell />;
  if (status && !isTerminal) {
    return <Navigate to="/resilience/$jobId" params={{ jobId }} replace />;
  }

  return (
    <div className="space-y-4">
      <Hero
        jobId={jobId}
        completedAt={job.data?.completed_at}
        status={status ?? "pending"}
        architecture={job.data?.request?.resilience_config?.architecture}
        highlights={report.data?.highlights}
      />

      <Tabs defaultValue="report" className="w-full">
        <TabsList>
          <TabsTrigger value="report">Report</TabsTrigger>
          <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
          <TabsTrigger value="trace">Trace</TabsTrigger>
          <TabsTrigger value="topology">Topology</TabsTrigger>
        </TabsList>

        <TabsContent value="report" className="mt-4">
          <ReportTab
            report={report.data}
            loading={report.isPending}
            error={reportError}
          />
        </TabsContent>

        <TabsContent value="breakdown" className="mt-4">
          <BreakdownTab rows={report.data?.experiment_table ?? []} loading={report.isPending} />
        </TabsContent>

        <TabsContent value="trace" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Experiment timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <TraceTimeline
                events={report.data?.timeline ?? []}
                maxItems={100}
                loading={report.isPending}
                error={reportError}
              />
            </CardContent>
          </Card>
          <div className="mt-4">
            <CheckpointScrubber
              steps={report.data?.checkpoint_steps ?? []}
              loading={report.isPending}
              error={reportError}
            />
          </div>
        </TabsContent>

        <TabsContent value="topology" className="mt-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Agent graph</CardTitle>
            </CardHeader>
            <CardContent>
              <AgentGraph
                graph={report.data?.agent_graph ?? { nodes: [], edges: [] }}
                loading={report.isPending}
                error={reportError}
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ReportLoadingShell() {
  return (
    <div className="space-y-4">
      <div className="h-32 animate-pulse rounded-xl bg-muted/40" />
      <div className="h-9 w-72 animate-pulse rounded-md bg-muted/40" />
      <div className="h-64 animate-pulse rounded-xl bg-muted/40" />
    </div>
  );
}

function Hero({
  jobId,
  completedAt,
  status,
  architecture,
  highlights,
}: {
  jobId: string;
  completedAt?: string | null;
  status: string;
  architecture?: string;
  highlights?: ResilienceReportHighlights;
}) {
  const score = highlights?.overall_score ?? 0;
  const tone = scoreTone(score);

  return (
    <Card className="overflow-hidden">
      <div className="grid gap-0 lg:grid-cols-[1fr_auto]">
        <div className="space-y-1.5 p-5">
          <h1 className="text-2xl font-semibold tracking-tight">Resilience report</h1>
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
            {architecture && (
              <Badge variant="outline">
                <span className="text-muted-foreground">arch ·</span>&nbsp;{architecture}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap items-stretch gap-3 p-5 lg:border-l lg:border-border/60">
          <StatCard
            tone={tone}
            icon={<IconShieldCheck className="h-5 w-5" />}
            label="Overall score"
            value={highlights ? `${Math.round(score)}` : "—"}
            sub="/ 100"
          />
          <StatCard
            tone={highlights && highlights.experiments_passed === highlights.total_experiments ? "excellent" : "fair"}
            icon={<IconCircleCheck className="h-5 w-5" />}
            label="Experiments passed"
            value={highlights ? `${highlights.experiments_passed}/${highlights.total_experiments}` : "—"}
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
  tone: ScoreTone;
  icon: ReactNode;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className={cn("flex min-w-[180px] flex-col justify-between gap-2 rounded-xl border px-4 py-3", tonePalette(tone))}>
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-semibold uppercase tracking-[0.14em] opacity-80">{label}</span>
        <span className="opacity-80">{icon}</span>
      </div>
      <div className="space-y-0.5">
        <div className="text-3xl font-semibold tabular-nums leading-none">
          {value}
          {sub && <span className="text-lg opacity-70">{sub}</span>}
        </div>
      </div>
    </div>
  );
}

function ReportTab({
  report,
  loading,
  error,
}: {
  report?: ResilienceReport;
  loading: boolean;
  error?: string | null;
}) {
  if (loading && !report) {
    return <div className="h-64 animate-pulse rounded-xl bg-muted/40" />;
  }
  if (error && !report) {
    return (
      <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-6 text-sm text-destructive">
        {error}
      </div>
    );
  }
  if (!report) {
    return <p className="text-sm text-muted-foreground">Report unavailable.</p>;
  }

  const h = report.highlights;
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Metrics radar</CardTitle>
        </CardHeader>
        <CardContent>
          <MetricsRadar
            metrics={report.metrics_radar}
            loading={loading && !report.metrics_radar.length}
            error={error}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Metric rates</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <MetricRow label="Detection" value={h.detection_rate} />
          <MetricRow label="Containment" value={h.containment_rate} />
          <MetricRow label="Recovery" value={h.recovery_rate} />
          {h.is_multi_agent && (
            <>
              <MetricRow label="Cascade resilience" value={h.cascading_failure_rate} />
              <MetricRow label="System degradation" value={h.system_degradation_rate} />
            </>
          )}
        </CardContent>
      </Card>

      {report.key_findings.length > 0 && (
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <IconAlertTriangle className="h-4 w-4" /> Key findings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {report.key_findings.map((f: ResilienceReportKeyFinding) => (
              <div
                key={f.injector_id}
                className="rounded-lg border border-border/60 bg-muted/20 px-4 py-3 text-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold">{f.injector_name}</span>
                  <Badge variant="outline">{Math.round(f.composite_score)}/100</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{f.summary}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MetricRow({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  return (
    <div>
      <div className="mb-1 flex justify-between text-xs">
        <span>{label}</span>
        <span className="tabular-nums">{pct}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <motion.div
          className="h-full bg-primary"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
    </div>
  );
}

function BreakdownTab({
  rows,
  loading,
}: {
  rows: ResilienceReportExperimentRow[];
  loading: boolean;
}) {
  const downloadCsv = () => {
    const header = [
      "injector",
      "score",
      "passed",
      "detection",
      "containment",
      "recovery",
    ];
    const lines = rows.map((r) =>
      [
        r.injector_name,
        r.composite_score.toFixed(1),
        r.passed,
        r.detection_score.toFixed(2),
        r.containment_score.toFixed(2),
        r.recovery_score.toFixed(2),
      ].join(","),
    );
    const blob = new Blob([[header.join(","), ...lines].join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "resilience_breakdown.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading && rows.length === 0) {
    return <div className="h-48 animate-pulse rounded-xl bg-muted/40" />;
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-sm">Per-injector comparison</CardTitle>
        <Button size="sm" variant="outline" onClick={downloadCsv} disabled={rows.length === 0}>
          Export CSV
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        {rows.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground">No experiment data.</p>
        ) : (
          <table className="w-full text-sm">
            <thead className="border-b border-border text-left text-[11px] uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-6 py-2 font-medium">Injector</th>
                <th className="px-6 py-2 font-medium">Score</th>
                <th className="px-6 py-2 font-medium">Passed</th>
                <th className="px-6 py-2 font-medium">Detection</th>
                <th className="px-6 py-2 font-medium">Containment</th>
                <th className="px-6 py-2 font-medium">Recovery</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.experiment_id} className="border-b border-border/40 last:border-b-0">
                  <td className="px-6 py-2">{row.injector_name}</td>
                  <td className="px-6 py-2 font-mono tabular-nums">{Math.round(row.composite_score)}</td>
                  <td className="px-6 py-2">
                    {row.passed ? (
                      <IconCircleCheck className="h-4 w-4 text-emerald-500" />
                    ) : (
                      <IconBolt className="h-4 w-4 text-destructive" />
                    )}
                  </td>
                  <td className="px-6 py-2 tabular-nums">{Math.round(row.detection_score * 100)}%</td>
                  <td className="px-6 py-2 tabular-nums">{Math.round(row.containment_score * 100)}%</td>
                  <td className="px-6 py-2 tabular-nums">{Math.round(row.recovery_score * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </CardContent>
    </Card>
  );
}
