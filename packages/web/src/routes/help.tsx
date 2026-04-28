import { createFileRoute } from "@tanstack/react-router";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const Route = createFileRoute("/help")({
  component: HelpPage,
});

function HelpPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Help</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Quick reference for the web console. The full TUI cheatsheet lives at{" "}
          <code className="rounded bg-muted px-1 py-0.5 text-xs">rogue-ai tui</code>.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Run modes</CardTitle>
          <CardDescription>How the CLI launches the platform.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <Cli cmd="uvx rogue-ai" desc="Start the TUI with a backing server" />
          <Cli cmd="uvx rogue-ai web" desc="Start the web UI (this app)" />
          <Cli cmd="uvx rogue-ai server" desc="Start the FastAPI server only" />
          <Cli cmd="uvx rogue-ai cli --config-file ..." desc="Non-interactive batch evaluation" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Web flags</CardTitle>
          <CardDescription>
            Available with the <code>web</code> subcommand.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <Cli cmd="--host 0.0.0.0" desc="Bind to all interfaces (default 127.0.0.1)" />
          <Cli cmd="--port 8080" desc="Bind to a custom port (default 8000)" />
          <Cli cmd="--no-browser" desc="Do not open a browser window automatically" />
          <Cli
            cmd="--server-url https://…"
            desc="Point the SPA at a remote API instead of starting one"
          />
        </CardContent>
      </Card>
    </div>
  );
}

function Cli({ cmd, desc }: { cmd: string; desc: string }) {
  return (
    <div className="grid grid-cols-[minmax(14rem,auto)_1fr] items-baseline gap-4">
      <code className="font-mono text-xs text-primary">{cmd}</code>
      <span className="text-muted-foreground">{desc}</span>
    </div>
  );
}
