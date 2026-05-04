import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useConfig } from "@/stores/config";
import { useScenariosStore } from "@/stores/scenarios";

export const Route = createFileRoute("/settings/backup")({
  component: BackupPage,
});

function BackupPage() {
  const cfg = useConfig();
  const scenarios = useScenariosStore((s) => s.scenarios);
  const setAllScenarios = useScenariosStore((s) => s.setAll);

  const exportConfig = () => {
    const payload = {
      version: 1,
      config: cfg,
      scenarios,
    };
    download("rogue-backup.json", JSON.stringify(payload, null, 2));
    toast.success("Backup exported");
  };

  const importConfig = async (file: File) => {
    try {
      const text = await file.text();
      const payload = JSON.parse(text) as { config?: unknown; scenarios?: unknown };
      if (payload.config && typeof payload.config === "object") {
        Object.assign(useConfig.getState(), payload.config);
      }
      if (Array.isArray(payload.scenarios)) {
        setAllScenarios(payload.scenarios);
      }
      toast.success("Backup imported");
    } catch (e) {
      toast.error(`Import failed: ${(e as Error).message}`);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Backup &amp; restore</CardTitle>
          <CardDescription>
            Round-trip your client config and scenarios as a JSON file. Use this to sync between
            machines or share with a teammate.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={exportConfig}>
            Export JSON
          </Button>
          <label className="cursor-pointer">
            <input
              type="file"
              accept="application/json"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) importConfig(f);
              }}
            />
            <span className="inline-flex h-9 items-center rounded-md border border-border bg-background px-4 text-sm font-medium hover:bg-accent">
              Import JSON
            </span>
          </label>
          <Button
            variant="outline"
            onClick={() => {
              cfg.reset();
              toast.success("Settings reset to defaults");
            }}
          >
            Reset settings
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function download(name: string, body: string) {
  const blob = new Blob([body], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
