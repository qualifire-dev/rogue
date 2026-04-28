import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { ModelPickerButton } from "@/components/model-picker/dialog";
import { CatalogPane } from "@/components/red-team/catalog-pane";
import { FrameworksDialog } from "@/components/red-team/frameworks-dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import {
  authNeedsCredentials,
  getTransportsForProtocol,
  protocolNeedsAgentUrl,
} from "@/lib/protocols";
import { useConfig } from "@/stores/config";
import { useRedTeamConfig } from "@/stores/red-team";
import { cn } from "@/lib/utils";
import {
  AUTH_TYPE_LABELS,
  PROTOCOL_LABELS,
  TRANSPORT_LABELS,
  type AuthType,
  type Protocol,
  type ScanType,
  type Transport,
} from "@/api/types";

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

const PROTOCOLS: Protocol[] = ["a2a", "mcp", "python", "openai_api"];
const AUTH_TYPES: AuthType[] = ["no_auth", "api_key", "bearer_token", "basic"];

function credentialsPlaceholder(auth: AuthType): string {
  switch (auth) {
    case "api_key":
      return "API key sent as X-API-Key";
    case "bearer_token":
      return "Bearer token";
    case "basic":
      return "user:password (or pre-encoded base64)";
    default:
      return "";
  }
}

function RedTeamConfigurePage() {
  const cfg = useConfig();
  const navigate = useNavigate();
  const start = useStartRedTeam();
  const rt = useRedTeamConfig();

  const [protocol, setProtocol] = useState<Protocol>("a2a");
  const [transport, setTransport] = useState<Transport | "">("http");
  const [agentUrl, setAgentUrl] = useState("http://localhost:10001");
  const [pythonFile, setPythonFile] = useState("");
  const [authType, setAuthType] = useState<AuthType>("no_auth");
  const [credentials, setCredentials] = useState("");

  const transports = useMemo(() => getTransportsForProtocol(protocol), [protocol]);
  const needsAgentUrl = protocolNeedsAgentUrl(protocol);
  const isPython = protocol === "python";

  const onProtocolChange = (next: Protocol) => {
    setProtocol(next);
    const opts = getTransportsForProtocol(next);
    setTransport(opts[0] ?? "");
    if (next === "python") setAuthType("no_auth");
  };

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
    if (isPython && !pythonFile.trim()) {
      toast.error("A Python entrypoint file is required for the python protocol.");
      return;
    }
    if (authNeedsCredentials(authType) && !credentials.trim()) {
      toast.error(`${AUTH_TYPE_LABELS[authType]} requires credentials.`);
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
        evaluated_agent_url: needsAgentUrl ? agentUrl : undefined,
        evaluated_agent_protocol: protocol,
        evaluated_agent_transport: transport || undefined,
        evaluated_agent_auth_type: authType,
        evaluated_agent_auth_credentials: authNeedsCredentials(authType)
          ? credentials.trim()
          : undefined,
        python_entrypoint_file: isPython ? pythonFile.trim() : undefined,
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
          <CardTitle>Target agent</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Protocol</Label>
              <Select value={protocol} onValueChange={(v) => onProtocolChange(v as Protocol)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PROTOCOLS.map((p) => (
                    <SelectItem key={p} value={p}>
                      {PROTOCOL_LABELS[p]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {transports.length > 0 && (
              <div className="space-y-1.5">
                <Label>Transport</Label>
                <Select value={transport} onValueChange={(v) => setTransport(v as Transport)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {transports.map((t) => (
                      <SelectItem key={t} value={t}>
                        {TRANSPORT_LABELS[t]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          {isPython ? (
            <div className="space-y-1.5">
              <Label>Python entrypoint file</Label>
              <Input
                value={pythonFile}
                onChange={(e) => setPythonFile(e.target.value)}
                placeholder="/path/to/agent.py"
                className="font-mono text-xs"
              />
            </div>
          ) : (
            <div className="space-y-1.5">
              <Label>Agent URL</Label>
              <Input value={agentUrl} onChange={(e) => setAgentUrl(e.target.value)} />
            </div>
          )}
          {!isPython && (
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Auth type</Label>
                <Select value={authType} onValueChange={(v) => setAuthType(v as AuthType)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {AUTH_TYPES.map((a) => (
                      <SelectItem key={a} value={a}>
                        {AUTH_TYPE_LABELS[a]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {authNeedsCredentials(authType) && (
                <div className="space-y-1.5">
                  <Label>
                    {authType === "basic" ? "user:password" : AUTH_TYPE_LABELS[authType]}
                  </Label>
                  <Input
                    type="password"
                    value={credentials}
                    onChange={(e) => setCredentials(e.target.value)}
                    placeholder={credentialsPlaceholder(authType)}
                  />
                </div>
              )}
            </div>
          )}
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
