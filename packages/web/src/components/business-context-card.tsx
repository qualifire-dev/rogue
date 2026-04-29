import { Link } from "@tanstack/react-router";
import { IconWand } from "@tabler/icons-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useConfig } from "@/stores/config";

interface Props {
  /** Optional offer to launch the interview (only meaningful for evaluations). */
  showInterviewLink?: boolean;
}

/**
 * Free-text "what does this agent do?" panel. Persisted in the config store
 * so it survives reloads, gets pushed to the TUI's TOML via /api/v1/config,
 * and is forwarded as `business_context` on every eval / red-team submit.
 */
export function BusinessContextCard({ showInterviewLink = false }: Props) {
  const value = useConfig((s) => s.businessContext);
  const setValue = useConfig((s) => s.setBusinessContext);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-3">
        <div>
          <CardTitle>Business context</CardTitle>
          <CardDescription>
            Describe what the agent does, who its users are, and the policy boundaries. Used by the
            judge to score scenarios and by the scenario generator to write realistic prompts.
          </CardDescription>
        </div>
        {showInterviewLink && (
          <Button asChild size="sm" variant="outline" className="shrink-0">
            <Link to="/scenarios/interview">
              <IconWand className="mr-1.5 h-4 w-4" />
              Use interview
            </Link>
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          rows={5}
          placeholder="e.g. T-shirt shopping assistant for Shirtify. Should never quote prices below $10, never reveal supplier names, and always suggest the V-neck variant when out of stock."
          className="font-mono text-xs"
        />
      </CardContent>
    </Card>
  );
}
