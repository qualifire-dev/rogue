import { useEffect, useMemo, useState } from "react";
import { IconFolderOpen } from "@tabler/icons-react";
import { toast } from "sonner";

import { api } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  authNeedsCredentials,
  getTransportsForProtocol,
  protocolNeedsAgentUrl,
} from "@/lib/protocols";
import {
  AUTH_TYPE_LABELS,
  PROTOCOL_LABELS,
  TRANSPORT_LABELS,
  type AuthType,
  type Protocol,
  type Transport,
} from "@/api/types";

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

/**
 * Shape held by the form. Both `evaluations/new` and `red-team/configure`
 * lift this state to their own scope so they can serialise it into the
 * exact request payload each endpoint expects (the field names differ).
 */
export interface TargetAgentValue {
  protocol: Protocol;
  transport: Transport | "";
  agentUrl: string;
  pythonFile: string;
  authType: AuthType;
  credentials: string;
}

export const DEFAULT_TARGET_AGENT_VALUE: TargetAgentValue = {
  protocol: "a2a",
  transport: "http",
  agentUrl: "http://localhost:10001",
  pythonFile: "",
  authType: "no_auth",
  credentials: "",
};

interface Props {
  value: TargetAgentValue;
  onChange: (next: TargetAgentValue) => void;
  /** Optional override: hide the wrapping <Card> (caller composes its own). */
  bare?: boolean;
  description?: string;
}

/**
 * Shared "Target agent" config block used by the new-evaluation and
 * red-team-configure flows. Owns no submit logic — the parent reads
 * `value` and assembles its own request body.
 */
export function TargetAgentForm({ value, onChange, bare = false, description }: Props) {
  const [pickingPython, setPickingPython] = useState(false);

  const transports = useMemo(() => getTransportsForProtocol(value.protocol), [value.protocol]);
  const needsAgentUrl = protocolNeedsAgentUrl(value.protocol);
  const isPython = value.protocol === "python";

  // Keep transport in sync when protocol changes — otherwise a Python eval
  // can submit with a stale `http` transport that the server rejects.
  useEffect(() => {
    if (transports.length === 0) {
      if (value.transport !== "") onChange({ ...value, transport: "" });
      return;
    }
    const first = transports[0];
    if (first && !transports.includes(value.transport as Transport)) {
      onChange({ ...value, transport: first });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value.protocol]);

  const onProtocolChange = (next: Protocol) => {
    const nextTransports = getTransportsForProtocol(next);
    const nextTransport: Transport | "" = nextTransports[0] ?? "";
    onChange({
      ...value,
      protocol: next,
      transport: nextTransport,
      // Python doesn't support auth headers — reset.
      authType: next === "python" ? "no_auth" : value.authType,
    });
  };

  const pickPythonEntrypoint = async () => {
    setPickingPython(true);
    try {
      // The local server opens a native OS file dialog and returns the
      // absolute path. Browsers themselves never expose the real path
      // from <input type="file">, so we go through the local server.
      const res = await api<{ path: string | null }>("/api/v1/fs/pick-file", {
        body: { extensions: ["py"], prompt: "Select Python entrypoint" },
      });
      if (res.path) onChange({ ...value, pythonFile: res.path });
    } catch (e) {
      toast.error(`Couldn't open file dialog: ${(e as Error).message}`);
    } finally {
      setPickingPython(false);
    }
  };

  const inner = (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label>Protocol</Label>
          <Select value={value.protocol} onValueChange={(v) => onProtocolChange(v as Protocol)}>
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
            <Select
              value={value.transport}
              onValueChange={(v) => onChange({ ...value, transport: v as Transport })}
            >
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
            value={value.agentUrl}
            onChange={(e) => onChange({ ...value, agentUrl: e.target.value })}
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
              value={value.pythonFile}
              onChange={(e) => onChange({ ...value, pythonFile: e.target.value })}
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
            <Select
              value={value.authType}
              onValueChange={(v) => onChange({ ...value, authType: v as AuthType })}
            >
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
          {authNeedsCredentials(value.authType) && (
            <div className="space-y-1.5">
              <Label htmlFor="creds">
                {value.authType === "basic" ? "user:password" : AUTH_TYPE_LABELS[value.authType]}
              </Label>
              <Input
                id="creds"
                type="password"
                value={value.credentials}
                onChange={(e) => onChange({ ...value, credentials: e.target.value })}
                placeholder={credentialsPlaceholder(value.authType)}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );

  if (bare) return inner;
  return (
    <Card>
      <CardHeader>
        <CardTitle>Target agent</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{inner}</CardContent>
    </Card>
  );
}
