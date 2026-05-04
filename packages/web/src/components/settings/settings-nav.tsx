import {
  IconArchive,
  IconKey,
  IconRobot,
  IconSettings2,
  IconShieldCheck,
} from "@tabler/icons-react";
import { Link, useRouterState } from "@tanstack/react-router";
import type { ComponentType } from "react";

import { cn } from "@/lib/utils";

interface NavItem {
  title: string;
  href: string;
  icon: ComponentType<{ className?: string }>;
}

const ITEMS: NavItem[] = [
  { title: "General", href: "/settings/general", icon: IconSettings2 },
  { title: "Models", href: "/settings/models", icon: IconRobot },
  { title: "API keys", href: "/settings/api-keys", icon: IconKey },
  { title: "Rogue Security", href: "/settings/rogue-security", icon: IconShieldCheck },
  { title: "Backup", href: "/settings/backup", icon: IconArchive },
];

export function SettingsNav() {
  const { location } = useRouterState();
  const pathname = location.pathname;

  return (
    <nav className="flex flex-col gap-1">
      {ITEMS.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            to={item.href}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              isActive
                ? "bg-accent text-accent-foreground"
                : "text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground",
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.title}
          </Link>
        );
      })}
    </nav>
  );
}
