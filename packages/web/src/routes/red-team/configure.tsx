import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { ModelPickerButton } from "@/components/model-picker/dialog";
import { CatalogPane } from "@/components/red-team/catalog-pane";
import { FrameworksDialog } from "@/components/red-team/frameworks-dialog";
import {
  DEFAULT_TARGET_AGENT_VALUE,
  TargetAgentForm,
  type TargetAgentValue,
} from "@/components/target-agent-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useStartRedTeam } from "@/api/queries";
import {
  ATTACK_CATALOG,
  BASIC_ATTACKS,
  BASIC_VULNS,
  VULNERABILITY_CATALOG,
  allFreeAttackIds,
  allFreeVulnIds,
  totalAttacks,
  totalVulns,
} from "@/lib/red-team-catalog";
import { authNeedsCredentials, protocolNeedsAgentUrl } from "@/lib/protocols";
import { useConfig } from "@/stores/config";
import { useRedTeamConfig } from "@/stores/red-team";
import { cn } from "@/lib/utils";
import { AUTH_TYPE_LABELS, type ScanType } from "@/api/types";

export const Route = createFileRoute("/red-team/configure")({
  component: RedTeamConfigurePage,
});

const SCAN_TYPES: { id: ScanType; label: string; description: string }[] = [
  {
    id: "basic",
    label: "Basic",
    description: "10 prompt + PII vulnerabilities, 5 single-turn attacks",
  },
  {
    id: "full",
    label: "Full",
    description: "All free vulnerabilities and free attacks",
  },
  {
    id: "custom",
    label: "Custom",
    description: "Pick your own from the catalog",
  },
];

