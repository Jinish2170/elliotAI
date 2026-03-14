"use client";

import { getVerdictLevel, VERDICT_COLORS } from "@/config/agents";
import Link from "next/link";
import { useEffect, useState } from "react";

interface AuditRecord {
  id: string;
  url: string;
  score: number;
  riskLevel: string;
  date: string;
  tier: string;
}

const STORAGE_KEY = "veritas_recent_audits";

export function saveAuditToHistory(record: AuditRecord) {
  if (typeof window === "undefined") return;
  try {
    const existing = localStorage.getItem(STORAGE_KEY);
    let audits: AuditRecord[] = existing ? JSON.parse(existing) : [];
    audits = [record, ...audits.filter((a) => a.id !== record.id)].slice(0, 10);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(audits));
  } catch (err) {
    console.error("Failed to save audit history", err);
  }
}

export function RecentAudits() {
  const [audits, setAudits] = useState<AuditRecord[]>([]);

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        let parsed = JSON.parse(stored);
        parsed = parsed.map((a: AuditRecord) => ({
          ...a,
          date: new Date(a.date).toLocaleDateString(),
        }));
        setAudits(parsed);
      }
    } catch {
      // ignore
    }
  }, []);

  if (audits.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[10px] text-[var(--t-dim)] font-mono uppercase tracking-widest">
        <span className="animate-pulse">LOCAL_HISTORY_EMPTY</span>
        <span className="opacity-50 mt-2">AWAITING_FIRST_AUDIT</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
       <div className="text-[10px] font-mono text-[var(--t-dim)] uppercase tracking-widest border-b border-[var(--t-border)] pb-2 mb-2 flex justify-between">
         <span>LOCAL.AUDIT_HISTORY</span>
         <span className="text-[var(--t-text)]">[{audits.length}]</span>
      </div>
      
      <div className="flex-1 overflow-y-auto pr-1 flex flex-col gap-2">
        {audits.map((audit) => {
          const isCritical = audit.score < 40;
          const isWarning = audit.score >= 40 && audit.score < 70;
          const barColor = isCritical ? "bg-[#FF003C]" : isWarning ? "bg-[#FFB000]" : "bg-[#00FF41]";
          const textColor = isCritical ? "text-[#FF003C]" : isWarning ? "text-[#FFB000]" : "text-[#00FF41]";

          return (
            <Link
              key={audit.id}
              href={"/audit/"}
              className={"block border border-[var(--t-border)] bg-[#111] p-2 hover:border-[#00FF41] transition-colors cursor-pointer group"}
            >
              <div className="flex justify-between items-center mb-1">
                <span className="text-[11px] font-bold font-mono text-[var(--t-text)] truncate max-w-[200px] group-hover:text-[#00FF41] transition-colors">
                  {audit.url}
                </span>
                <span className={"text-[10px] font-bold font-mono "}>
                  V-SCORE: {audit.score}
                </span>
              </div>
              
              <div className="flex justify-between items-center text-[9px] font-mono text-[var(--t-dim)] uppercase">
                 <span>{audit.date}</span>
                 <span>{audit.tier.replace(/_/g, " ")}</span>
                 <span className={textColor}>{audit.riskLevel}</span>
              </div>

               {/* Score Bar */}
              <div className="mt-2 w-full h-[2px] bg-[#222]">
                <div className={`h-full ${barColor} opacity-70`} style={{ width: `${Math.min(audit.score, 100)}%` }} />
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
