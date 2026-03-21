"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { CVEEntry, Tor2WebThreatData, MarketplaceThreatData } from "@/lib/types";

interface Props {
	cves: CVEEntry[];
	tor: Tor2WebThreatData[];
	marketplace: MarketplaceThreatData[];
}

export function DarknetOsintGrid({ cves, tor, marketplace }: Props) {
	const isEmpty = !cves?.length && !tor?.length && !marketplace?.length;
	if (isEmpty) return <GhostPanel message="OSINT ACTIVE - DEEP_WEB MONITORING" />;

	return (
		<div className="w-full h-full overflow-y-auto p-3 flex flex-row gap-4 align-top items-start">
			{/* CVEs Column */}
			<div className="flex-1 flex flex-col gap-2 min-w-0">
				<div className="text-[10px] text-[var(--t-red)] border-b border-[var(--t-red)] pb-1 shrink-0">
					DETECTED_CVES <span className="opacity-70">[{cves?.length || 0}]</span>
				</div>
				<div className="flex flex-col gap-1 overflow-y-auto pr-1">
					{!cves?.length && <span className="text-[10px] text-[var(--t-dim)]">NO DATA</span>}
					{cves?.map((c, i) => (
						<div key={i} className="text-[10px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-red)] shrink-0">
							<span className="font-bold">{c.cve_id || "UNKNOWN"}</span>
							<span className="opacity-70 truncate">{c.name || ""}</span>
						</div>
					))}
				</div>
			</div>

			{/* Tor2Web Column */}
			<div className="flex-1 flex flex-col gap-2 min-w-0 border-l border-[var(--t-border)] pl-4">
				<div className="text-[10px] text-[var(--t-amber)] border-b border-[var(--t-amber)] pb-1 shrink-0">
					ANONYMITY_BREACH <span className="opacity-70">[{tor?.length || 0}]</span>
				</div>
				<div className="flex flex-col gap-1 overflow-y-auto pr-1">
					{!tor?.length && <span className="text-[10px] text-[var(--t-dim)]">NO DATA</span>}
					{tor?.map((t, i) => (
						<div key={i} className="text-[10px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-amber)] shrink-0">
							<span className="font-bold text-[var(--t-amber)]">RISK: {(t.de_anon_risk || "UNKNOWN").toUpperCase()}</span>
							<span className="opacity-70 truncate" title={t.gateway_domains?.join(", ") || ""}>GW: {t.gateway_domains?.[0] || "N/A"}</span>
						</div>
					))}
				</div>
			</div>

			{/* Marketplace Column */}
			<div className="flex-1 flex flex-col gap-2 min-w-0 border-l border-[var(--t-border)] pl-4">
				<div className="text-[10px] text-[var(--t-amber)] border-b border-[var(--t-amber)] pb-1 shrink-0">
					MARKETPLACE_ACTOR <span className="opacity-70">[{marketplace?.length || 0}]</span>
				</div>
				<div className="flex flex-col gap-1 overflow-y-auto pr-1">
					{!marketplace?.length && <span className="text-[10px] text-[var(--t-dim)]">NO DATA</span>}
					{marketplace?.map((m, i) => (
						<div key={i} className="text-[10px] flex flex-col bg-[#111] p-1.5 border-l-2 border-[var(--t-amber)] shrink-0">
							<span className="font-bold truncate">{(m.marketplace_name || "UNKNOWN").toUpperCase()}</span>
							<span className="opacity-70 flex justify-between">
								<span className="truncate pr-2">T: {m.marketplace_type || "UNK"}</span>
								<span className="text-[var(--t-text)]">C: {((m.confidence ?? 0) * 100).toFixed(0)}%</span>
							</span>
						</div>
					))}
				</div>
			</div>
		</div>
	);
}