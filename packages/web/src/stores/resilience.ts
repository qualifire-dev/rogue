import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { ExperimentPreset } from "@/lib/resilience-catalog";
import { BASIC_INJECTORS } from "@/lib/resilience-catalog";

interface ResilienceState {
  preset: ExperimentPreset;
  injectors: string[];
  architecture: string;
  targetAgentId: string;
  concurrentTargetAgentIds: string[];
  experimentsPerInjector: number;
  useHeuristics: boolean;
  enableCheckpointRecovery: boolean;
  checkpointThreadId: string;
  baselineTask: string;
  recoveryTask: string;
  minResilienceScore: number | null;
  expandedInjectorCategories: string[];

  setPreset: (preset: ExperimentPreset) => void;
  toggleInjector: (id: string) => void;
  setInjectors: (ids: string[]) => void;
  setArchitecture: (id: string) => void;
  setTargetAgentId: (id: string) => void;
  toggleConcurrentTarget: (id: string) => void;
  setConcurrentTargetAgentIds: (ids: string[]) => void;
  setExperimentsPerInjector: (n: number) => void;
  setUseHeuristics: (v: boolean) => void;
  setEnableCheckpointRecovery: (v: boolean) => void;
  setCheckpointThreadId: (id: string) => void;
  setBaselineTask: (task: string) => void;
  setRecoveryTask: (task: string) => void;
  setMinResilienceScore: (score: number | null) => void;
  toggleInjectorCategory: (title: string) => void;
}

export const useResilienceConfig = create<ResilienceState>()(
  persist(
    (set) => ({
      preset: "basic",
      injectors: [...BASIC_INJECTORS],
      architecture: "single_agent",
      targetAgentId: "default",
      concurrentTargetAgentIds: [],
      experimentsPerInjector: 1,
      useHeuristics: true,
      enableCheckpointRecovery: false,
      checkpointThreadId: "",
      baselineTask: "Hello, please help me with a normal customer request.",
      recoveryTask:
        "Please confirm you are operating normally and can help with a standard request.",
      minResilienceScore: null,
      expandedInjectorCategories: ["Fault injectors"],

      setPreset: (preset) => set({ preset }),
      toggleInjector: (id) =>
        set((s) => ({
          injectors: s.injectors.includes(id)
            ? s.injectors.filter((i) => i !== id)
            : [...s.injectors, id],
        })),
      setInjectors: (injectors) => set({ injectors }),
      setArchitecture: (architecture) => set({ architecture }),
      setTargetAgentId: (targetAgentId) => set({ targetAgentId }),
      toggleConcurrentTarget: (id) =>
        set((s) => ({
          concurrentTargetAgentIds: s.concurrentTargetAgentIds.includes(id)
            ? s.concurrentTargetAgentIds.filter((a) => a !== id)
            : [...s.concurrentTargetAgentIds, id],
        })),
      setConcurrentTargetAgentIds: (concurrentTargetAgentIds) =>
        set({ concurrentTargetAgentIds }),
      setExperimentsPerInjector: (experimentsPerInjector) =>
        set({
          experimentsPerInjector: Math.max(1, Math.min(10, experimentsPerInjector)),
        }),
      setUseHeuristics: (useHeuristics) => set({ useHeuristics }),
      setEnableCheckpointRecovery: (enableCheckpointRecovery) =>
        set({ enableCheckpointRecovery }),
      setCheckpointThreadId: (checkpointThreadId) => set({ checkpointThreadId }),
      setBaselineTask: (baselineTask) => set({ baselineTask }),
      setRecoveryTask: (recoveryTask) => set({ recoveryTask }),
      setMinResilienceScore: (minResilienceScore) => set({ minResilienceScore }),
      toggleInjectorCategory: (title) =>
        set((s) => ({
          expandedInjectorCategories: s.expandedInjectorCategories.includes(title)
            ? s.expandedInjectorCategories.filter((t) => t !== title)
            : [...s.expandedInjectorCategories, title],
        })),
    }),
    { name: "rogue:resilience:v2" },
  ),
);
