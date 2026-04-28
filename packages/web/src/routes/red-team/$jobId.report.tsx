import { Navigate, createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useMemo, type ReactNode } from "react";
import {
  IconAlertTriangle,
  IconCircleCheck,
  IconCircleX,
  IconMessages,
  IconShieldCheck,
  IconShieldHalf,
  IconTarget,
} from "@tabler/icons-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useRedTeamJob, useRedTeamReport } from "@/api/queries";
import { RogueSecuritySuggestion } from "@/components/rogue-security-suggestion";
import { cn, formatRelative } from "@/lib/utils";
import type {
  RedTeamConversationMessage,
  RedTeamReport,
  RedTeamReportFrameworkCard,
  RedTeamReportKeyFinding,
  RedTeamReportSeverityCounts,
  RedTeamReportVulnerabilityRow,
} from "@/api/types";

export const Route = createFileRoute("/red-team/$jobId/report")({
  component: RedTeamReportPage,
});

type SeverityTone = "critical" | "high" | "medium" | "low" | "muted";

function severityTone(severity: string | null | undefined): SeverityTone {
  if (!severity) return "muted";
  const s = severity.toLowerCase();
  if (s === "critical") return "critical";
  if (s === "high") return "high";
  if (s === "medium") return "medium";
  if (s === "low") return "low";
  return "muted";
}

function tonePalette(tone: SeverityTone | "success" | "danger"): string {
  switch (tone) {
    case "critical":
    case "danger":
      return "border-destructive/40 bg-destructive/10 text-destructive";
    case "high":
      return "border-orange-500/40 bg-orange-500/10 text-orange-400";
    case "medium":
      return "border-[var(--chart-3)]/40 bg-[var(--chart-3)]/10 text-[var(--chart-3)]";
    case "low":
      return "border-blue-500/40 bg-blue-500/10 text-blue-400";
    case "success":
      return "border-[var(--chart-2)]/40 bg-[var(--chart-2)]/10 text-[var(--chart-2)]";
    case "muted":
    default:
      return "border-border/60 bg-muted/40 text-muted-foreground";
  }
}

