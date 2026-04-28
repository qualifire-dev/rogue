import type { ReactNode } from "react";

import { useTheme } from "@/components/theme-provider";
import { cn } from "@/lib/utils";

export type EmptyStateIllustration =
  | "alerts"
  | "api-keys"
  | "exposures"
  | "integrations"
  | "inventory"
  | "logs"
  | "red-team"
  | "risks";

interface EmptyStateProps {
  illustration: EmptyStateIllustration;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  illustration,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  const { theme } = useTheme();
  const src = `/assets/empty-state/${illustration}-${theme}.svg`;
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-md border border-dashed border-border/60 px-6 py-12 text-center",
        className,
      )}
    >
      <img src={src} alt="" aria-hidden className="h-32 w-auto opacity-90" />
      <div className="space-y-1">
        <h3 className="text-base font-semibold tracking-tight">{title}</h3>
        {description && (
          <p className="mx-auto max-w-md text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {action && <div className="pt-1">{action}</div>}
    </div>
  );
}
