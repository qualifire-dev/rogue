import { Component, type ErrorInfo, type ReactNode } from "react";
import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

import type { ResilienceReportMetricRadar } from "@/api/types";
import {
  ResilienceChartSkeleton,
  ResilienceEmptyPanel,
  ResilienceErrorPanel,
} from "@/components/resilience/panel-states";

interface MetricsRadarProps {
  metrics: ResilienceReportMetricRadar[];
  className?: string;
  loading?: boolean;
  error?: string | null;
}

interface RadarChartBodyProps {
  data: Array<{ metric: string; value: number; fullMark: number }>;
  className?: string;
}

/** Catches Recharts render failures and shows a friendly error panel. */
class RadarChartErrorBoundary extends Component<
  { children: ReactNode; className?: string },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("MetricsRadar render failed:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ResilienceErrorPanel
          title="Chart could not render"
          description="Metric values may be invalid. Try reloading the report."
        />
      );
    }
    return this.props.children;
  }
}

function RadarChartBody({ data, className }: RadarChartBodyProps) {
  return (
    <div className={className ?? "h-72 w-full"}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="70%">
          <PolarGrid stroke="var(--border)" />
          <PolarAngleAxis
            dataKey="metric"
            tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
          />
          <Radar
            name="Score"
            dataKey="value"
            stroke="var(--primary)"
            fill="var(--primary)"
            fillOpacity={0.35}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MetricsRadar({
  metrics,
  className,
  loading = false,
  error = null,
}: MetricsRadarProps) {
  if (loading) {
    return <ResilienceChartSkeleton className={className} />;
  }

  if (error) {
    return <ResilienceErrorPanel title="Metrics unavailable" description={error} />;
  }

  if (metrics.length === 0) {
    return (
      <ResilienceEmptyPanel
        title="No metrics available"
        description="Run at least one injector experiment to populate the radar chart."
      />
    );
  }

  const data = metrics.map((m) => ({
    metric: m.label,
    value: Number.isFinite(m.value) ? Math.round(m.value * 100) : 0,
    fullMark: 100,
  }));

  return (
    <RadarChartErrorBoundary
      key={data.map((d) => `${d.metric}:${d.value}`).join("|")}
      className={className}
    >
      <RadarChartBody data={data} className={className} />
    </RadarChartErrorBoundary>
  );
}
