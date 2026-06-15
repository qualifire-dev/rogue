import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { IconWand } from "@tabler/icons-react";
import { useMemo } from "react";
import { toast } from "sonner";

import { useGenerateResilienceScenarios, useStartResilience } from "@/api/queries";
import { BusinessContextCard } from "@/components/business-context-card";
import { ModelPickerButton } from "@/components/model-picker/dialog";
import { InjectorCatalogPane } from "@/components/resilience/injector-catalog-pane";
import { TargetAgentForm } from "@/components/target-agent-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  ARCHITECTURE_CATALOG,
  BASIC_INJECTORS,
  FULL_INJECTORS,
  type ExperimentPreset,
  getArchitecture,
} from "@/lib/resilience-catalog";
import { authNeedsCredentials, protocolNeedsAgentUrl } from "@/lib/protocols";
import { cn } from "@/lib/utils";
import { useConfig } from "@/stores/config";
import { useResilienceConfig } from "@/stores/resilience";
import { AUTH_TYPE_LABELS } from "@/api/types";

export const Route = createFileRoute("/resilience/configure")({
  component: ResilienceConfigurePage,
});

const PRESETS: { id: ExperimentPreset; label: string; description: string }[] = [
  {
    id: "basic",
    label: "Basic",
    description: "Policy violation + tool misuse on single agent",
  },
  {
    id: "full",
    label: "Full",
    description: "All built-in injectors including premium gradual goal drift",
  },
  {
    id: "custom",
    label: "Custom",
    description: "Pick injectors and architecture manually",
  },
];

