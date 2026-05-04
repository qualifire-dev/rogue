import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { ScanType } from "@/api/types";

interface RedTeamState {
  scanType: ScanType;
  vulnerabilities: string[];
  attacks: string[];
  frameworks: string[];
  attacksPerVulnerability: number;
  expandedVulnCategories: string[];
  expandedAttackCategories: string[];

  setScanType: (t: ScanType) => void;
  toggleVuln: (id: string) => void;
  toggleAttack: (id: string) => void;
  setVulns: (ids: string[]) => void;
  setAttacks: (ids: string[]) => void;
  toggleFramework: (id: string) => void;
  setAttacksPerVulnerability: (n: number) => void;
  toggleVulnCategory: (title: string) => void;
  toggleAttackCategory: (title: string) => void;
  clear: () => void;
}

const DEFAULT_EXPANDED_VULNS = ["Prompt Security", "PII Protection"];
const DEFAULT_EXPANDED_ATTACKS = ["Single-Turn"];

export const useRedTeamConfig = create<RedTeamState>()(
  persist(
    (set) => ({
      scanType: "custom",
      vulnerabilities: [],
      attacks: [],
      frameworks: [],
      attacksPerVulnerability: 3,
      expandedVulnCategories: DEFAULT_EXPANDED_VULNS,
      expandedAttackCategories: DEFAULT_EXPANDED_ATTACKS,

      setScanType: (scanType) => set({ scanType }),
      toggleVuln: (id) =>
        set((s) => ({
          vulnerabilities: s.vulnerabilities.includes(id)
            ? s.vulnerabilities.filter((v) => v !== id)
            : [...s.vulnerabilities, id],
        })),
      toggleAttack: (id) =>
        set((s) => ({
          attacks: s.attacks.includes(id) ? s.attacks.filter((a) => a !== id) : [...s.attacks, id],
        })),
      setVulns: (vulnerabilities) => set({ vulnerabilities }),
      setAttacks: (attacks) => set({ attacks }),
      toggleFramework: (id) =>
        set((s) => ({
          frameworks: s.frameworks.includes(id)
            ? s.frameworks.filter((f) => f !== id)
            : [...s.frameworks, id],
        })),
      setAttacksPerVulnerability: (attacksPerVulnerability) =>
        set({ attacksPerVulnerability: Math.max(1, Math.min(20, attacksPerVulnerability)) }),
      toggleVulnCategory: (title) =>
        set((s) => ({
          expandedVulnCategories: s.expandedVulnCategories.includes(title)
            ? s.expandedVulnCategories.filter((t) => t !== title)
            : [...s.expandedVulnCategories, title],
        })),
      toggleAttackCategory: (title) =>
        set((s) => ({
          expandedAttackCategories: s.expandedAttackCategories.includes(title)
            ? s.expandedAttackCategories.filter((t) => t !== title)
            : [...s.expandedAttackCategories, title],
        })),
      clear: () =>
        set({
          vulnerabilities: [],
          attacks: [],
          frameworks: [],
        }),
    }),
    { name: "rogue:red-team:v2" },
  ),
);
