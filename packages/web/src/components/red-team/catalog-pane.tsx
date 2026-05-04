import { IconChevronRight, IconStar } from "@tabler/icons-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Category } from "@/lib/red-team-catalog";
import { cn } from "@/lib/utils";

interface CatalogPaneProps {
  title: string;
  categories: Category[];
  selected: Set<string>;
  expanded: Set<string>;
  disabled?: boolean;
  onToggleItem: (id: string) => void;
  onToggleCategory: (title: string) => void;
}

export function CatalogPane({
  title,
  categories,
  selected,
  expanded,
  disabled,
  onToggleItem,
  onToggleCategory,
}: CatalogPaneProps) {
  const totalSelected = Array.from(selected).length;
  const total = categories.reduce((s, c) => s + c.items.length, 0);

  return (
    <Card className={cn("flex flex-col overflow-hidden", disabled && "opacity-60")}>
      <CardHeader className="flex flex-row items-center justify-between border-b border-border/60 py-3">
        <CardTitle className="text-sm">
          {title}{" "}
          <span className="ml-1 font-mono text-xs text-muted-foreground">
            ({totalSelected}/{total})
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[34rem]">
          <ul className="divide-y divide-border/40">
            {categories.map((cat) => {
              const inCat = cat.items.filter((i) => selected.has(i.id)).length;
              const open = expanded.has(cat.title);
              return (
                <li key={cat.title}>
                  <button
                    type="button"
                    disabled={disabled}
                    onClick={() => onToggleCategory(cat.title)}
                    className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm font-medium hover:bg-accent/40 disabled:cursor-not-allowed"
                  >
                    <IconChevronRight
                      className={cn(
                        "h-3.5 w-3.5 text-muted-foreground transition-transform",
                        open && "rotate-90",
                      )}
                    />
                    <span className="flex-1 text-primary">{cat.title}</span>
                    <span className="font-mono text-xs text-muted-foreground">
                      ({inCat}/{cat.items.length})
                    </span>
                  </button>
                  {open && (
                    <ul className="bg-background/30 px-3 pb-2">
                      {cat.items.map((item) => {
                        const checked = selected.has(item.id);
                        return (
                          <li key={item.id}>
                            <label
                              className={cn(
                                "flex cursor-pointer items-center gap-2 rounded px-3 py-1 font-mono text-xs transition-colors hover:bg-accent/30",
                                checked && "text-foreground",
                                !checked && "text-muted-foreground",
                                disabled && "cursor-not-allowed",
                              )}
                            >
                              <span
                                className={cn(
                                  "flex h-4 w-4 shrink-0 items-center justify-center rounded border border-border",
                                  checked && "border-primary bg-primary",
                                )}
                              >
                                {checked && (
                                  <span className="text-[10px] text-primary-foreground">✓</span>
                                )}
                              </span>
                              <input
                                type="checkbox"
                                className="sr-only"
                                checked={checked}
                                disabled={disabled}
                                onChange={() => onToggleItem(item.id)}
                              />
                              <span className="flex-1">{item.name}</span>
                              {item.premium && (
                                <IconStar className="h-3 w-3 text-[var(--chart-3)]" />
                              )}
                            </label>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </li>
              );
            })}
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
