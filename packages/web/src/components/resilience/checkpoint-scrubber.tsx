import { useEffect, useState } from "react";

import type { ResilienceReportCheckpointStep } from "@/api/types";
import {
  ResilienceEmptyPanel,
  ResilienceErrorPanel,
  ResilienceLoadingPanel,
} from "@/components/resilience/panel-states";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface CheckpointScrubberProps {
  steps: ResilienceReportCheckpointStep[];
  className?: string;
  loading?: boolean;
  error?: string | null;
}

/** Step through checkpoint snapshot/restore operations from experiment traces. */
export function CheckpointScrubber({
  steps,
  className,
  loading = false,
  error = null,
}: CheckpointScrubberProps) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    setIndex(0);
  }, [steps.length]);

  if (loading) {
    return (
      <ResilienceLoadingPanel
        title="Loading checkpoint steps…"
        description="Reading snapshot and restore events from the experiment trace."
      />
    );
  }

  if (error) {
    return <ResilienceErrorPanel title="Checkpoint replay unavailable" description={error} />;
  }

  if (steps.length === 0) {
    return (
      <ResilienceEmptyPanel
        className={className}
        title="No checkpoint operations recorded"
        description="Enable checkpoint recovery in experiment config to capture snapshot/restore steps."
      />
    );
  }

  const safeIndex = Math.min(index, steps.length - 1);
  const step = steps[safeIndex];
  if (!step) {
    return (
      <ResilienceErrorPanel
        title="Invalid checkpoint step"
        description="The checkpoint index is out of range."
      />
    );
  }

  const tone = step.success
    ? "border-emerald-500/40 bg-emerald-500/10"
    : "border-destructive/40 bg-destructive/10";

  return (
    <div className={cn("space-y-3 rounded-xl border border-border/60 p-4", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Checkpoint replay</h3>
        <span className="font-mono text-xs text-muted-foreground">
          {safeIndex + 1} / {steps.length}
        </span>
      </div>
      <div className={cn("rounded-lg border p-4 text-sm", tone)}>
        <div className="font-semibold capitalize">{step.operation}</div>
        <dl className="mt-2 space-y-1 text-xs text-muted-foreground">
          <div className="flex justify-between">
            <dt>Status</dt>
            <dd>{step.success ? "Success" : "Failed"}</dd>
          </div>
          {step.thread_id && (
            <div className="flex justify-between">
              <dt>Thread</dt>
              <dd className="font-mono">{step.thread_id}</dd>
            </div>
          )}
          {step.checkpoint_id && (
            <div className="flex justify-between gap-2">
              <dt>Checkpoint</dt>
              <dd className="max-w-[12rem] truncate font-mono">{step.checkpoint_id}</dd>
            </div>
          )}
          {step.error && (
            <div>
              <dt className="text-destructive">Error</dt>
              <dd className="text-destructive">{step.error}</dd>
            </div>
          )}
        </dl>
      </div>
      <div className="flex gap-2">
        <Button
          size="sm"
          variant="outline"
          disabled={safeIndex <= 0}
          onClick={() => setIndex((i) => Math.max(0, i - 1))}
        >
          Previous
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={safeIndex >= steps.length - 1}
          onClick={() => setIndex((i) => Math.min(steps.length - 1, i + 1))}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
