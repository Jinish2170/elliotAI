"use client";

/* ========================================
   EntityIntel — Domain/Entity Intelligence
   WHOIS + DNS + SSL in TerminalBlock +
   DataTable format. Replaces card-based
   EntityDetails.
   ======================================== */

import { cn } from "@/lib/utils";
import { PanelChrome } from "@/components/layout/PanelChrome";
import { TerminalBlock } from "@/components/data-display/TerminalBlock";
import type { DomainInfo } from "@/lib/types";
import {
  Globe,
  ShieldCheck,
  ShieldX,
  AlertTriangle,
  Calendar,
  Building2,
  Lock,
  MapPin,
  Server,
} from "lucide-react";

interface EntityIntelProps {
  domainInfo: DomainInfo;
  url: string;
  className?: string;
}

export function EntityIntel({ domainInfo, url, className }: EntityIntelProps) {
  let hostname = "";
  try {
    hostname = new URL(url).hostname;
  } catch {
    hostname = url;
  }

  const ageYears = domainInfo.age_days
    ? (domainInfo.age_days / 365).toFixed(1)
    : null;

  // Build WHOIS-style terminal content
  const whoisLines = [
    `Domain Name: ${hostname}`,
    `Registrar: ${domainInfo.registrar || "N/A"}`,
    `Domain Age: ${domainInfo.age_days ? `${domainInfo.age_days} days (${ageYears} years)` : "N/A"}`,
    `SSL Issuer: ${domainInfo.ssl_issuer || "N/A"}`,
    `IP Address: ${domainInfo.ip || "N/A"}`,
    `Country: ${domainInfo.country || "N/A"}`,
    `Entity Verified: ${domainInfo.entity_verified ? "YES" : "NO"}`,
  ];

  // Key-value rows for grid
  const rows: { icon: React.ReactNode; label: string; value: string; status?: "pass" | "warn" | "fail" }[] = [
    {
      icon: <Globe className="w-3.5 h-3.5" />,
      label: "Domain",
      value: hostname,
    },
    {
      icon: <Building2 className="w-3.5 h-3.5" />,
      label: "Registrar",
      value: domainInfo.registrar || "Unknown",
    },
    {
      icon: <Calendar className="w-3.5 h-3.5" />,
      label: "Domain Age",
      value: domainInfo.age_days
        ? `${domainInfo.age_days}d (${ageYears}y)`
        : "Unknown",
      status: domainInfo.age_days
        ? domainInfo.age_days < 90
          ? "fail"
          : domainInfo.age_days < 365
          ? "warn"
          : "pass"
        : undefined,
    },
    {
      icon: <Lock className="w-3.5 h-3.5" />,
      label: "SSL Issuer",
      value: domainInfo.ssl_issuer || "Unknown",
      status: domainInfo.ssl_issuer ? "pass" : "fail",
    },
    {
      icon: <Server className="w-3.5 h-3.5" />,
      label: "IP Address",
      value: domainInfo.ip || "Unknown",
    },
    {
      icon: <MapPin className="w-3.5 h-3.5" />,
      label: "Country",
      value: domainInfo.country || "Unknown",
    },
    {
      icon: domainInfo.entity_verified ? (
        <ShieldCheck className="w-3.5 h-3.5" />
      ) : (
        <ShieldX className="w-3.5 h-3.5" />
      ),
      label: "Entity Verified",
      value: domainInfo.entity_verified ? "Verified" : "Not Verified",
      status: domainInfo.entity_verified ? "pass" : "warn",
    },
  ];

  const statusColor = {
    pass: "text-emerald-400",
    warn: "text-amber-400",
    fail: "text-red-400",
  };

  return (
    <PanelChrome title="Entity Intelligence" elevation={2} className={className}>
      {/* Grid overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 mb-4">
        {rows.map((row) => (
          <div
            key={row.label}
            className="flex items-center justify-between px-3 py-2 rounded border border-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.02)] transition-colors"
          >
            <div className="flex items-center gap-2 text-[var(--v-text-tertiary)]">
              {row.icon}
              <span className="text-[11px] uppercase tracking-wider">
                {row.label}
              </span>
            </div>
            <span
              className={cn(
                "text-[13px] font-mono",
                row.status ? statusColor[row.status] : "text-[var(--v-text)]"
              )}
            >
              {row.value}
            </span>
          </div>
        ))}
      </div>

      {/* Inconsistencies */}
      {domainInfo.inconsistencies && domainInfo.inconsistencies.length > 0 && (
        <div className="mb-4 p-3 rounded border border-amber-500/20 bg-amber-500/[0.04]">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            <h4 className="text-[10px] uppercase tracking-[0.15em] font-bold text-amber-400">
              Inconsistencies Detected
            </h4>
          </div>
          <div className="space-y-1">
            {domainInfo.inconsistencies.map((inc, i) => (
              <div
                key={i}
                className="flex items-start gap-2 text-[12px] text-[var(--v-text-secondary)]"
              >
                <span className="text-amber-500 mt-0.5 shrink-0">•</span>
                <span>{inc}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Raw WHOIS data terminal */}
      <TerminalBlock
        title="WHOIS Lookup"
        subtitle={hostname}
        command={`whois ${hostname}`}
        content={whoisLines}
      />
    </PanelChrome>
  );
}
