import { createFileRoute } from "@tanstack/react-router";

import { ModelPickerButton } from "@/components/model-picker/dialog";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useConfig } from "@/stores/config";

export const Route = createFileRoute("/settings/models")({
  component: ModelsSettingsPage,
});

function ModelsSettingsPage() {
  const cfg = useConfig();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Judge model</CardTitle>
          <CardDescription>
            Scores agent behavior in policy-mode evaluations and red-team scans.
          </CardDescription>
        </CardHeader>
        <CardContent>
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
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Attacker model</CardTitle>
          <CardDescription>Generates probes during red-team scans.</CardDescription>
        </CardHeader>
        <CardContent>
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

      <Card>
        <CardHeader>
          <CardTitle>Interview model</CardTitle>
          <CardDescription>
            Drives the interview chat that derives business context.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ModelPickerButton
            label="Interview"
            value={{
              provider: cfg.interviewProvider,
              model: cfg.interviewModel,
              apiKey: cfg.apiKeys[cfg.interviewProvider],
              apiBase: cfg.interviewApiBase,
            }}
            onChange={(v) => {
              cfg.setInterviewProvider(v.provider);
              cfg.setInterviewModel(v.model);
              cfg.setInterviewApiBase(v.apiBase);
              if (v.apiKey) cfg.setApiKey(v.provider, v.apiKey);
            }}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scenario generation model</CardTitle>
          <CardDescription>
            Used by the LLM service to propose new scenarios from business context.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ModelPickerButton
            label="Scenario generation"
            value={{
              provider: cfg.scenarioGenProvider,
              model: cfg.scenarioGenModel,
              apiKey: cfg.apiKeys[cfg.scenarioGenProvider],
              apiBase: cfg.scenarioGenApiBase,
            }}
            onChange={(v) => {
              cfg.setScenarioGenProvider(v.provider);
              cfg.setScenarioGenModel(v.model);
              cfg.setScenarioGenApiBase(v.apiBase);
              if (v.apiKey) cfg.setApiKey(v.provider, v.apiKey);
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
