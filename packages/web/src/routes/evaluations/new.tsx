import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { IconArrowRight, IconAlertTriangle } from "@tabler/icons-react";
import { useState } from "react";
import { toast } from "sonner";

import { BusinessContextCard } from "@/components/business-context-card";
import { ModelPickerButton } from "@/components/model-picker/dialog";
import { RogueSecuritySuggestion } from "@/components/rogue-security-suggestion";
import {
  DEFAULT_TARGET_AGENT_VALUE,
  TargetAgentForm,
  type TargetAgentValue,
} from "@/components/target-agent-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useStartEvaluation } from "@/api/queries";
import { authNeedsCredentials, protocolNeedsAgentUrl } from "@/lib/protocols";
import { useConfig } from "@/stores/config";
import { useScenariosStore } from "@/stores/scenarios";
import { AUTH_TYPE_LABELS } from "@/api/types";

export const Route = createFileRoute("/evaluations/new")({
  component: NewEvaluationPage,
});

function NewEvaluationPage() {
  const navigate = useNavigate();
  const cfg = useConfig();
  const start = useStartEvaluation();
  const scenarios = useScenariosStore((s) => s.scenarios);

  const [agent, setAgent] = useState<TargetAgentValue>(DEFAULT_TARGET_AGENT_VALUE);

  const isPython = agent.protocol === "python";
  const needsAgentUrl = protocolNeedsAgentUrl(agent.protocol);

  const submit = async () => {
    if (scenarios.length === 0) {
      toast.error("Add at least one scenario before running an evaluation.");
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
        agent_config: {
          // AgentConfig's fields are unprefixed for protocol/transport (the
          // `evaluated_agent_` prefix only exists on the red-team schema).
          protocol: agent.protocol,
          transport: agent.transport || undefined,
          evaluated_agent_url: needsAgentUrl ? agent.agentUrl : undefined,
          python_entrypoint_file: isPython ? agent.pythonFile.trim() : undefined,
          evaluated_agent_auth_type: agent.authType,
          evaluated_agent_credentials: authNeedsCredentials(agent.authType)
            ? agent.credentials.trim()
            : undefined,
          judge_llm: cfg.judgeModel,
          judge_llm_api_key: cfg.apiKeys[cfg.judgeProvider],
          judge_llm_api_base: cfg.judgeApiBase,
          business_context: cfg.businessContext.trim() || undefined,
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

      <RogueSecuritySuggestion />

      <TargetAgentForm
        value={agent}
        onChange={setAgent}
        description="How to reach the agent under evaluation."
      />

      <BusinessContextCard showInterviewLink />

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
