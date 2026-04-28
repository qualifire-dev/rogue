import {
  IconActivity,
  IconHelp,
  IconHome,
  IconSettings,
  IconShieldHalf,
} from "@tabler/icons-react";
import { Link } from "@tanstack/react-router";
import type { ComponentProps } from "react";

import { NavMain, type NavMainItem } from "@/components/nav-main";
import { NavSecondary } from "@/components/nav-secondary";
import { NavUser } from "@/components/nav-user";
import { RogueLogo } from "@/components/rogue-logo";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

const NAV_MAIN: NavMainItem[] = [
  { title: "Dashboard", url: "/", icon: IconHome },
  {
    title: "Evaluations",
    url: "/evaluations",
    icon: IconActivity,
    items: [
      { title: "New evaluation", url: "/evaluations/new" },
      { title: "Scenarios", url: "/scenarios" },
    ],
  },
  {
    title: "Red Team",
    url: "/red-team",
    icon: IconShieldHalf,
    items: [{ title: "Configure", url: "/red-team/configure" }],
  },
];

const NAV_SECONDARY = [
  { title: "Settings", url: "/settings", icon: IconSettings },
  { title: "Help", url: "/help", icon: IconHelp },
];

export function AppSidebar(props: ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar variant="inset" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              asChild
              className="h-14 justify-center hover:bg-sidebar-accent/40 active:bg-sidebar-accent/40"
            >
              <Link to="/" aria-label="Rogue" className="flex items-center justify-center px-2">
                <span className="flex items-center justify-center">
                  <RogueLogo className="h-9 w-auto text-primary" />
                </span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <NavMain items={NAV_MAIN} label="Platform" />
        <NavSecondary items={NAV_SECONDARY} className="mt-auto" />
      </SidebarContent>

      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  );
}
