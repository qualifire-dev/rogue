import { createFileRoute } from "@tanstack/react-router";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PROVIDERS } from "@/components/model-picker/catalog";
import { useConfig, type Provider } from "@/stores/config";

export const Route = createFileRoute("/settings/api-keys")({
  component: ApiKeysSettingsPage,
});

function ApiKeysSettingsPage() {
  const cfg = useConfig();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Provider API keys</CardTitle>
          <CardDescription>
            Stored locally in your browser. Sent per-request to your local Rogue server only.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {PROVIDERS.map((p) => (
            <div key={p.id} className="grid grid-cols-[10rem_1fr] items-center gap-3">
              <Label className="text-sm">
                {p.name}
                <span className="ml-2 text-[10px] uppercase tracking-wider text-muted-foreground">
                  {p.id}
                </span>
              </Label>
              <Input
                type="password"
                value={cfg.apiKeys[p.id as Provider] ?? ""}
                placeholder={p.fields.find((f) => f.key === "apiKey")?.placeholder ?? "—"}
                onChange={(e) => cfg.setApiKey(p.id as Provider, e.target.value)}
              />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
