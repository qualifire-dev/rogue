import { IconCheck } from "@tabler/icons-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FRAMEWORKS } from "@/lib/red-team-catalog";
import { cn } from "@/lib/utils";
import { useRedTeamConfig } from "@/stores/red-team";

export function FrameworksDialog() {
  const { frameworks, toggleFramework } = useRedTeamConfig();

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          Frameworks ({frameworks.length})
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Compliance frameworks</DialogTitle>
          <DialogDescription>
            Toggle frameworks to align this scan with their requirements.
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="h-80 rounded-md border border-border/60">
          <ul className="divide-y divide-border/40">
            {FRAMEWORKS.map((f) => {
              const on = frameworks.includes(f.id);
              return (
                <li key={f.id}>
                  <button
                    type="button"
                    onClick={() => toggleFramework(f.id)}
                    className={cn(
                      "flex w-full items-center justify-between gap-3 px-3 py-2.5 text-left transition-colors hover:bg-accent",
                      on && "bg-accent/60",
                    )}
                  >
                    <span>
                      <span className="font-medium">{f.name}</span>
                      <span className="ml-2 text-xs text-muted-foreground">{f.description}</span>
                    </span>
                    {on && <IconCheck className="h-4 w-4 text-primary" />}
                  </button>
                </li>
              );
            })}
          </ul>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}
