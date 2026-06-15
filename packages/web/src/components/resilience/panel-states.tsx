import type { ReactNode } from "react";
import { IconAlertCircle, IconLoader2 } from "@tabler/icons-react";

import { cn } from "@/lib/utils";

interface PanelStateProps {
  className?: string;
  title?: string;
  description?: string;
  children?: ReactNode;
}

/** Centered loading placeholder for resilience visualizations. */
export function ResilienceLoadingPanel({
  className,
  title = "Loading…",
  description,
}: PanelStateProps) {
  return (
    <div
      className={cn(
        "flex h-48 flex-col items-center justify-center gap-2 rounded-xl border border-border/60 bg-muted/20 p-6 text-center",
        className,
      )}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <IconLoader2 className="h-6 w-6 animate-spin text-muted-foreground" aria-hidden />
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description && <p className="max-w-sm text-xs text-muted-foreground">{description}</p>}
    </div>
  );
}

/** Error placeholder when report data or chart rendering fails. */
export function ResilienceErrorPanel({
  className,
  title = "Unable to load data",
  description = "Something went wrong while loading this section. Try refreshing the page.",
  children,
}: PanelStateProps) {
  return (
    <div
      className={cn(
        "flex h-48 flex-col items-center justify-center gap-2 rounded-xl border border-destructive/40 bg-destructive/10 p-6 text-center",
        className,
      )}
      role="alert"
    >
      <IconAlertCircle className="h-6 w-6 text-destructive" aria-hidden />
      <p className="text-sm font-medium text-destructive">{title}</p>
      <p className="max-w-sm text-xs text-destructive/80">{description}</p>
      {children}
    </div>
  );
}

/** Empty placeholder when there is no data yet (not an error). */
export function ResilienceEmptyPanel({
  className,
  title = "No data yet",
  description,
}: PanelStateProps) {
  return (
    <div
      className={cn(
        "flex h-48 flex-col items-center justify-center gap-1 rounded-xl border border-dashed border-border/60 p-6 text-center",
        className,
      )}
    >
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      {description && <p className="max-w-sm text-xs text-muted-foreground">{description}</p>}
    </div>
  );
}

/** Inline skeleton bars for chart areas while loading. */
export function ResilienceChartSkeleton({ className }: { className?: string }) {
  return (
    <div
      className={cn("flex h-72 flex-col items-center justify-center gap-3", className)}
      aria-hidden
    >
      <div className="h-48 w-48 animate-pulse rounded-full bg-muted/50" />
      <div className="h-3 w-32 animate-pulse rounded bg-muted/40" />
    </div>
  );
}
