"use client";

import type { Phase, PhaseState } from "@/lib/types";
import { AgentCard } from "./AgentCard";

const PIPELINE_PHASES: Phase[] = ["scout", "security", "vision", "graph", "judge"];

interface AgentPipelineProps {
  phases: Record<Phase, PhaseState>;
  currentPhase: Phase | null;
}

export function AgentPipeline({ phases, currentPhase }: AgentPipelineProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold px-1">
        Agent Pipeline
      </h3>
      <div className="space-y-5">
        {PIPELINE_PHASES.map((phase) => (
          <AgentCard
            key={phase}
            phase={phase}
            state={phases[phase]}
            isActive={phase === currentPhase}
          />
        ))}
      </div>
    </div>
  );
}
