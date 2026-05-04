import { IconDotsVertical, IconMoon, IconSun } from "@tabler/icons-react";

import { useTheme } from "@/components/theme-provider";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

export function NavUser() {
  const { isMobile } = useSidebar();
  const { theme, toggle } = useTheme();

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            >
              <span className="flex h-8 w-8 items-center justify-center rounded-md bg-sidebar-accent text-sidebar-accent-foreground">
                <img src="/assets/wolf-favicon.svg" alt="Local user" className="h-4 w-4" />
              </span>
              <div className="grid flex-1 text-left text-sm leading-tight">
                <span className="truncate font-medium">Local agent</span>
                <span className="truncate text-xs text-muted-foreground">rogue · localhost</span>
              </div>
              <IconDotsVertical className="ml-auto size-4" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className="min-w-56 rounded-lg"
            side={isMobile ? "bottom" : "right"}
            align="end"
            sideOffset={4}
          >
            <DropdownMenuLabel className="text-xs text-muted-foreground">
              Appearance
            </DropdownMenuLabel>
            <DropdownMenuItem onClick={toggle}>
              {theme === "dark" ? (
                <>
                  <IconSun className="mr-2 h-4 w-4" />
                  Switch to light
                </>
              ) : (
                <>
                  <IconMoon className="mr-2 h-4 w-4" />
                  Switch to dark
                </>
              )}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
