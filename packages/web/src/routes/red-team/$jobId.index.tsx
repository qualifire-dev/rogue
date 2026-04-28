import { createFileRoute, Link } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useRedTeamJob } from "@/api/queries";
import { useJobStream } from "@/api/ws";
import { formatRelative } from "@/lib/utils";
import { StatusBadge } from "@/routes/index";

export const Route = createFileRoute("/red-team/$jobId/")({
  component: RedTeamDetailPage,
});

function RedTeamDetailPage() {
  const { jobId } = Route.useParams();
  const job = useRedTeamJob(jobId);
  const stream = useJobStream(jobId);

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            <span className="text-muted-foreground">Red team</span>{" "}
            <span className="font-mono text-base">{jobId.slice(0, 12)}…</span>
          </h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Created {formatRelative(job.data?.created_at)}
          </p>
        </div>
        <Button asChild variant="outline" size="sm">
          <Link to="/red-team/$jobId/report" params={{ jobId }}>
            Report
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Live event stream</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-96 overflow-y-auto rounded-md bg-background/40 px-4 py-3 font-mono text-[12px] leading-relaxed">
              {stream.events.length === 0 ? (
                <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                  Waiting for events…
                </div>
              ) : (
                stream.events.map((e, i) => (
                  <div key={i} className="text-muted-foreground">
                    [{new Date(e.at).toLocaleTimeString()}]{" "}
                    {e.kind === "status"
                      ? `${e.update.status} · ${Math.round((e.update.progress ?? 0) * 100)}%`
                      : `${e.chat.role}: ${e.chat.content}`}
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-[11px] uppercase tracking-wider text-muted-foreground">
                State
              </span>
              <StatusBadge
                status={(stream.latest?.status ?? job.data?.status ?? "pending") as string}
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-[11px] uppercase tracking-wider text-muted-foreground">
                Progress
              </span>
              <span>{Math.round((stream.latest?.progress ?? job.data?.progress ?? 0) * 100)}%</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
