import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/red-team/new")({
  beforeLoad: () => {
    throw redirect({ to: "/red-team/configure" });
  },
});
