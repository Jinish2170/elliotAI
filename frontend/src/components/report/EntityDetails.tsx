"use client";

import type { DomainInfo } from "@/lib/types";
import { motion } from "framer-motion";

interface EntityDetailsProps {
  domainInfo: DomainInfo;
  url: string;
}

export function EntityDetails({ domainInfo, url }: EntityDetailsProps) {
  const rows = [
    { label: "Domain", value: new URL(url).hostname, icon: "🌐" },
    { label: "Registrar", value: domainInfo.registrar || "Unknown", icon: "📋" },
    {
      label: "Domain Age",
      value: domainInfo.age_days
        ? `${domainInfo.age_days} days (${(domainInfo.age_days / 365).toFixed(1)} years)`
        : "Unknown",
      icon: "📅",
    },
    { label: "SSL Issuer", value: domainInfo.ssl_issuer || "Unknown", icon: "🔒" },
    { label: "IP Address", value: domainInfo.ip || "Unknown", icon: "📡" },
    { label: "Country", value: domainInfo.country || "Unknown", icon: "🏳️" },
    {
      label: "Entity Verified",
      value: domainInfo.entity_verified ? "Yes ✅" : "No ❌",
      icon: "✔️",
    },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.3 }}
      className="glass-card rounded-2xl p-8 mb-6"
    >
      <h2 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold mb-6">
        Entity Verification
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-3">
        {rows.map((row, i) => (
          <motion.div
            key={row.label}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 + i * 0.05 }}
            className="flex items-center justify-between py-2 border-b border-white/5"
          >
            <span className="text-xs text-[var(--v-text-tertiary)] flex items-center gap-2">
              <span>{row.icon}</span> {row.label}
            </span>
            <span className="text-sm text-[var(--v-text)] font-mono">{row.value}</span>
          </motion.div>
        ))}
      </div>

      {/* Inconsistencies */}
      {domainInfo.inconsistencies && domainInfo.inconsistencies.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xs font-semibold text-amber-400 mb-2">⚠️ Inconsistencies Detected</h3>
          <div className="space-y-1">
            {domainInfo.inconsistencies.map((inc, i) => (
              <div key={i} className="text-xs text-[var(--v-text-secondary)] flex items-start gap-2">
                <span className="text-amber-400 mt-0.5">•</span>
                <span>{inc}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </motion.section>
  );
}