function RedTeamConfigurePage() {
  const cfg = useConfig();
  const navigate = useNavigate();
  const start = useStartRedTeam();
  const rt = useRedTeamConfig();

  const [agent, setAgent] = useState<TargetAgentValue>(DEFAULT_TARGET_AGENT_VALUE);

  const isPython = agent.protocol === "python";
  const needsAgentUrl = protocolNeedsAgentUrl(agent.protocol);

  const onScanTypeChange = (next: ScanType) => {
    rt.setScanType(next);
    if (next === "basic") {
      rt.setVulns(BASIC_VULNS);
      rt.setAttacks(BASIC_ATTACKS);
    } else if (next === "full") {
      rt.setVulns(allFreeVulnIds());
      rt.setAttacks(allFreeAttackIds());
    }
  };

  const selectedVulns = useMemo(() => new Set(rt.vulnerabilities), [rt.vulnerabilities]);
  const selectedAttacks = useMemo(() => new Set(rt.attacks), [rt.attacks]);
  const expandedVulnCats = useMemo(
    () => new Set(rt.expandedVulnCategories),
    [rt.expandedVulnCategories],
  );
  const expandedAttackCats = useMemo(
    () => new Set(rt.expandedAttackCategories),
    [rt.expandedAttackCategories],
  );

  const isLocked = rt.scanType !== "custom";

  const submit = async () => {
    if (rt.vulnerabilities.length === 0) {
      toast.error("Select at least one vulnerability");
      return;
    }
    if (rt.attacks.length === 0) {
      toast.error("Select at least one attack");
      return;
    }
    if (isPython && !agent.pythonFile.trim()) {
      toast.error("A Python entrypoint file is required for the python protocol.");
      return;
    }
    if (authNeedsCredentials(agent.authType) && !agent.credentials.trim()) {
      toast.error(`${AUTH_TYPE_LABELS[agent.authType]} requires credentials.`);
      return;
    }
    try {
      const res = await start.mutateAsync({
        red_team_config: {
          scan_type: rt.scanType,
          vulnerabilities: rt.vulnerabilities,
          attacks: rt.attacks,
          attacks_per_vulnerability: rt.attacksPerVulnerability,
          frameworks: rt.frameworks,
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
        attacker_llm: cfg.attackerModel,
        attacker_llm_api_key: cfg.apiKeys[cfg.attackerProvider],
        attacker_llm_api_base: cfg.attackerApiBase,
        rogue_security_api_key: cfg.rogueSecurityEnabled ? cfg.rogueSecurityApiKey : undefined,
        rogue_security_base_url: cfg.rogueSecurityEnabled ? cfg.rogueSecurityBaseUrl : undefined,
        max_retries: 3,
        timeout_seconds: 600,
      });
      toast.success("Red-team scan started");
      navigate({ to: "/red-team/$jobId", params: { jobId: res.job_id } });
    } catch (e) {
      toast.error(`Failed: ${(e as Error).message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Configure red-team scan</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Pick a scan profile or hand-craft your own selection of vulnerabilities and attacks.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <FrameworksDialog />
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              rt.clear();
              toast.success("Selection cleared");
            }}
          >
            Clear
          </Button>
          <Button onClick={submit} disabled={start.isPending}>
            {start.isPending ? "Starting…" : "Run scan"}
          </Button>
        </div>
      </div>

      <TargetAgentForm
        value={agent}
        onChange={setAgent}
        description="How to reach the agent under scan."
      />

      <Card>
        <CardHeader>
          <CardTitle>Scan type</CardTitle>
          <CardDescription>
            Basic and Full apply curated presets. Custom unlocks the catalog below.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-2 md:grid-cols-3">
            {SCAN_TYPES.map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => onScanTypeChange(t.id)}
                className={cn(
                  "cursor-pointer rounded-lg border px-4 py-3 text-left transition-colors",
                  rt.scanType === t.id
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

      <Card>
        <CardHeader>
          <CardTitle>LLMs</CardTitle>
          <CardDescription>Judge scores attacks; Attacker generates the probes.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
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
          <ModelPickerButton
            label="Attacker"
            value={{
              provider: cfg.attackerProvider,
              model: cfg.attackerModel,
              apiKey: cfg.apiKeys[cfg.attackerProvider],
              apiBase: cfg.attackerApiBase,
            }}
            onChange={(v) => {
              cfg.setAttackerProvider(v.provider);
              cfg.setAttackerModel(v.model);
              cfg.setAttackerApiBase(v.apiBase);
              if (v.apiKey) cfg.setApiKey(v.provider, v.apiKey);
            }}
          />
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <CatalogPane
          title="Vulnerabilities"
          categories={VULNERABILITY_CATALOG}
          selected={selectedVulns}
          expanded={expandedVulnCats}
          disabled={isLocked}
          onToggleItem={rt.toggleVuln}
          onToggleCategory={rt.toggleVulnCategory}
        />
        <CatalogPane
          title="Attacks"
          categories={ATTACK_CATALOG}
          selected={selectedAttacks}
          expanded={expandedAttackCats}
          disabled={isLocked}
          onToggleItem={rt.toggleAttack}
          onToggleCategory={rt.toggleAttackCategory}
        />
      </div>

      <StatusBar />
    </div>
  );
}

function StatusBar() {
  const rt = useRedTeamConfig();
  return (
    <div className="sticky bottom-0 -mx-4 flex flex-wrap items-center justify-between gap-4 border-t border-border bg-background/90 px-4 py-3 backdrop-blur">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs">
        <Stat label="Scan" value={rt.scanType} />
        <Stat label="Vulnerabilities" value={`${rt.vulnerabilities.length}/${totalVulns()}`} />
        <Stat label="Attacks" value={`${rt.attacks.length}/${totalAttacks()}`} />
        <Stat label="Frameworks" value={String(rt.frameworks.length)} />
      </div>
      <div className="flex items-center gap-2">
        <Label htmlFor="apv" className="text-xs">
          Attacks/Vuln
        </Label>
        <Input
          id="apv"
          type="number"
          min={1}
          max={20}
          value={rt.attacksPerVulnerability}
          onChange={(e) => rt.setAttacksPerVulnerability(Number(e.target.value))}
          className="h-8 w-20"
        />
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <span className="flex items-baseline gap-1.5 text-muted-foreground">
      <span className="text-[10px] font-semibold uppercase tracking-wider">{label}</span>
      <span className="font-mono text-foreground">{value}</span>
    </span>
  );
}
