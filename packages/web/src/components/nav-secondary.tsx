import { type Icon } from "@tabler/icons-react";
import { Link, useRouterState } from "@tanstack/react-router";
import type { ComponentProps, ComponentType } from "react";

import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

interface NavSecondaryItem {
  title: string;
  url: string;
  icon: Icon | ComponentType<{ className?: string }>;
}

export function NavSecondary({
  items,
  ...props
}: { items: NavSecondaryItem[] } & ComponentProps<typeof SidebarGroup>) {
  const { location } = useRouterState();
  const pathname = location.pathname;

  return (
    <SidebarGroup {...props}>
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton
                asChild
                size="sm"
                tooltip={item.title}
                isActive={
                  pathname === item.url || (item.url !== "/" && pathname.startsWith(item.url + "/"))
                }
              >
                <Link to={item.url}>
                  <item.icon />
                  <span>{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
