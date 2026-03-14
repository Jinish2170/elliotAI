"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { TechniqueMatch } from "@/lib/types";

export function MitreGrid({ techniques }: { techniques: TechniqueMatch[] }) {
  if (!techniques || techniques.length === 0) return <GhostPanel message="AWAITING CTI MAPPING" />;
  
  return (
    <div className="w-full h-full overflow-y-auto p-2">
      <table className="w-full text-left text-[10px] border-collapse sticky top-0">
        <thead className="bg-[#111]">
          <tr className="border-b border-[var(--t-border)] text-[var(--t-dim)] uppercase">
             <th className="p-2 font-normal">TID</th>
             <th className="p-2 font-normal">TACTIC</th>
             <th className="p-2 font-normal">TECHNIQUE</th>
          </tr>
        </thead>
        <tbody className="text-[var(--t-text)]">
          {techniques.map((t, idx) => (
             <tr key={idx} className="border-b border-[var(--t-border)] hover:bg-[#1a1a1a] transition-colors">
               <td className="p-2 text-[var(--t-amber)] font-bold">{t.technique_id}</td>
               <td className="p-2 opacity-70 uppercase truncate max-w-[80px]" title={t.tactic}>
                 {t.tactic.replace("x-mitre-tactic-", "").replace(/-/g, " ")}
               </td>
               <td className="p-2 uppercase truncate max-w-[120px]" title={t.technique_name}>
                 {t.technique_name}
               </td>
             </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
