import { createFileRoute } from "@tanstack/react-router";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useConfig } from "@/stores/config";

export const Route = createFileRoute("/settings/rogue-security")({
  component: RogueSecuritySettingsPage,
});

function RogueSecuritySettingsPage() {
  const cfg = useConfig();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Rogue Security</CardTitle>
          <CardDescription>
            Auto-report scan summaries to the Rogue Security platform.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="rs-toggle">Enable reporting</Label>
              <p className="text-xs text-muted-foreground">
                When enabled, evaluation and scan summaries are pushed to your Rogue Security
                workspace.
              </p>
            </div>
            <Switch
              id="rs-toggle"
              checked={cfg.rogueSecurityEnabled}
              onCheckedChange={(c) =>
                cfg.setRogueSecurity(c, cfg.rogueSecurityApiKey, cfg.rogueSecurityBaseUrl)
              }
            />
          </div>

          {cfg.rogueSecurityEnabled && (
            <>
              <div className="space-y-2">
                <Label htmlFor="rs-key">Rogue Security API key</Label>
                <Input
                  id="rs-key"
                  type="password"
                  placeholder="rsk_…"
                  value={cfg.rogueSecurityApiKey ?? ""}
                  onChange={(e) =>
                    cfg.setRogueSecurity(true, e.target.value, cfg.rogueSecurityBaseUrl)
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rs-base">Base URL (optional)</Label>
                <Input
                  id="rs-base"
                  placeholder="https://api.rogue.security"
                  value={cfg.rogueSecurityBaseUrl ?? ""}
                  onChange={(e) =>
                    cfg.setRogueSecurity(true, cfg.rogueSecurityApiKey, e.target.value)
                  }
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
