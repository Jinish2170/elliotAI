"use client";

/* ========================================
   CapabilitiesGrid — System Capabilities
   Compact grid showing what Veritas detects.
   Internal-tool feel, no marketing copy.
   ======================================== */

import { PanelChrome } from "@/components/layout/PanelChrome";
import {
  ScanEye,
  ShieldCheck,
  Network,
  Scale,
  Radar,
  FileWarning,
  Lock,
  Globe,
  Bug,
  Fingerprint,
  Camera,
  Brain,
} from "lucide-react";

const CAPABILITIES = [
  { icon: ScanEye, label: "Visual Analysis", desc: "Screenshot-based dark pattern detection" },
  { icon: ShieldCheck, label: "Security Headers", desc: "HTTP header policy verification" },
  { icon: Network, label: "Graph Investigation", desc: "Entity relationship mapping" },
  { icon: Scale, label: "Trust Scoring", desc: "Multi-signal consensus verdict" },
  { icon: Radar, label: "Scout Navigation", desc: "Multi-page crawl & DOM analysis" },
  { icon: FileWarning, label: "Dark Patterns", desc: "Deceptive UI pattern recognition" },
  { icon: Lock, label: "SSL/TLS Analysis", desc: "Certificate chain validation" },
  { icon: Globe, label: "OSINT Recon", desc: "WHOIS, DNS, reputation lookup" },
  { icon: Bug, label: "Phishing Detection", desc: "Database & heuristic checks" },
  { icon: Fingerprint, label: "Form Validation", desc: "Input field security analysis" },
  { icon: Camera, label: "Evidence Capture", desc: "Annotated screenshot collection" },
  { icon: Brain, label: "AI Consensus", desc: "Multi-agent verdict reconciliation" },
] as const;

export function CapabilitiesGrid() {
  return (
    <PanelChrome title="System Capabilities" count={CAPABILITIES.length} elevation={2}>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-1">
        {CAPABILITIES.map((cap) => {
          const Icon = cap.icon;
          return (
            <div
              key={cap.label}
              className="flex items-start gap-2.5 px-3 py-2.5 rounded hover:bg-[rgba(255,255,255,0.02)] transition-colors"
            >
              <Icon className="w-4 h-4 text-[var(--v-text-tertiary)] mt-0.5 shrink-0" />
              <div className="min-w-0">
                <span className="block text-[12px] font-semibold text-[var(--v-text)]">
                  {cap.label}
                </span>
                <span className="block text-[10px] text-[var(--v-text-tertiary)] leading-tight">
                  {cap.desc}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </PanelChrome>
  );
}
