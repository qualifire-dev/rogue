import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";

import { ConfirmDialog } from "@/components/confirm-dialog";
import { EmptyState } from "@/components/empty-state";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { useScenariosStore } from "@/stores/scenarios";
import type { Scenario } from "@/api/types";

export const Route = createFileRoute("/scenarios/")({
  component: ScenariosPage,
});

function ScenariosPage() {
  const { scenarios, add, remove, update, setAll } = useScenariosStore();
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [deletingIndex, setDeletingIndex] = useState<number | null>(null);
  const editing = editingIndex !== null ? scenarios[editingIndex] : null;
  const deleting = deletingIndex !== null ? scenarios[deletingIndex] : null;

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(scenarios, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "scenarios.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const importJson = async (file: File) => {
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      if (!Array.isArray(parsed)) throw new Error("Expected an array");
      setAll(parsed as Scenario[]);
      toast.success(`Imported ${parsed.length} scenarios`);
    } catch (e) {
      toast.error(`Import failed: ${(e as Error).message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Scenarios</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            The test scenarios used by policy-mode evaluations. Compatible with the TUI&apos;s{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">.rogue/scenarios.json</code>.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button asChild variant="outline" size="sm">
            <Link to="/scenarios/interview">Interview</Link>
          </Button>
          <Button variant="outline" size="sm" onClick={exportJson}>
            Export
          </Button>
          <label className="cursor-pointer">
            <input
              type="file"
              accept="application/json"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) importJson(f);
              }}
            />
            <span className="inline-flex h-8 items-center rounded-md border border-border bg-background px-3 text-xs font-medium hover:bg-accent">
              Import
            </span>
          </label>
          <Button
            size="sm"
            onClick={() => {
              add({
                scenario: "New scenario",
                multi_turn: true,
                max_turns: 10,
                expected_outcome: "",
              });
              setEditingIndex(scenarios.length);
            }}
          >
            Add
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">All scenarios ({scenarios.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {scenarios.length === 0 ? (
            <div className="p-6">
              <EmptyState
                illustration="inventory"
                title="No scenarios yet"
                description="Add one manually, import from a JSON file, or generate a set via the Interview."
                action={
                  <Button
                    onClick={() => {
                      add({
                        scenario: "New scenario",
                        multi_turn: true,
                        max_turns: 10,
                        expected_outcome: "",
                      });
                      setEditingIndex(scenarios.length);
                    }}
                  >
                    Add scenario
                  </Button>
                }
              />
            </div>
          ) : (
            <ul className="divide-y divide-border/60">
              {scenarios.map((s, i) => (
                <li
                  key={i}
                  className="flex items-center justify-between gap-4 px-6 py-3 hover:bg-card/40"
                >
                  <button onClick={() => setEditingIndex(i)} className="flex-1 text-left text-sm">
                    <div className="line-clamp-1 font-medium">{s.scenario}</div>
                    <div className="mt-0.5 text-xs text-muted-foreground">
                      {[
                        s.multi_turn ? `multi-turn · max ${s.max_turns ?? 10}` : "single-turn",
                        (s.attempts ?? 1) > 1 ? `${s.attempts}× attempts` : null,
                        typeof s.temperature === "number" ? `temp ${s.temperature}` : null,
                      ]
                        .filter(Boolean)
                        .join(" · ")}
                    </div>
                  </button>
                  <Button
                    variant="destructive"
                    size="sm"
                    className="h-7 px-2 text-xs"
                    onClick={() => setDeletingIndex(i)}
                  >
                    Delete
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Sheet open={editingIndex !== null} onOpenChange={(o) => !o && setEditingIndex(null)}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Edit scenario</SheetTitle>
            <SheetDescription>Changes are saved to local storage.</SheetDescription>
          </SheetHeader>
          {editing && editingIndex !== null && (
            <ScenarioForm value={editing} onChange={(updated) => update(editingIndex, updated)} />
          )}
        </SheetContent>
      </Sheet>

      <ConfirmDialog
        open={deletingIndex !== null}
        onOpenChange={(open) => !open && setDeletingIndex(null)}
        title="Delete scenario?"
        description={
          deleting ? (
            <>
              <span className="block">This will permanently remove:</span>
              <span className="mt-2 block rounded-md border border-border/60 bg-card/40 px-3 py-2 text-foreground">
                {deleting.scenario}
              </span>
            </>
          ) : null
        }
        confirmLabel="Delete"
        destructive
        onConfirm={() => {
          if (deletingIndex !== null) remove(deletingIndex);
          setDeletingIndex(null);
        }}
      />
    </div>
  );
}

function ScenarioForm({ value, onChange }: { value: Scenario; onChange: (s: Scenario) => void }) {
  return (
    <div className="mt-6 space-y-4">
      <div className="space-y-1.5">
        <Label>Scenario</Label>
        <Textarea
          rows={4}
          value={value.scenario}
          onChange={(e) => onChange({ ...value, scenario: e.target.value })}
        />
      </div>
      <div className="space-y-1.5">
        <Label>Expected outcome</Label>
        <Textarea
          rows={3}
          value={value.expected_outcome ?? ""}
          onChange={(e) => onChange({ ...value, expected_outcome: e.target.value })}
        />
      </div>
      <div className="flex items-center justify-between rounded-md border border-border/60 px-3 py-2">
        <Label>Multi-turn</Label>
        <Switch
          checked={value.multi_turn ?? true}
          onCheckedChange={(c) => onChange({ ...value, multi_turn: c })}
        />
      </div>
      {value.multi_turn !== false && (
        <div className="space-y-1.5">
          <Label>Max turns ({value.max_turns ?? 10})</Label>
          <Input
            type="range"
            min={1}
            max={100}
            value={value.max_turns ?? 10}
            onChange={(e) => onChange({ ...value, max_turns: Number(e.target.value) })}
          />
        </div>
      )}
      <div className="space-y-1.5">
        <Label htmlFor="scenario-attempts">Attempts ({value.attempts ?? 1})</Label>
        <Input
          id="scenario-attempts"
          type="number"
          min={1}
          max={20}
          step={1}
          value={value.attempts ?? 1}
          onChange={(e) => {
            const raw = Number(e.target.value);
            // Clamp + drop NaN / float input. The server enforces ge=1/le=20
            // but we keep the UI sane too so users see the same number that
            // gets persisted.
            const next = Number.isFinite(raw) ? Math.max(1, Math.min(20, Math.round(raw))) : 1;
            onChange({ ...value, attempts: next });
          }}
        />
        <p className="text-xs text-muted-foreground">
          Run this scenario N times to test robustness against sampling variation. The scenario
          passes only if every attempt passes.
        </p>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="scenario-temperature">Temperature (optional)</Label>
        <Input
          id="scenario-temperature"
          type="number"
          min={0}
          max={2}
          step={0.1}
          placeholder="0.7 (driver default)"
          value={typeof value.temperature === "number" ? value.temperature : ""}
          onChange={(e) => {
            const raw = e.target.value;
            // Empty string → fall back to driver default (null = unset).
            // Anything else → clamp to 0..2 and round to 1 decimal so the
            // saved value matches the input step.
            if (raw === "") {
              onChange({ ...value, temperature: null });
              return;
            }
            const num = Number(raw);
            if (!Number.isFinite(num)) return;
            const clamped = Math.max(0, Math.min(2, num));
            onChange({ ...value, temperature: Math.round(clamped * 10) / 10 });
          }}
        />
        <p className="text-xs text-muted-foreground">
          Override the multi-turn driver's sampling temperature for this scenario. Leave blank to
          use the driver default (0.7). Higher values produce more variation between attempts.
        </p>
      </div>
    </div>
  );
}
