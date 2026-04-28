import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/api/client";

export const Route = createFileRoute("/red-team/$jobId/report")({
  component: RedTeamReportPage,
});

function RedTeamReportPage() {
  const { jobId } = Route.useParams();
  const report = useQuery({
    queryKey: ["red-team", jobId, "report"],
    queryFn: () => api<Record<string, unknown>>(`/api/v1/red-team/${jobId}/report`),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold tracking-tight">Red team report</h1>
        <Button asChild variant="outline" size="sm">
          <Link to="/red-team/$jobId" params={{ jobId }}>
            Back
          </Link>
        </Button>
      </div>

      <Card>
        <CardContent className="p-6">
          {report.isLoading ? (
            <p className="text-muted-foreground">Loading…</p>
          ) : report.isError ? (
            <p className="text-destructive">{(report.error as Error).message}</p>
          ) : (
            <pre className="overflow-auto whitespace-pre-wrap font-mono text-xs">
              {JSON.stringify(report.data, null, 2)}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
