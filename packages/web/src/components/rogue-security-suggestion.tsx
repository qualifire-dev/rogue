import { Link } from "@tanstack/react-router";
import { IconShieldLock, IconX } from "@tabler/icons-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useConfig } from "@/stores/config";
import { cn } from "@/lib/utils";

const DISMISS_KEY = "rogue:rs-suggestion-dismissed";

interface Props {
  className?: string;
  /** Variant: "card" (full banner) or "inline" (compact one-liner). */
  variant?: "card" | "inline";
}

/**
 * Shown across live-eval / report views when Rogue Security isn't configured.
 *
 * Encourages users to enable centralized reporting via the rogue.security cloud.
 * Hides once they enable it (or click dismiss for the session).
 */
export function RogueSecuritySuggestion({ className, variant = "card" }: Props) {
  const enabled = useConfig((s) => s.rogueSecurityEnabled);
  const apiKey = useConfig((s) => s.rogueSecurityApiKey);
  const [dismissed, setDismissed] = useState(() => sessionStorage.getItem(DISMISS_KEY) === "1");

  // Considered "configured" only when both the toggle is on AND a key is set.
  if ((enabled && apiKey) || dismissed) return null;

  const handleDismiss = () => {
    sessionStorage.setItem(DISMISS_KEY, "1");
    setDismissed(true);
  };

  if (variant === "inline") {
    return (
      <div
        className={cn(
          "flex items-center gap-2 rounded-md border border-primary/30 bg-primary/5 px-3 py-2 text-xs",
          className,
        )}
      >
        <IconShieldLock className="h-3.5 w-3.5 text-primary" />
        <span className="text-foreground/90">
          Centralize reports — enable Rogue Security in{" "}
          <Link
            to="/settings"
            className="font-medium text-primary underline-offset-2 hover:underline"
          >
            Settings
          </Link>
          .
        </span>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "relative flex items-start gap-3 rounded-lg border border-primary/30 bg-primary/5 px-4 py-3",
        className,
      )}
    >
      <IconShieldLock className="mt-0.5 h-5 w-5 shrink-0 text-primary" />
      <div className="flex-1 space-y-1">
        <p className="text-sm font-medium text-foreground">Centralize your evaluation reports</p>
        <p className="text-xs text-muted-foreground">
          Enable Rogue Security and add an API key to ship every report to the rogue.security
          dashboard — share findings with your team and track posture over time.
        </p>
      </div>
      <div className="flex items-center gap-2">
        <Button asChild size="sm" variant="outline" className="h-8">
          <Link to="/settings">Configure</Link>
        </Button>
        <button
          type="button"
          aria-label="Dismiss"
          onClick={handleDismiss}
          className="text-muted-foreground transition-colors hover:text-foreground"
        >
          <IconX className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
