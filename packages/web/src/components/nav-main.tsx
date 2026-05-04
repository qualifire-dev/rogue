import { IconChevronRight, type Icon } from "@tabler/icons-react";
import { Link, useRouterState } from "@tanstack/react-router";
import type { ComponentType } from "react";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";

export interface NavMainItem {
  title: string;
  /**
   * Optional URL for the top-level row. When `items` is provided this is
   * ignored — the row becomes a pure toggle and the destination URLs live
   * on the sub-items.
   */
  url?: string;
  icon: Icon | ComponentType<{ className?: string }>;
  items?: { title: string; url: string }[];
}

function isPathActive(pathname: string, url: string): boolean {
  if (pathname === url) return true;
  if (url === "/") return false;
  return pathname.startsWith(url + "/");
}

/**
 * For nested sections, more than one sub-item URL may be a prefix of the
 * current pathname (e.g. `/evaluations` AND `/evaluations/new` both match
 * `/evaluations/new`). Pick the longest match so only the most-specific
 * sub-item lights up.
 */
function pickMostSpecific(pathname: string, urls: string[]): string | null {
  const matches = urls.filter((u) => isPathActive(pathname, u));
  if (matches.length === 0) return null;
  return matches.reduce((a, b) => (b.length > a.length ? b : a));
}

export function NavMain({ items, label }: { items: NavMainItem[]; label?: string }) {
  const { location } = useRouterState();
  const pathname = location.pathname;

  return (
    <SidebarGroup>
      {label && <SidebarGroupLabel>{label}</SidebarGroupLabel>}
      <SidebarMenu>
        {items.map((item) => {
          // Leaf row: simple link. `url` is required here.
          if (!item.items?.length) {
            const url = item.url ?? "/";
            return (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton asChild tooltip={item.title} isActive={pathname === url}>
                  <Link to={url}>
                    <item.icon />
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          }

          // Section row: pure toggle. Clicks expand/collapse the sub-menu;
          // navigation lives on the sub-items.
          const subUrls = item.items.map((s) => s.url);
          const activeSubUrl = pickMostSpecific(pathname, subUrls);
          const sectionActive = activeSubUrl !== null;

          return (
            <Collapsible
              key={item.title}
              asChild
              defaultOpen={sectionActive}
              className="group/collapsible"
            >
              <SidebarMenuItem>
                <CollapsibleTrigger asChild>
                  {/*
                   * Section header is a pure toggle — never visually "active",
                   * even when a sub-item is selected. The active treatment lives
                   * on the sub-item itself (see below).
                   */}
                  <SidebarMenuButton tooltip={item.title}>
                    <item.icon />
                    <span>{item.title}</span>
                    <IconChevronRight className="ml-auto transition-transform duration-150 group-data-[state=open]/collapsible:rotate-90" />
                  </SidebarMenuButton>
                </CollapsibleTrigger>
                <CollapsibleContent>
                  <SidebarMenuSub>
                    {item.items.map((subItem) => (
                      <SidebarMenuSubItem key={subItem.title}>
                        <SidebarMenuSubButton asChild isActive={subItem.url === activeSubUrl}>
                          <Link to={subItem.url}>
                            <span>{subItem.title}</span>
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    ))}
                  </SidebarMenuSub>
                </CollapsibleContent>
              </SidebarMenuItem>
            </Collapsible>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}
