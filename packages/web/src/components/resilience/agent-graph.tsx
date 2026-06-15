import type { ResilienceReportAgentGraph } from "@/api/types";
import {
  ResilienceEmptyPanel,
  ResilienceErrorPanel,
  ResilienceLoadingPanel,
} from "@/components/resilience/panel-states";
import { cn } from "@/lib/utils";

interface AgentGraphProps {
  graph: ResilienceReportAgentGraph;
  className?: string;
  loading?: boolean;
  error?: string | null;
}

/** Simple force-free layout: nodes in a row, edges as SVG lines. */
export function AgentGraph({
  graph,
  className,
  loading = false,
  error = null,
}: AgentGraphProps) {
  if (loading) {
    return (
      <ResilienceLoadingPanel
        title="Loading agent topology…"
        description="Building the graph from the architecture profile."
      />
    );
  }

  if (error) {
    return <ResilienceErrorPanel title="Topology unavailable" description={error} />;
  }

  const nodes = graph?.nodes ?? [];
  const edges = graph?.edges ?? [];

  if (nodes.length === 0) {
    return (
      <ResilienceEmptyPanel
        title="No agent topology"
        description="Single-agent runs show one node. Multi-agent architectures display supervisor/worker edges."
      />
    );
  }

  const positions = new Map<string, { x: number; y: number }>();
  const spacing = 100 / Math.max(nodes.length, 1);
  nodes.forEach((node, i) => {
    positions.set(node.agent_id, { x: spacing * (i + 0.5), y: 50 });
  });

  return (
    <div
      className={cn(
        "relative h-56 w-full rounded-xl border border-border/60 bg-muted/20 p-4",
        className,
      )}
    >
      <svg viewBox="0 0 100 100" className="h-full w-full" aria-label="Agent topology">
        <defs>
          <marker id="resilience-arrow" markerWidth="4" markerHeight="4" refX="2" refY="2" orient="auto">
            <path d="M0,0 L4,2 L0,4 Z" fill="var(--muted-foreground)" fillOpacity={0.6} />
          </marker>
        </defs>
        {edges.map((edge, i) => {
          const from = positions.get(edge.source);
          const to = positions.get(edge.target);
          if (!from || !to) return null;
          return (
            <line
              key={`${edge.source}-${edge.target}-${i}`}
              x1={from.x}
              y1={from.y}
              x2={to.x}
              y2={to.y}
              stroke="var(--muted-foreground)"
              strokeWidth={0.4}
              strokeOpacity={0.5}
              markerEnd="url(#resilience-arrow)"
            />
          );
        })}
        {nodes.map((node) => {
          const pos = positions.get(node.agent_id);
          if (!pos) return null;
          const isRogue = node.is_rogue || node.is_target;
          return (
            <g key={node.agent_id}>
              <circle
                cx={pos.x}
                cy={pos.y}
                r={6}
                className={cn(
                  isRogue ? "fill-destructive" : "fill-primary",
                  "stroke-background",
                )}
                strokeWidth={1}
              />
              <text
                x={pos.x}
                y={pos.y + 14}
                textAnchor="middle"
                fontSize={4}
                fill="var(--foreground)"
              >
                {node.agent_id}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="absolute bottom-2 left-3 flex gap-3 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full bg-primary" /> healthy
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full bg-destructive" /> fault target
        </span>
      </div>
    </div>
  );
}
