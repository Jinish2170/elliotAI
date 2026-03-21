"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { TechniqueMatch } from "@/lib/types";

export function MitreGrid({ techniques, status }: { techniques: TechniqueMatch[], status?: string }) {
	if (!techniques || techniques.length === 0) {
    if (status === "complete") {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-[var(--t-green)]/5">
          <span className="text-[var(--t-green)]/50 font-mono text-[10px] uppercase tracking-widest">[ NO TTPs DETECTED ]</span>
        </div>
      );
    }
    return <GhostPanel message="AWAITING CTI MAPPING" />;
  }

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
							<td className="p-2 opacity-70 uppercase truncate max-w-[80px]" title={t.tactic || ""}>
								{(t.tactic || "").replace("x-mitre-tactic-", "").replace(/-/g, " ")}
							</td>
							<td className="p-2 uppercase truncate max-w-[120px]" title={t.technique_name || ""}>
								{t.technique_name || "UNKNOWN"}
							</td>
						</tr>
					))}
				</tbody>
			</table>
		</div>
	);
}