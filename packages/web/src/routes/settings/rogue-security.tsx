import { createFileRoute } from "@tanstack/react-router";
import { IconAlertTriangle } from "@tabler/icons-react";

import { useServerEnvDefaults } from "@/api/queries";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useConfig } from "@/stores/config";

export const Route = createFileRoute("/settings/rogue-security")({
  component: RogueSecuritySettingsPage,
});

const CLOUD_BASE_URL = "https://app.rogue.security";

function RogueSecuritySettingsPage() {
  const cfg = useConfig();
  const env = useServerEnvDefaults();

  // What the server WILL hit if the user leaves "Base URL" empty:
  // - the ``ROGUE_SECURITY_URL`` env var if set on the server process
  // - otherwise, the hardcoded production cloud URL
  // We distinguish them so we can warn the user when an env var is
  // silently overriding their intended endpoint.
  const envOverride = env.data?.rogue_security_base_url ?? null;
  const effectiveFallback = envOverride ?? CLOUD_BASE_URL;
  const userValue = cfg.rogueSecurityBaseUrl?.trim() ?? "";
  const effective = userValue || effectiveFallback;

  // Highlight only when the env actively replaces the cloud default AND
  // the user hasn't typed an override of their own — that's the case
  // where reports are silently going somewhere unexpected.
  const envIsHijacking = !!envOverride && !userValue;

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

              {envIsHijacking && (
                <div className="flex items-start gap-3 rounded-md border border-[var(--chart-3)]/40 bg-[var(--chart-3)]/10 p-3 text-sm">
                  <IconAlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--chart-3)]" />
                  <div className="flex-1 space-y-1">
                    <div className="font-medium">Env var is overriding the destination</div>
                    <div className="text-xs text-muted-foreground">
                      The server is launched with{" "}
                      <code className="rounded bg-muted px-1 py-0.5 text-[10px]">
                        ROGUE_SECURITY_URL={envOverride}
                      </code>
                      . Reports go there instead of the cloud. To send to{" "}
                      <code className="rounded bg-muted px-1 py-0.5 text-[10px]">
                        {CLOUD_BASE_URL}
                      </code>{" "}
                      anyway, set the Base URL below — your value wins.
                    </div>
                    <div className="pt-1">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          cfg.setRogueSecurity(true, cfg.rogueSecurityApiKey, CLOUD_BASE_URL)
                        }
                      >
                        Use cloud ({CLOUD_BASE_URL})
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <Label htmlFor="rs-base">Base URL (optional)</Label>
                <Input
                  id="rs-base"
                  placeholder={effectiveFallback}
                  value={cfg.rogueSecurityBaseUrl ?? ""}
                  onChange={(e) =>
                    cfg.setRogueSecurity(true, cfg.rogueSecurityApiKey, e.target.value)
                  }
                />
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span>
                    Reports will be sent to{" "}
                    <code className="rounded bg-muted px-1 py-0.5 text-[10px]">{effective}</code>
                    {!userValue && envOverride && (
                      <span className="ml-1 text-[var(--chart-3)]">(via env var)</span>
                    )}
                    {!userValue && !envOverride && (
                      <span className="ml-1 opacity-70">(default)</span>
                    )}
                    {userValue && <span className="ml-1 opacity-70">(your override)</span>}
                  </span>
                  {userValue && (
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      className="h-6 px-2 text-xs"
                      onClick={() => cfg.setRogueSecurity(true, cfg.rogueSecurityApiKey, undefined)}
                    >
                      Clear override
                    </Button>
                  )}
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