function ResilienceConfigurePage() {
  const cfg = useConfig();
  const navigate = useNavigate();
  const start = useStartResilience();
  const generateScenarios = useGenerateResilienceScenarios();
  const rs = useResilienceConfig();

  const agent = cfg.lastResilienceAgent;
  const setAgent = cfg.setLastResilienceAgent;

  const isPython = agent.protocol === "python";
  const needsAgentUrl = protocolNeedsAgentUrl(agent.protocol);
  const isLocked = rs.preset !== "custom";
  const arch = getArchitecture(rs.architecture);

  const onPresetChange = (next: ExperimentPreset) => {
    rs.setPreset(next);
    if (next === "basic") {
      rs.setInjectors([...BASIC_INJECTORS]);
    } else if (next === "full") {
      rs.setInjectors([...FULL_INJECTORS]);
    }
  };

  const onArchitectureChange = (id: string) => {
    rs.setArchitecture(id);
    const profile = getArchitecture(id);
    if (profile) {
      rs.setTargetAgentId(
        profile.agentIds.includes(rs.targetAgentId) ? rs.targetAgentId : (profile.agentIds[0] ?? "default"),
      );
      rs.setConcurrentTargetAgentIds(
        rs.concurrentTargetAgentIds.filter((a) => profile.agentIds.includes(a)),
      );
    }
  };

  const selectedInjectors = useMemo(() => new Set(rs.injectors), [rs.injectors]);
  const expanded = useMemo(
    () => new Set(rs.expandedInjectorCategories),
    [rs.expandedInjectorCategories],
  );
  const concurrentSet = useMemo(
    () => new Set(rs.concurrentTargetAgentIds),
    [rs.concurrentTargetAgentIds],
  );

  const applyGeneratedScenario = async () => {
    const context = cfg.businessContext.trim();
    if (!context) {
      toast.error("Add business context before generating scenarios");
      return;
    }
    if (!cfg.judgeModel.trim()) {
      toast.error("Select a judge model first");
      return;
    }
    try {
      const res = await generateScenarios.mutateAsync({
        business_context: context,
        model: cfg.judgeModel,
        api_key: cfg.apiKeys[cfg.judgeProvider],
        api_base: cfg.judgeApiBase,
        count: 5,
      });
      const first = res.scenarios[0];
      if (!first) {
        toast.error("No scenarios returned");
        return;
      }
      rs.setPreset("custom");
      rs.setInjectors(first.injectors);
      rs.setArchitecture(first.architecture);
      rs.setTargetAgentId(first.target_agent_id);
      rs.setConcurrentTargetAgentIds([]);
      rs.setBaselineTask(first.baseline_task);
      rs.setRecoveryTask(first.recovery_task);
      toast.success(`Applied scenario: ${first.name}`);
    } catch (e) {
      toast.error(`Generate failed: ${(e as Error).message}`);
    }
  };

  const submit = async () => {
    if (rs.injectors.length === 0) {
      toast.error("Select at least one injector");
      return;
    }
    if (isPython && !agent.pythonFile.trim()) {
      toast.error("A Python entrypoint file is required for the python protocol.");
      return;
    }
    if (needsAgentUrl && !agent.agentUrl.trim()) {
      toast.error("An agent URL is required for the selected protocol.");
      return;
    }
    if (authNeedsCredentials(agent.authType) && !agent.credentials.trim()) {
      toast.error(`${AUTH_TYPE_LABELS[agent.authType]} requires credentials.`);
      return;
    }
    if (!cfg.judgeModel.trim()) {
      toast.error("Select a judge model");
      return;
    }
    try {
      cfg.setLastResilienceAgent(agent);
      const concurrent =
        rs.concurrentTargetAgentIds.length >= 2 ? rs.concurrentTargetAgentIds : undefined;
      const res = await start.mutateAsync({
        resilience_config: {
          injectors: rs.injectors,
          architecture: rs.architecture,
          target_agent_id: rs.targetAgentId,
          concurrent_target_agent_ids: concurrent,
          experiments_per_injector: rs.experimentsPerInjector,
          baseline_task: rs.baselineTask,
          recovery_task: rs.recoveryTask,
          use_heuristics: rs.useHeuristics,
          enable_checkpoint_recovery: rs.enableCheckpointRecovery,
          checkpoint_thread_id: rs.checkpointThreadId.trim() || undefined,
          min_resilience_score: rs.minResilienceScore ?? undefined,
        },
        evaluated_agent_url: needsAgentUrl ? agent.agentUrl : undefined,
        evaluated_agent_protocol: agent.protocol,
        evaluated_agent_transport: agent.transport || undefined,
        evaluated_agent_auth_type: agent.authType,
        evaluated_agent_auth_credentials: authNeedsCredentials(agent.authType)
          ? agent.credentials.trim()
          : undefined,
        python_entrypoint_file: isPython ? agent.pythonFile.trim() : undefined,
        judge_llm: cfg.judgeModel,
        judge_llm_api_key: cfg.apiKeys[cfg.judgeProvider],
        judge_llm_api_base: cfg.judgeApiBase,
        business_context: cfg.businessContext.trim() || "",
      });
      toast.success("Resilience experiment started");
      navigate({ to: "/resilience/$jobId", params: { jobId: res.job_id } });
    } catch (e) {
      toast.error(`Failed: ${(e as Error).message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Configure resilience experiment</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Inject faults into your agent system and measure detection, containment, and recovery.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ModelPickerButton
            label="Judge"
            value={{
              provider: cfg.judgeProvider,
              model: cfg.judgeModel,
              apiKey: cfg.apiKeys[cfg.judgeProvider],
              apiBase: cfg.judgeApiBase,
            }}
            onChange={(v) => {
              cfg.setJudgeProvider(v.provider);
              cfg.setJudgeModel(v.model);
              cfg.setJudgeApiBase(v.apiBase);
              if (v.apiKey) cfg.setApiKey(v.provider, v.apiKey);
            }}
          />
          <Button onClick={submit} disabled={start.isPending}>
            {start.isPending ? "Starting…" : "Run experiment"}
          </Button>
        </div>
      </div>

      <Card className="border-primary/30 bg-primary/5">
        <CardHeader className="py-3">
          <CardTitle className="text-sm">Resilience vs Red Team (Robustness)</CardTitle>
          <CardDescription>
            Red Team tests external adversarial attacks on your agent. Resilience tests internal
            faults — when an agent in your multi-agent system goes rogue. Use both for defense in
            depth.
          </CardDescription>
        </CardHeader>
      </Card>

      <TargetAgentForm
        value={agent}
        onChange={setAgent}
        description="Python entrypoint or remote agent under test."
      />

      <BusinessContextCard />

      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={applyGeneratedScenario}
          disabled={generateScenarios.isPending}
        >
          <IconWand className="mr-2 size-4" />
          {generateScenarios.isPending ? "Generating…" : "Generate scenario from context"}
        </Button>
        <span className="text-xs text-muted-foreground">
          Uses business context + judge model to suggest injectors and tasks.
        </span>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Experiment preset</CardTitle>
          <CardDescription>Basic and Full apply curated injector sets. Custom unlocks the catalog.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-3">
            {PRESETS.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => onPresetChange(t.id)}
                className={cn(
                  "cursor-pointer rounded-lg border px-4 py-3 text-left transition-colors",
                  rs.preset === t.id
                    ? "border-primary bg-primary/10"
                    : "border-border/60 hover:border-primary/50",
                )}
              >
                <div className="text-sm font-semibold">{t.label}</div>
                <div className="mt-1 text-xs text-muted-foreground">{t.description}</div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <InjectorCatalogPane
          selected={selectedInjectors}
          expanded={expanded}
          disabled={isLocked}
          onToggleItem={rs.toggleInjector}
          onToggleCategory={rs.toggleInjectorCategory}
        />

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Architecture</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {ARCHITECTURE_CATALOG.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  onClick={() => onArchitectureChange(a.id)}
                  className={cn(
                    "w-full rounded-lg border px-3 py-2 text-left text-sm transition-colors",
                    rs.architecture === a.id
                      ? "border-primary bg-primary/10"
                      : "border-border/60 hover:border-primary/50",
                  )}
                >
                  <div className="font-medium">{a.name}</div>
                  <div className="text-xs text-muted-foreground">{a.description}</div>
                </button>
              ))}
              <div className="space-y-2 pt-2">
                <Label htmlFor="target-agent">Primary injection target</Label>
                <Input
                  id="target-agent"
                  value={rs.targetAgentId}
                  onChange={(e) => rs.setTargetAgentId(e.target.value)}
                  placeholder={arch?.agentIds[0] ?? "default"}
                  className="font-mono text-xs"
                />
              </div>
              {arch?.isMultiAgent && (
                <div className="space-y-2">
                  <Label>Concurrent targets (select 2+ for parallel injection)</Label>
                  <div className="flex flex-wrap gap-2">
                    {arch.agentIds.map((id) => (
                      <button
                        key={id}
                        type="button"
                        onClick={() => rs.toggleConcurrentTarget(id)}
                        className={cn(
                          "rounded-md border px-2 py-1 font-mono text-xs transition-colors",
                          concurrentSet.has(id)
                            ? "border-primary bg-primary/15"
                            : "border-border/60 hover:border-primary/40",
                        )}
                      >
                        {id}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="exp-per-inj">Experiments per injector</Label>
                <Input
                  id="exp-per-inj"
                  type="number"
                  min={1}
                  max={10}
                  value={rs.experimentsPerInjector}
                  onChange={(e) => rs.setExperimentsPerInjector(Number(e.target.value))}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Options</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="heuristics">Use heuristics (no LLM judge calls)</Label>
                <Switch
                  id="heuristics"
                  checked={rs.useHeuristics}
                  onCheckedChange={rs.setUseHeuristics}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="checkpoints">Enable checkpoint recovery</Label>
                <Switch
                  id="checkpoints"
                  checked={rs.enableCheckpointRecovery}
                  onCheckedChange={rs.setEnableCheckpointRecovery}
                />
              </div>
              {rs.enableCheckpointRecovery && (
                <div className="space-y-2">
                  <Label htmlFor="thread-id">Checkpoint thread ID</Label>
                  <Input
                    id="thread-id"
                    value={rs.checkpointThreadId}
                    onChange={(e) => rs.setCheckpointThreadId(e.target.value)}
                    placeholder="resilience-thread-1"
                    className="font-mono text-xs"
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="min-score">Minimum resilience score (optional CI gate)</Label>
                <Input
                  id="min-score"
                  type="number"
                  min={0}
                  max={100}
                  placeholder="e.g. 60"
                  value={rs.minResilienceScore ?? ""}
                  onChange={(e) => {
                    const raw = e.target.value.trim();
                    rs.setMinResilienceScore(raw === "" ? null : Number(raw));
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
