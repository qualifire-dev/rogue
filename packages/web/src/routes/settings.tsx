import { Outlet, createFileRoute } from "@tanstack/react-router";

import { SettingsNav } from "@/components/settings/settings-nav";

export const Route = createFileRoute("/settings")({
  component: SettingsLayout,
});

function SettingsLayout() {
  return (
    <div className="flex flex-1 flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage your local Rogue configuration.</p>
      </div>
      <div className="flex flex-1 gap-8">
        <aside className="w-[220px] shrink-0">
          <SettingsNav />
        </aside>
        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
