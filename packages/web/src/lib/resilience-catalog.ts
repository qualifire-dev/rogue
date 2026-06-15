/**
 * Resilience catalog — injectors and architecture profiles.
 * Mirrors backend ``rogue/injectors/registry.py`` and
 * ``rogue/resilience/catalog/architectures.py``.
 */

export interface CatalogItem {
  id: string;
  name: string;
  description: string;
}

export interface ArchitectureCatalogItem extends CatalogItem {
  agentIds: string[];
  isMultiAgent: boolean;
}

export const INJECTOR_CATALOG: CatalogItem[] = [
  {
    id: "tool_misuse",
    name: "Tool misuse",
    description: "Unauthorized or malformed tool calls",
  },
  {
    id: "hallucination_spamming",
    name: "Hallucination spamming",
    description: "High-volume fabricated output",
  },
  {
    id: "goal_conflict",
    name: "Goal conflict",
    description: "Adversarial sub-goals injected at runtime",
  },
  {
    id: "policy_violation",
    name: "Policy violation",
    description: "Deliberate business-rule breaches",
  },
  {
    id: "action_spam",
    name: "Action spam",
    description: "Rapid-fire messages and actions",
  },
];

export const ARCHITECTURE_CATALOG: ArchitectureCatalogItem[] = [
  {
    id: "single_agent",
    name: "Single agent",
    description: "Phase 1 default — one agent under test",
    agentIds: ["default"],
    isMultiAgent: false,
  },
  {
    id: "hierarchical",
    name: "Hierarchical",
    description: "Supervisor + workers; tests cascade detection",
    agentIds: ["supervisor", "worker-1", "worker-2"],
    isMultiAgent: true,
  },
  {
    id: "peer_to_peer",
    name: "Peer to peer",
    description: "Fully connected peers; tests cascade spread",
    agentIds: ["peer-a", "peer-b", "peer-c"],
    isMultiAgent: true,
  },
  {
    id: "supervisor_worker",
    name: "Supervisor worker",
    description: "Sequential pipeline topology",
    agentIds: ["supervisor", "worker-1", "worker-2"],
    isMultiAgent: true,
  },
];

export const BASIC_INJECTORS = ["policy_violation", "tool_misuse"];
export const FULL_INJECTORS = INJECTOR_CATALOG.map((i) => i.id);

export type ExperimentPreset = "basic" | "full" | "custom";

export function getArchitecture(id: string): ArchitectureCatalogItem | undefined {
  return ARCHITECTURE_CATALOG.find((a) => a.id === id);
}

export function getInjector(id: string): CatalogItem | undefined {
  return INJECTOR_CATALOG.find((i) => i.id === id);
}
