"use client";

import { CommandInput } from "@/components/landing/CommandInput";
import { AgentStatus } from "@/components/landing/AgentStatus";
import { CapabilitiesGrid } from "@/components/landing/CapabilitiesGrid";
import { RecentAudits } from "@/components/landing/RecentAudits";
import { ParticleField } from "@/components/ambient/ParticleField";

export default function Home() {
  return (
    <div className="relative min-h-screen bg-[var(--v-deep)]">
      {/* Subtle ambient background — reduced particle count */}
      <ParticleField color="cyan" particleCount={20} />

      <main className="relative z-10 pt-20 pb-16 px-4 lg:px-8 max-w-6xl mx-auto">
        {/* Input Hero */}
        <CommandInput />

        {/* Agent Status + Capabilities */}
        <div className="mt-10 grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <CapabilitiesGrid />
          </div>
          <div>
            <AgentStatus />
          </div>
        </div>

        {/* Recent Audits */}
        <div className="mt-8">
          <RecentAudits />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[rgba(255,255,255,0.04)] py-8 text-center">
        <p className="text-[10px] font-mono text-[var(--v-text-tertiary)]">
          VERITAS · AUTONOMOUS FORENSIC WEB AUDITOR · Trust, Verified
        </p>
      </footer>
    </div>
  );
}
