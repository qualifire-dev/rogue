import { Outlet, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/resilience/$jobId")({
  component: JobLayout,
});

function JobLayout() {
  return <Outlet />;
}
