import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { IconArrowRight, IconAlertTriangle, IconFolderOpen } from "@tabler/icons-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { ModelPickerButton } from "@/components/model-picker/dialog";
import { api } from "@/api/client";
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
import { useStartEvaluation } from "@/api/queries";
import {
  authNeedsCredentials,
  getTransportsForProtocol,
  protocolNeedsAgentUrl,
} from "@/lib/protocols";
import { useConfig } from "@/stores/config";
import { useScenariosStore } from "@/stores/scenarios";
import {
  AUTH_TYPE_LABELS,
  PROTOCOL_LABELS,
  TRANSPORT_LABELS,
  type AuthType,
  type Protocol,
  type Transport,
} from "@/api/types";

export const Route = createFileRoute("/evaluations/new")({
  component: NewEvaluationPage,
});

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

function NewEvaluationPage() {
  const navigate = useNavigate();
  const cfg = useConfig();
  const start = useStartEvaluation();
  const scenarios = useScenariosStore((s) => s.scenarios);

  const [protocol, setProtocol] = useState<Protocol>("a2a");
  const [transport, setTransport] = useState<Transport | "">("http");
  const [agentUrl, setAgentUrl] = useState("http://localhost:10001");
  const [pythonFile, setPythonFile] = useState("");
  const [pickingPython, setPickingPython] = useState(false);
  const [authType, setAuthType] = useState<AuthType>("no_auth");
  const [credentials, setCredentials] = useState("");

  const pickPythonEntrypoint = async () => {
    setPickingPython(true);
    try {
      // The local server opens a native OS file dialog and returns the
      // absolute path. Browsers themselves never expose the real path from
      // <input type="file">, so we go through the local server instead.
      const res = await api<{ path: string | null }>("/api/v1/fs/pick-file", {
        body: {
          extensions: ["py"],
          prompt: "Select Python entrypoint",
        },
      });
      if (res.path) setPythonFile(res.path);
    } catch (e) {
      toast.error(`Couldn't open file dialog: ${(e as Error).message}`);
    } finally {
      setPickingPython(false);
    }
  };

  const transports = useMemo(() => getTransportsForProtocol(protocol), [protocol]);
  const needsAgentUrl = protocolNeedsAgentUrl(protocol);
  const isPython = protocol === "python";

  const onProtocolChange = (next: Protocol) => {
    setProtocol(next);
    const opts = getTransportsForProtocol(next);
    setTransport(opts[0] ?? "");
    if (next === "python") setAuthType("no_auth");
  };

  const submit = async () => {
    if (scenarios.length === 0) {
      toast.error("Add at least one scenario before running an evaluation.");
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
        agent_config: {
          // AgentConfig's fields are unprefixed for protocol/transport (the
          // `evaluated_agent_` prefix only exists on the red-team schema).
          protocol,
          transport: transport || undefined,
          evaluated_agent_url: needsAgentUrl ? agentUrl : undefined,
          python_entrypoint_file: isPython ? pythonFile.trim() : undefined,
          evaluated_agent_auth_type: authType,
          evaluated_agent_credentials: authNeedsCredentials(authType)
            ? credentials.trim()
            : undefined,
          judge_llm: cfg.judgeModel,
          judge_llm_api_key: cfg.apiKeys[cfg.judgeProvider],
          judge_llm_api_base: cfg.judgeApiBase,
        },
        scenarios,
        max_retries: 3,
        timeout_seconds: 600,
      });
      toast.success("Evaluation started");
      navigate({ to: "/evaluations/$jobId", params: { jobId: res.job_id } });
    } catch (e) {
      toast.error(`Failed to start: ${(e as Error).message}`);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New evaluation</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Configure the target agent. Scenarios are pulled from your library.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Target agent</CardTitle>
          <CardDescription>How to reach the agent under evaluation.</CardDescription>
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
          {needsAgentUrl && (
            <div className="space-y-1.5">
              <Label htmlFor="agent-url">Agent URL</Label>
              <Input
                id="agent-url"
                value={agentUrl}
                onChange={(e) => setAgentUrl(e.target.value)}
                placeholder="http://localhost:10001"
              />
            </div>
          )}
          {isPython && (
            <div className="space-y-1.5">
              <Label htmlFor="python-file">Python entrypoint file</Label>
              <div className="flex gap-2">
                <Input
                  id="python-file"
                  value={pythonFile}
                  onChange={(e) => setPythonFile(e.target.value)}
                  placeholder="/path/to/agent.py"
                  className="font-mono text-xs"
                />
                <Button
                  type="button"
                  variant="outline"
                  className="shrink-0"
                  onClick={pickPythonEntrypoint}
                  disabled={pickingPython}
                >
                  <IconFolderOpen className="mr-1.5 h-4 w-4" />
                  {pickingPython ? "Opening…" : "Browse…"}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Absolute path to a Python file that exports a{" "}
                <code className="rounded bg-muted px-1 py-0.5">call_agent</code> function.
              </p>
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
                  <Label htmlFor="creds">
                    {authType === "basic" ? "user:password" : AUTH_TYPE_LABELS[authType]}
                  </Label>
                  <Input
                    id="creds"
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
          <CardTitle>Judge</CardTitle>
          <CardDescription>The LLM that scores agent behavior.</CardDescription>
        </CardHeader>
        <CardContent>
          <ModelPickerButton
            label="Judge model"
            value={{
              provider: cfg.judgeProvider,
              model: cfg.judgeModel,
              apiKey: cfg.apiKeys[cfg.judgeProvider],
              apiBase: cfg.judgeApiBase,
            }}
            onChange={(v) => {
              cfg.setSelectedProvider(v.provider);
              cfg.setJudgeModel(v.model);
              cfg.setJudgeProvider(v.provider);
              if (v.apiKey) cfg.setApiKey(v.provider, v.apiKey);
              cfg.setJudgeApiBase(v.apiBase);
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scenarios</CardTitle>
          <CardDescription>Pulled from your scenario library at submit time.</CardDescription>
        </CardHeader>
        <CardContent>
          {scenarios.length === 0 ? (
            <div className="flex items-start gap-3 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
              <IconAlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <div className="flex-1">
                <div className="font-medium">No scenarios yet</div>
                <div className="mt-0.5 text-xs opacity-90">
                  Add at least one before running an evaluation.
                </div>
              </div>
              <Button asChild size="sm" variant="outline">
                <Link to="/scenarios">
                  Go to scenarios <IconArrowRight className="ml-1 h-3 w-3" />
                </Link>
              </Button>
            </div>
          ) : (
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="text-sm">
                  <span className="font-semibold">{scenarios.length}</span> scenario
                  {scenarios.length === 1 ? "" : "s"} loaded
                </div>
                <ul className="mt-2 space-y-1 text-xs text-muted-foreground">
                  {scenarios.slice(0, 3).map((s, i) => (
                    <li key={i} className="line-clamp-1">
                      · {s.scenario}
                    </li>
                  ))}
                  {scenarios.length > 3 && (
                    <li className="italic opacity-80">… and {scenarios.length - 3} more</li>
                  )}
                </ul>
              </div>
              <Button asChild size="sm" variant="outline">
                <Link to="/scenarios">
                  Manage <IconArrowRight className="ml-1 h-3 w-3" />
                </Link>
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={() => history.back()}>
          Cancel
        </Button>
        <Button onClick={submit} disabled={start.isPending || scenarios.length === 0}>
          {start.isPending ? "Starting…" : "Start evaluation"}
        </Button>
      </div>
    </div>
  );
}