function RedTeamReportPage() {
  const { jobId } = Route.useParams();
  const job = useRedTeamJob(jobId);
  const status = job.data?.status;
  const isTerminal = status === "completed" || status === "failed" || status === "cancelled";

  const report = useRedTeamReport(jobId, isTerminal);

  if (job.isLoading && !job.data) return <ReportLoadingShell />;
  // While the scan is still pending/running there's no report — bounce to
  // the live console.
  if (status && !isTerminal) {
    return <Navigate to="/red-team/$jobId" params={{ jobId }} replace />;
  }

  const conversations = job.data?.conversations ?? [];

  return (
    <div className="space-y-4">
      <Hero
        jobId={jobId}
        completedAt={job.data?.completed_at}
        status={status ?? "pending"}
        scanType={job.data?.request?.red_team_config?.scan_type}
        highlights={report.data?.highlights}
      />

      <RogueSecuritySuggestion />

      <Tabs defaultValue="report" className="w-full">
        <TabsList>
          <TabsTrigger value="report">Report</TabsTrigger>
          <TabsTrigger value="breakdown">Breakdown</TabsTrigger>
          <TabsTrigger value="conversations">
            Conversations
            {conversations.length > 0 && (
              <span className="ml-1.5 rounded-full bg-muted px-1.5 py-px text-[10px] tabular-nums text-muted-foreground">
                {conversations.length}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="report" className="mt-4">
          <ReportTab
            report={report.data}
            loading={report.isPending}
            error={report.error as Error | null}
          />
        </TabsContent>

        <TabsContent value="breakdown" className="mt-4">
          <BreakdownTab rows={report.data?.vulnerability_table ?? []} loading={report.isPending} />
        </TabsContent>

        <TabsContent value="conversations" className="mt-4">
          <ConversationsTab conversations={conversations} />
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

// ─── Hero ────────────────────────────────────────────────────────────────────

function Hero({
  jobId,
  completedAt,
  status,
  scanType,
  highlights,
}: {
  jobId: string;
  completedAt?: string | null;
  status: string;
  scanType?: string;
  highlights?: RedTeamReportSeverityCounts;
}) {
  const score = highlights?.overall_score ?? 0;
  const total = highlights?.total_vulnerabilities_tested ?? 0;
  const found = highlights?.total_vulnerabilities_found ?? 0;

  // Lower score = worse. Map to a tone.
  const scoreTone = score >= 80 ? "success" : score >= 50 ? "medium" : "critical";
  const vulnTone = found > 0 ? "critical" : "success";

  return (
    <Card className="overflow-hidden">
      <div className="grid gap-0 lg:grid-cols-[1fr_auto]">
        <div className="space-y-1.5 p-5">
          <h1 className="text-2xl font-semibold tracking-tight">Red team report</h1>
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
            {scanType && (
              <Badge variant="outline">
                <span className="text-muted-foreground">scan ·</span>&nbsp;{scanType}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap items-stretch gap-3 p-5 lg:border-l lg:border-border/60">
          <StatCard
            tone={scoreTone}
            icon={<IconShieldCheck className="h-5 w-5" />}
            label="Overall security"
            value={highlights ? `${Math.round(score)}%` : "—"}
          />
          <StatCard
            tone={vulnTone}
            icon={<IconAlertTriangle className="h-5 w-5" />}
            label="Vulnerabilities"
            value={highlights ? `${found} / ${total}` : "—"}
            sub={highlights ? "found / tested" : undefined}
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
  tone: SeverityTone | "success";
  icon: ReactNode;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div
      className={cn(
        "flex min-w-[180px] flex-col justify-between gap-2 rounded-xl border px-4 py-3",
        tonePalette(tone),
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
  report,
  loading,
  error,
}: {
  report: RedTeamReport | undefined;
  loading: boolean;
  error: Error | null;
}) {
  if (loading) {
    return <StateCard message="Loading report…" />;
  }
  if (error) {
    return <StateCard tone="danger" message={`Failed to load report: ${error.message}`} />;
  }
  if (!report) {
    return <StateCard message="No report available." />;
  }

  return (
    <div className="space-y-4">
      <HighlightsRow highlights={report.highlights} />
      {report.framework_coverage.length > 0 && (
        <FrameworkCoverageCard cards={report.framework_coverage} />
      )}
      {report.key_findings.length > 0 && <KeyFindingsCard findings={report.key_findings} />}
    </div>
  );
}

function StateCard({ message, tone = "muted" }: { message: string; tone?: "muted" | "danger" }) {
  return (
    <Card>
      <CardContent className="py-8 text-center">
        <p
          className={cn(
            "text-sm",
            tone === "danger" ? "text-destructive" : "text-muted-foreground",
          )}
        >
          {message}
        </p>
      </CardContent>
    </Card>
  );
}

function HighlightsRow({ highlights }: { highlights: RedTeamReportSeverityCounts }) {
  const items: { label: string; value: number; tone: SeverityTone }[] = [
    { label: "Critical", value: highlights.critical_count, tone: "critical" },
    { label: "High", value: highlights.high_count, tone: "high" },
    { label: "Medium", value: highlights.medium_count, tone: "medium" },
    { label: "Low", value: highlights.low_count, tone: "low" },
  ];
  return (
    <Card>
      <CardHeader className="border-b border-border/60 py-3">
        <CardTitle className="text-sm">Highlights</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4">
        {items.map((it) => (
          <div
            key={it.label}
            className={cn(
              "flex items-center justify-between rounded-lg border px-4 py-3",
              tonePalette(it.tone),
            )}
          >
            <span className="text-sm font-medium">{it.label}</span>
            <span className="text-2xl font-semibold tabular-nums">{it.value}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function FrameworkCoverageCard({ cards }: { cards: RedTeamReportFrameworkCard[] }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2.5 border-b border-border/60 py-3">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-primary/40 bg-primary/10 text-primary">
          <IconShieldHalf className="h-4 w-4" />
        </span>
        <div>
          <CardTitle className="text-sm">Compliance frameworks</CardTitle>
          <p className="text-xs text-muted-foreground">
            Measures the agent against requested frameworks.
          </p>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => {
          const failed = c.tested_count - c.passed_count;
          const tone: SeverityTone | "success" =
            c.compliance_score >= 80 ? "success" : c.compliance_score >= 50 ? "medium" : "critical";
          return (
            <div key={c.framework_id} className={cn("rounded-lg border p-3", tonePalette(tone))}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold">{c.framework_name}</span>
                <span className="text-xs tabular-nums opacity-80">
                  {Math.round(c.compliance_score)}%
                </span>
              </div>
              <p className="mt-2 text-xs opacity-80">
                {c.tested_count} / {c.total_count} vulnerabilities tested
              </p>
              <p className="mt-0.5 text-xs opacity-80">
                {failed} failed · {c.passed_count} passed
              </p>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

function KeyFindingsCard({ findings }: { findings: RedTeamReportKeyFinding[] }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2.5 border-b border-border/60 py-3">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-destructive/40 bg-destructive/10 text-destructive">
          <IconTarget className="h-4 w-4" />
        </span>
        <div>
          <CardTitle className="text-sm">Key findings</CardTitle>
          <p className="text-xs text-muted-foreground">
            Top {findings.length} most critical vulnerabilities.
          </p>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 p-4">
        {findings.map((f) => {
          const tone = severityTone(f.severity);
          return (
            <div
              key={f.vulnerability_id}
              className="rounded-lg border border-border/60 bg-card/40 p-3"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm font-semibold">{f.vulnerability_name}</span>
                    {f.severity && (
                      <span
                        className={cn(
                          "rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
                          tonePalette(tone),
                        )}
                      >
                        {f.severity}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{f.summary}</p>
                  {f.attack_ids.length > 0 && (
                    <p className="text-[11px] text-muted-foreground">
                      <span className="font-medium">Attacks:</span>{" "}
                      <span className="font-mono">{f.attack_ids.join(", ")}</span>
                    </p>
                  )}
                </div>
                <div className="flex shrink-0 gap-3 rounded-md border border-border/60 bg-background/60 px-3 py-1.5 text-xs">
                  <div className="text-center">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                      Success rate
                    </div>
                    <div className="font-semibold tabular-nums">
                      {(f.success_rate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
                      CVSS
                    </div>
                    <div className="font-semibold tabular-nums">{f.cvss_score.toFixed(1)}</div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}

// ─── Breakdown tab ───────────────────────────────────────────────────────────

function BreakdownTab({
  rows,
  loading,
}: {
  rows: RedTeamReportVulnerabilityRow[];
  loading: boolean;
}) {
  const csv = useMemo(() => buildBreakdownCsv(rows), [rows]);
  const downloadCsv = () => {
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "red-team-breakdown.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <StateCard message="Loading breakdown…" />;
  if (rows.length === 0) {
    return <StateCard message="No vulnerabilities recorded." />;
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2 border-b border-border/60 py-3">
        <CardTitle className="text-sm">Vulnerability breakdown</CardTitle>
        <button
          type="button"
          onClick={downloadCsv}
          className="rounded-md border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-medium text-primary transition-colors hover:bg-primary/20"
        >
          Export full report (CSV)
        </button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border/60 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <th className="px-4 py-2 font-medium">Vulnerability</th>
                <th className="w-[80px] px-4 py-2 font-medium">Safe</th>
                <th className="w-[110px] px-4 py-2 font-medium">Severity</th>
                <th className="w-[110px] px-4 py-2 font-medium">Success rate</th>
                <th className="px-4 py-2 font-medium">Attacks</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const tone = severityTone(r.severity);
                return (
                  <tr
                    key={r.vulnerability_id}
                    className="border-b border-border/40 last:border-b-0 hover:bg-muted/30"
                  >
                    <td className="px-4 py-3 align-top text-foreground/90">
                      {r.vulnerability_name}
                    </td>
                    <td className="px-4 py-3 align-top">
                      {r.passed ? (
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-md border border-[var(--chart-2)]/40 bg-[var(--chart-2)]/10 text-[var(--chart-2)]">
                          <IconCircleCheck className="h-3.5 w-3.5" />
                        </span>
                      ) : (
                        <span className="inline-flex h-6 w-6 items-center justify-center rounded-md border border-destructive/40 bg-destructive/10 text-destructive">
                          <IconCircleX className="h-3.5 w-3.5" />
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 align-top">
                      {r.severity ? (
                        <span
                          className={cn(
                            "rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
                            tonePalette(tone),
                          )}
                        >
                          {r.severity}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 align-top tabular-nums text-muted-foreground">
                      {(r.success_rate * 100).toFixed(1)}%
                    </td>
                    <td className="px-4 py-3 align-top font-mono text-xs text-muted-foreground">
                      {r.attacks_used.join(", ") || "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function buildBreakdownCsv(rows: RedTeamReportVulnerabilityRow[]): string {
  const header = [
    "vulnerability_id",
    "vulnerability_name",
    "passed",
    "severity",
    "success_rate",
    "attacks_attempted",
    "attacks_successful",
    "attacks_used",
  ];
  const lines = [header.join(",")];
  for (const r of rows) {
    lines.push(
      [
        r.vulnerability_id,
        csvField(r.vulnerability_name),
        r.passed ? "true" : "false",
        r.severity ?? "",
        r.success_rate.toFixed(4),
        String(r.attacks_attempted),
        String(r.attacks_successful),
        csvField(r.attacks_used.join("|")),
      ].join(","),
    );
  }
  return lines.join("\n") + "\n";
}

function csvField(value: string): string {
  if (/[",\n]/.test(value)) return `"${value.replace(/"/g, '""')}"`;
  return value;
}

// ─── Conversations tab ───────────────────────────────────────────────────────

function ConversationsTab({ conversations }: { conversations: RedTeamConversationMessage[] }) {
  if (conversations.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-2 py-12 text-center">
          <IconMessages className="h-8 w-8 text-muted-foreground" />
          <p className="text-sm font-medium">No conversations recorded</p>
          <p className="text-xs text-muted-foreground">
            This scan did not capture any chat transcripts.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="border-b border-border/60 py-3">
        <CardTitle className="text-sm">Captured conversations</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 p-4">
        {conversations.map((m, i) => {
          const role = (m.role || "").toLowerCase();
          const isAgent = role.includes("agent");
          return (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.12, delay: i * 0.01 }}
              className={cn("flex w-full", isAgent ? "justify-start" : "justify-end")}
            >
              <div
                className={cn(
                  "flex max-w-[85%] flex-col gap-1",
                  isAgent ? "items-start" : "items-end",
                )}
              >
                <span
                  className={cn(
                    "text-[10px] font-semibold uppercase tracking-wider",
                    isAgent ? "text-[var(--chart-2)]" : "text-primary",
                  )}
                >
                  {m.role || (isAgent ? "Agent under test" : "Rogue")}
                </span>
                <div
                  className={cn(
                    "whitespace-pre-wrap rounded-lg border px-3 py-2 text-sm leading-relaxed",
                    isAgent
                      ? "border-border/60 bg-card text-foreground"
                      : "border-primary/30 bg-primary/10 text-foreground",
                  )}
                >
                  {m.content}
                </div>
              </div>
            </motion.div>
          );
        })}
      </CardContent>
    </Card>
  );
}
