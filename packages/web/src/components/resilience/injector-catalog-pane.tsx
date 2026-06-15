import { CatalogPane } from "@/components/red-team/catalog-pane";
import type { Category } from "@/lib/red-team-catalog";
import { INJECTOR_CATALOG } from "@/lib/resilience-catalog";

const INJECTOR_CATEGORY: Category[] = [
  {
    title: "Fault injectors",
    items: INJECTOR_CATALOG.map((i) => ({ id: i.id, name: i.name, premium: false })),
  },
];

interface InjectorCatalogPaneProps {
  selected: Set<string>;
  expanded: Set<string>;
  disabled?: boolean;
  onToggleItem: (id: string) => void;
  onToggleCategory: (title: string) => void;
}

export function InjectorCatalogPane(props: InjectorCatalogPaneProps) {
  return (
    <CatalogPane
      title="Injectors"
      categories={INJECTOR_CATEGORY}
      selected={props.selected}
      expanded={props.expanded}
      disabled={props.disabled}
      onToggleItem={props.onToggleItem}
      onToggleCategory={props.onToggleCategory}
    />
  );
}
