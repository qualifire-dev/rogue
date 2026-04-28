import { IconChevronRight } from "@tabler/icons-react";
import { Link, useRouterState } from "@tanstack/react-router";

import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

function pathToCrumbs(pathname: string): { label: string; to: string }[] {
  const parts = pathname.split("/").filter(Boolean);
  const crumbs: { label: string; to: string }[] = [{ label: "Rogue", to: "/" }];
  let acc = "";
  for (const part of parts) {
    acc += `/${part}`;
    crumbs.push({
      label: part
        .replace(/[-_]/g, " ")
        .replace(/\$/, "")
        .replace(/\b\w/g, (c) => c.toUpperCase()),
      to: acc,
    });
  }
  return crumbs;
}

export function SiteHeader() {
  const { location } = useRouterState();
  const crumbs = pathToCrumbs(location.pathname);

  return (
    <header className="flex h-16 shrink-0 items-center gap-2">
      <div className="flex items-center gap-2 px-4">
        <SidebarTrigger className="-ml-1" />
        <Separator orientation="vertical" className="mr-2 data-[orientation=vertical]:h-4" />
        <nav className="flex min-w-0 items-center gap-1.5 text-sm">
          {crumbs.map((c, i) => (
            <span key={c.to} className="flex items-center gap-1.5">
              {i > 0 && <IconChevronRight className="h-3.5 w-3.5 text-muted-foreground" />}
              <Link
                to={c.to}
                className={cn(
                  "truncate transition-colors",
                  i === crumbs.length - 1
                    ? "font-medium text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {c.label}
              </Link>
            </span>
          ))}
        </nav>
      </div>
    </header>
  );
}
