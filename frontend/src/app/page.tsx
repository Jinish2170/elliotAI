"use client";

import { CommandInput } from "@/components/landing/CommandInput";
import { AgentStatus } from "@/components/landing/AgentStatus";
import { RecentAudits } from "@/components/landing/RecentAudits";
import { ParticleField } from "@/components/ambient/ParticleField";

export default function Home() {
  return (
    <div className="relative min-h-screen bg-[var(--t-base)] flex flex-col justify-center items-center">
      <ParticleField color="cyan" particleCount={15} />

      <main className="relative z-10 w-full max-w-4xl px-4 flex flex-col gap-8">
        <CommandInput />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="border border-[var(--t-border)] p-4 bg-[#0a0a0a]">
            <AgentStatus />
          </div>
          <div className="border border-[var(--t-border)] p-4 bg-[#0a0a0a] min-h-[250px]">
            <RecentAudits />
          </div>
        </div>
      </main>

      <footer className="absolute bottom-4 text-center w-full">
        <p className="text-[10px] font-mono text-[var(--t-dim)] uppercase tracking-widest">
          VERITAS /// AUTONOMOUS FORENSIC WEB AUDITOR
        </p>
      </footer>
    </div>
  );
}
