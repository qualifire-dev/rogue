import { createFileRoute, Link } from "@tanstack/react-router";
import { IconActivity, IconShieldHalf } from "@tabler/icons-react";

import { EmptyState } from "@/components/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useEvaluations, useHealth, useRedTeamJobs } from "@/api/queries";
import { formatRelative } from "@/lib/utils";

export const Route = createFileRoute("/")({
  component: DashboardPage,
});

function DashboardPage() {
  const health = useHealth();
  const evals = useEvaluations();
  const redTeam = useRedTeamJobs();

  const recentEvals = evals.data?.jobs.slice(0, 5) ?? [];
  const recentRedTeam = redTeam.data?.jobs.slice(0, 5) ?? [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Operational Console</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Run policy evaluations, drive red-team scans, and review structured reports — all against
          your local Rogue server.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          label="Server"
          value={health.isError ? "Disconnected" : "Live"}
          tone={health.isError ? "destructive" : "success"}
          description={
            health.data?.timestamp ? `Last ping ${formatRelative(health.data.timestamp)}` : "—"
          }
        />
        <MetricCard
          label="Evaluations"
          value={evals.data?.total ?? 0}
          description="Total jobs created"
        />
        <MetricCard
          label="Red team scans"
          value={redTeam.data?.total ?? 0}
          description="Total scans created"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <IconActivity className="h-4 w-4 text-primary" /> Recent evaluations
              </CardTitle>
              <CardDescription>Latest 5 jobs</CardDescription>
            </div>
            <Button asChild size="sm" variant="ghost">
              <Link to="/evaluations">View all</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {recentEvals.length === 0 ? (
              <EmptyState
                illustration="logs"
                title="No evaluations yet"
                description="Start one to see it stream here in real time."
                action={
                  <Button asChild size="sm">
                    <Link to="/evaluations/new">New evaluation</Link>
                  </Button>
                }
              />
            ) : (
              <ul className="space-y-2">
                {recentEvals.map((j) => (
                  <li
                    key={j.job_id}
                    className="flex items-center justify-between rounded-md border border-border/60 bg-card/40 px-3 py-2"
                  >
                    <Link
                      to="/evaluations/$jobId"
                      params={{ jobId: j.job_id }}
                      className="font-mono text-xs text-foreground hover:text-primary"
                    >
                      {j.job_id.slice(0, 12)}…
                    </Link>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <StatusBadge status={j.status} />
                      <span>{formatRelative(j.created_at)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <IconShieldHalf className="h-4 w-4 text-primary" /> Recent red-team scans
              </CardTitle>
              <CardDescription>Latest 5 scans</CardDescription>
            </div>
            <Button asChild size="sm" variant="ghost">
              <Link to="/red-team">View all</Link>
            </Button>
          </CardHeader>
          <CardContent>
            {recentRedTeam.length === 0 ? (
              <EmptyState
                illustration="red-team"
                title="No red-team scans yet"
                description="Configure attacks and probe your agent for vulnerabilities."
                action={
                  <Button asChild size="sm">
                    <Link to="/red-team/configure">Configure scan</Link>
                  </Button>
                }
              />
            ) : (
              <ul className="space-y-2">
                {recentRedTeam.map((j) => (
                  <li
                    key={j.job_id}
                    className="flex items-center justify-between rounded-md border border-border/60 bg-card/40 px-3 py-2"
                  >
                    <Link
                      to="/red-team/$jobId"
                      params={{ jobId: j.job_id }}
                      className="font-mono text-xs text-foreground hover:text-primary"
                    >
                      {j.job_id.slice(0, 12)}…
                    </Link>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <StatusBadge status={j.status} />
                      <span>{formatRelative(j.created_at)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  description,
  tone,
}: {
  label: string;
  value: string | number;
  description?: string;
  tone?: "success" | "destructive";
}) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          {label}
        </div>
        <div
          className={
            "mt-2 text-2xl font-semibold tracking-tight " +
            (tone === "destructive"
              ? "text-destructive"
              : tone === "success"
                ? "text-[var(--chart-2)]"
                : "text-foreground")
          }
        >
          {value}
        </div>
        {description && <div className="mt-1 text-xs text-muted-foreground">{description}</div>}
      </CardContent>
    </Card>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const variant: Parameters<typeof Badge>[0]["variant"] =
    status === "completed"
      ? "success"
      : status === "failed" || status === "cancelled"
        ? "destructive"
        : status === "running"
          ? "default"
          : "secondary";
  return (
    <Badge variant={variant} className="px-1.5 text-[10px] uppercase tracking-wider">
      {status}
    </Badge>
  );
}
