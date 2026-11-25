"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { DomainInfo } from "@/lib/types";

/* Who is behind the site: the facts scam sites usually get wrong
   (brand-new domain, hidden owner, mismatched hosting country). */

function issuerName(raw?: string | null): string | null {
  if (!raw) return null;
  // Python ssl tuples arrive as "((('countryName', 'US'),), (('organizationName', 'X'),), ...)"
  const org = raw.match(/organizationName',\s*'([^']+)'/);
  return org ? org[1] : raw;
}

function age(days?: number | null): string {
  if (typeof days !== "number" || days < 0) return "unknown";
  if (days < 60) return `${days} days (very new)`;
  if (days < 365) return `${Math.round(days / 30)} months`;
  return `${(days / 365).toFixed(1)} years`;
}

export function DomainFactsPanel({ info, url, status }: { info?: DomainInfo | null; url?: string | null; status?: string }) {
  if (!info) {
    return <GhostPanel message={status === "complete" ? "NO DOMAIN DATA" : "DOMAIN RECORDS CHECKED IN STEP 4 OF 5"} />;
  }
  let host = "";
  try { host = url ? new URL(url).hostname : ""; } catch {}
  const rows: [string, string, boolean?][] = [
    ["Domain age", age(info.age_days), typeof info.age_days === "number" && info.age_days >= 0 && info.age_days < 60],
    ["Registrar", info.registrar || "not public"],
    ["Certificate", issuerName(info.ssl_issuer) || "none found", !info.ssl_issuer],
    ["Server IP", info.ip || "unknown"],
    ["Hosted in", info.country || "unknown"],
    ["Business identity", info.entity_verified ? "confirmed elsewhere" : "not confirmed"],
  ];
  return (
    <div className="w-full h-full overflow-y-auto p-3 font-mono text-[11px]">
      {host && <div className="font-bold mb-2 break-all">{host}</div>}
      <div className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1">
        {rows.map(([k, v, warn]) => (
          <React.Fragment key={k}>
            <span className="text-[var(--t-dim)]">{k}</span>
            <span className={warn ? "text-[var(--t-amber)]" : "text-[var(--t-text)]"}>{v}</span>
          </React.Fragment>
        ))}
      </div>
      {info.inconsistencies && info.inconsistencies.length > 0 && (
        <div className="mt-2 text-[10px] text-[var(--t-red)]">
          {info.inconsistencies.slice(0, 3).map((x, i) => <div key={i}>! {x}</div>)}
        </div>
      )}
    </div>
  );
}
