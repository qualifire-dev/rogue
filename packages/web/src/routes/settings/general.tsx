import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useTheme } from "@/components/theme-provider";
import { useConfig } from "@/stores/config";

export const Route = createFileRoute("/settings/general")({
  component: GeneralSettingsPage,
});

function GeneralSettingsPage() {
  const cfg = useConfig();
  const { theme, toggle } = useTheme();
  const [serverUrl, setServerUrl] = useState(cfg.serverUrl);
  const [pinging, setPinging] = useState(false);

  const ping = async () => {
    setPinging(true);
    const base = serverUrl.trim().replace(/\/$/, "");
    if (!base) {
      toast.error("Enter a server URL first.");
      setPinging(false);
      return;
    }
    if (!/^https?:\/\//i.test(base)) {
      toast.error("URL must start with http:// or https://");
      setPinging(false);
      return;
    }
    const ctrl = new AbortController();
    const timeout = window.setTimeout(() => ctrl.abort(), 5000);
    try {
      const res = await fetch(`${base}/api/v1/health`, {
        method: "GET",
        signal: ctrl.signal,
        headers: { accept: "application/json" },
        cache: "no-store",
      });
      if (!res.ok) {
        toast.error(`Server unreachable: HTTP ${res.status} ${res.statusText}`);
        return;
      }
      const body = (await res.json().catch(() => null)) as { status?: string } | null;
      if (body?.status === "healthy") {
        toast.success("Server reachable");
      } else {
        toast.error("Endpoint responded but did not look like a Rogue server.");
      }
    } catch (e) {
      const msg =
        (e as Error).name === "AbortError"
          ? "timed out after 5s"
          : (e as Error).message || "network error";
      toast.error(`Server unreachable: ${msg}`);
    } finally {
      window.clearTimeout(timeout);
      setPinging(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Server</CardTitle>
          <CardDescription>The Rogue API endpoint the SPA talks to.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="server-url">Server URL</Label>
            <div className="flex gap-2">
              <Input
                id="server-url"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                placeholder="http://127.0.0.1:8000"
              />
              <Button
                variant="outline"
                onClick={() => {
                  cfg.setServerUrl(serverUrl);
                  toast.success("Server URL saved");
                }}
              >
                Save
              </Button>
              <Button onClick={ping} disabled={pinging}>
                {pinging ? "Pinging…" : "Test"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Light or dark theme.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={toggle}>
            Switch to {theme === "dark" ? "light" : "dark"} mode
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
