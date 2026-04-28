import { IconCheck, IconChevronRight, IconCircleFilled, IconRefresh } from "@tabler/icons-react";
import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { findProvider, PROVIDERS, type ProviderInfo } from "./catalog";
import { modelsDevProviderId, useRecommendedModels } from "@/lib/models-dev";
import { cn } from "@/lib/utils";
import { useConfig, type Provider } from "@/stores/config";

export interface ModelPickerValue {
  provider: Provider;
  model: string;
  apiKey?: string;
  apiBase?: string;
  awsAccessKeyId?: string;
  awsSecretAccessKey?: string;
  awsRegion?: string;
  azureEndpoint?: string;
  azureApiVersion?: string;
  azureDeployment?: string;
}

interface ModelPickerButtonProps {
  label: string;
  value: ModelPickerValue;
  onChange: (v: ModelPickerValue) => void;
}

export function ModelPickerButton({ label, value, onChange }: ModelPickerButtonProps) {
  const [open, setOpen] = useState(false);
  const provider = findProvider(value.provider);

  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <button
            type="button"
            className="flex w-full cursor-pointer items-center justify-between gap-3 rounded-md border border-border bg-input px-3 py-2 text-left text-sm shadow-sm transition-colors hover:border-primary/40"
          >
            <span className="flex min-w-0 flex-1 flex-col">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {provider.name}
              </span>
              <span className="truncate font-mono text-sm">{value.model || "—"}</span>
            </span>
            <IconChevronRight className="h-4 w-4 -rotate-90 text-muted-foreground" />
          </button>
        </DialogTrigger>
        <DialogContent className="max-w-2xl">
          <ModelPickerContent
            initial={value}
            onCancel={() => setOpen(false)}
            onSave={(v) => {
              onChange(v);
              setOpen(false);
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}

type ConfiguredCheck = (p: ProviderInfo, draft: Partial<ModelPickerValue>) => boolean;

const isConfigured: ConfiguredCheck = (p, draft) => {
  // Treat the provider as configured when every required field is satisfied
  // either by the draft or by the persisted config store.
  const cfg = useConfig.getState();
  const apiKeyFromStore = cfg.apiKeys[p.id];
  const apiBaseFromStore = cfg.apiBases?.[p.id];
  for (const field of p.fields) {
    if (!field.required) continue;
    const draftValue = (draft as Record<string, unknown>)[field.key];
    const fallback =
      field.key === "apiKey"
        ? apiKeyFromStore
        : field.key === "apiBase"
          ? apiBaseFromStore
          : undefined;
    if (!draftValue && !fallback) return false;
  }
  return true;
};

function ModelPickerContent({
  initial,
  onSave,
  onCancel,
}: {
  initial: ModelPickerValue;
  onSave: (v: ModelPickerValue) => void;
  onCancel: () => void;
}) {
  const cfg = useConfig();
  const recommended = useRecommendedModels();
  const [draft, setDraft] = useState<ModelPickerValue>(initial);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState<Provider | null>(initial.provider ?? null);

  // Reset when reopened with a new value.
  useEffect(() => setDraft(initial), [initial]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return PROVIDERS.map((p) => {
      const apiKey = draft.provider === p.id ? draft.apiKey : cfg.apiKeys[p.id];
      const apiBase = draft.provider === p.id ? draft.apiBase : cfg.apiBases?.[p.id];
      const draftForProvider: Partial<ModelPickerValue> = { apiKey, apiBase };
      const configured = isConfigured(p, draftForProvider);
      const modelsDevId = modelsDevProviderId(p.id);
      const remoteModels = modelsDevId ? (recommended.byProvider[modelsDevId] ?? []) : [];
      const fallbackModels = p.models;
      const merged = Array.from(new Set([...remoteModels, ...fallbackModels]));
      const models = q
        ? merged.filter((m) => m.toLowerCase().includes(q) || p.name.toLowerCase().includes(q))
        : merged;
      const matchesSearch = !q || p.name.toLowerCase().includes(q) || models.length > 0;
      return { provider: p, configured, models, matchesSearch };
    }).filter((r) => r.matchesSearch);
  }, [search, draft, cfg.apiKeys, cfg.apiBases, recommended.byProvider]);

  const draftProvider = findProvider(draft.provider);
  const draftConfigured = isConfigured(draftProvider, draft);
  const canUseModel = !!draft.model && draftConfigured;

  return (
    <div className="flex flex-col">
      <DialogHeader>
        <DialogTitle>LLM Provider Configuration</DialogTitle>
        <DialogDescription>
          Pick a provider, configure credentials, and select a model.{" "}
          <span className="text-muted-foreground">✓ = configured · ● = currently selected</span>
        </DialogDescription>
      </DialogHeader>

      <div className="flex items-center gap-2 py-3">
        <Input
          autoFocus
          placeholder="Type to search models..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <Button
          type="button"
          size="icon"
          variant="outline"
          title="Refresh recommended models from models.dev"
          onClick={() => recommended.refresh()}
          disabled={recommended.loading}
        >
          <IconRefresh className={cn("h-4 w-4", recommended.loading && "animate-spin")} />
        </Button>
      </div>

      <ScrollArea className="h-[22rem] rounded-md border border-border/60">
        <ul className="divide-y divide-border/40">
          {filtered.map(({ provider: p, configured, models }) => {
            const open = expanded === p.id;
            const usingThisProvider = draft.provider === p.id;
            return (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => setExpanded((cur) => (cur === p.id ? null : p.id))}
                  className="flex w-full cursor-pointer items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-accent/40"
                >
                  <IconChevronRight
                    className={cn(
                      "h-3.5 w-3.5 text-muted-foreground transition-transform",
                      open && "rotate-90",
                    )}
                  />
                  <span className="flex-1 text-sm">
                    <span className="font-medium">{p.name}</span>
                    <span className="ml-2 text-xs text-muted-foreground">{p.description}</span>
                  </span>
                  {configured && <IconCheck className="h-4 w-4 text-[var(--chart-2)]" />}
                  {usingThisProvider && <IconCircleFilled className="h-3 w-3 text-primary" />}
                </button>

                {open && (
                  <div className="space-y-3 bg-background/30 px-4 py-3">
                    <CredentialsBlock provider={p} draft={draft} setDraft={setDraft} />
                    {configured ? (
                      <ModelList
                        provider={p}
                        models={models}
                        currentModel={draft.model}
                        currentProvider={draft.provider}
                        onPick={(modelId) => setDraft({ ...draft, provider: p.id, model: modelId })}
                      />
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        Provide the required credentials above to unlock this provider&apos;s
                        models.
                      </p>
                    )}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      </ScrollArea>

      {recommended.error && (
        <p className="mt-2 text-xs text-muted-foreground">
          Couldn&apos;t reach models.dev — using built-in suggestions.
        </p>
      )}

      <div className="flex items-center justify-between gap-2 border-t border-border/60 pt-4">
        <Button variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
        <div className="flex items-center gap-2">
          {!canUseModel && draft.model && !draftConfigured && (
            <span className="text-xs text-destructive">
              Configure credentials for {draftProvider.name} first
            </span>
          )}
          <Button onClick={() => onSave(draft)} disabled={!canUseModel}>
            <IconCheck className="mr-1 h-3.5 w-3.5" />
            Use model
          </Button>
        </div>
      </div>
    </div>
  );
}

function CredentialsBlock({
  provider,
  draft,
  setDraft,
}: {
  provider: ProviderInfo;
  draft: ModelPickerValue;
  setDraft: (v: ModelPickerValue) => void;
}) {
  const cfg = useConfig.getState();
  return (
    <div className="space-y-2 rounded-md border border-border/60 bg-card/40 p-3">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        Credentials
      </div>
      {provider.fields.map((f) => {
        const fallback =
          f.key === "apiKey"
            ? cfg.apiKeys[provider.id]
            : f.key === "apiBase"
              ? cfg.apiBases?.[provider.id]
              : undefined;
        const value =
          (draft.provider === provider.id
            ? (draft as unknown as Record<string, unknown>)[f.key]
            : undefined) ??
          fallback ??
          "";
        const missing = f.required && !value;
        return (
          <div key={f.key} className="space-y-1">
            <Label htmlFor={`${provider.id}-${f.key}`} className="text-xs">
              {f.label}
              {f.required && <span className="ml-1 text-destructive">*</span>}
            </Label>
            <Input
              id={`${provider.id}-${f.key}`}
              type={f.type}
              placeholder={f.placeholder}
              value={String(value)}
              className={cn(
                "h-8 text-xs",
                missing && "border-destructive/50 focus-visible:ring-destructive/40",
              )}
              onChange={(e) =>
                setDraft({
                  ...draft,
                  provider: provider.id,
                  [f.key]: e.target.value,
                } as ModelPickerValue)
              }
            />
            {missing && <p className="text-[11px] text-destructive">Required</p>}
          </div>
        );
      })}
    </div>
  );
}

function ModelList({
  provider,
  models,
  currentModel,
  currentProvider,
  onPick,
}: {
  provider: ProviderInfo;
  models: string[];
  currentModel: string;
  currentProvider: Provider;
  onPick: (id: string) => void;
}) {
  if (models.length === 0) {
    return (
      <p className="text-xs text-muted-foreground">
        No suggestions available — type a model id below.
      </p>
    );
  }
  return (
    <div className="space-y-2">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        Models ({models.length})
      </div>
      <div className="max-h-64 overflow-y-auto rounded-md border border-border/60">
        <ul className="divide-y divide-border/40">
          {models.map((m) => {
            const active = currentProvider === provider.id && currentModel === m;
            return (
              <li key={m}>
                <button
                  type="button"
                  onClick={() => onPick(m)}
                  className={cn(
                    "flex w-full cursor-pointer items-center justify-between gap-2 px-3 py-1.5 text-left font-mono text-xs transition-colors hover:bg-accent/40",
                    active && "bg-primary/10 text-foreground",
                  )}
                >
                  <span className="truncate">{m}</span>
                  {active && <IconCircleFilled className="h-2.5 w-2.5 shrink-0 text-primary" />}
                </button>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
