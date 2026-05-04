import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Scenario } from "@/api/types";

interface ScenariosState {
  scenarios: Scenario[];
  setAll: (s: Scenario[]) => void;
  add: (s: Scenario) => void;
  remove: (i: number) => void;
  update: (i: number, s: Scenario) => void;
}

export const useScenariosStore = create<ScenariosState>()(
  persist(
    (set) => ({
      scenarios: [],
      setAll: (scenarios) => set({ scenarios }),
      add: (s) => set((state) => ({ scenarios: [...state.scenarios, s] })),
      remove: (i) =>
        set((state) => ({
          scenarios: state.scenarios.filter((_, idx) => idx !== i),
        })),
      update: (i, s) =>
        set((state) => ({
          scenarios: state.scenarios.map((cur, idx) => (idx === i ? s : cur)),
        })),
    }),
    { name: "rogue:scenarios:v1" },
  ),
);
