import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/resilience/new")({
  beforeLoad: () => {
    throw redirect({ to: "/resilience/configure" });
  },
});
