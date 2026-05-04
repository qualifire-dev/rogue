import { Outlet, createFileRoute } from "@tanstack/react-router";

// Layout shell for /evaluations/$jobId. The detail (index) and report pages
// live in `$jobId.index.tsx` and `$jobId.report.tsx` and render through the
// <Outlet /> below. Without this layout, TanStack Router's file-based child
// routing would render the detail page even on /report.
export const Route = createFileRoute("/evaluations/$jobId")({
  component: JobLayout,
});

function JobLayout() {
  return <Outlet />;
}
