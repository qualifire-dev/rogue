import { Outlet, createFileRoute } from "@tanstack/react-router";

// Layout shell for /red-team/$jobId. Detail (index) and report pages render
// through the <Outlet /> below — see the matching evaluations layout for why.
export const Route = createFileRoute("/red-team/$jobId")({
  component: JobLayout,
});

function JobLayout() {
  return <Outlet />;
}
