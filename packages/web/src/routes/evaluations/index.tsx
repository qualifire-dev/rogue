import { createFileRoute, Link } from "@tanstack/react-router";

import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useEvaluations } from "@/api/queries";
import { formatRelative } from "@/lib/utils";
import { StatusBadge } from "@/routes/index";

export const Route = createFileRoute("/evaluations/")({
  component: EvaluationsListPage,
});

function EvaluationsListPage() {
  const { data, isLoading } = useEvaluations();
  const jobs = data?.jobs ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Evaluations</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Policy-mode evaluations of your agent against the configured scenarios.
          </p>
        </div>
        <Button asChild>
          <Link to="/evaluations/new">New evaluation</Link>
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">All jobs ({data?.total ?? 0})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="px-6 py-12 text-center text-sm text-muted-foreground">Loading…</div>
          ) : jobs.length === 0 ? (
            <div className="p-6">
              <EmptyState
                illustration="logs"
                title="No evaluations yet"
                description="Run your first policy-mode evaluation against the configured agent."
                action={
                  <Button asChild>
                    <Link to="/evaluations/new">New evaluation</Link>
                  </Button>
                }
              />
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="border-b border-border text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-6 py-2 font-medium">Job ID</th>
                  <th className="px-6 py-2 font-medium">Status</th>
                  <th className="px-6 py-2 font-medium">Progress</th>
                  <th className="px-6 py-2 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((j) => (
                  <tr
                    key={j.job_id}
                    className="border-b border-border/40 last:border-b-0 hover:bg-card/40"
                  >
                    <td className="px-6 py-2 font-mono text-xs">
                      <Link
                        to="/evaluations/$jobId"
                        params={{ jobId: j.job_id }}
                        className="hover:text-primary"
                      >
                        {j.job_id}
                      </Link>
                    </td>
                    <td className="px-6 py-2">
                      <StatusBadge status={j.status} />
                    </td>
                    <td className="px-6 py-2 text-xs text-muted-foreground">
                      {Math.round((j.progress ?? 0) * 100)}%
                    </td>
                    <td className="px-6 py-2 text-xs text-muted-foreground">
                      {formatRelative(j.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
