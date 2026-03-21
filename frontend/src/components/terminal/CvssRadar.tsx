"use client";
import React from "react";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { GhostPanel } from "./TerminalPanel";
import type { CVSSMetric } from "@/lib/types";

export function CvssRadar({ metrics, status }: { metrics: CVSSMetric[], status?: string }) {
  if (!metrics || metrics.length === 0) {
    if (status === "complete") {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-[var(--t-green)]/5">
          <span className="text-[var(--t-green)]/50 font-mono text-[10px] uppercase tracking-widest">[ NO CVEs DETECTED ]</span>
        </div>
      );
    }
    return <GhostPanel message="AWAITING VECTOR CALCULATION" />;
  }
  
  // Transform metrics
  const sevMap: Record<string, number> = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1, NONE: 0 };
  
  const data = metrics.map((m) => ({
    subject: m.name.replace(/_/g, '').substring(0, 7).toUpperCase(),
    A: sevMap[m.severity] || 0,
    fullLabel: `${m.name}: ${m.value}`,
    color: m.severity === "CRITICAL" ? "var(--t-red)" : m.severity === "HIGH" ? "var(--t-amber)" : "var(--t-green)"
  }));

  return (
    <div className="w-full h-full relative p-2 flex flex-col">
      <div className="flex flex-col gap-[2px] z-10 text-[9px] text-[var(--t-dim)] mb-2 shrink-0">
         {metrics.slice(0, 4).map((m, i) => (
           <div key={i} className="flex justify-between w-full uppercase">
             <span className="truncate pr-2">{m.name}</span>
             <span className={m.severity === "CRITICAL" || m.severity === "HIGH" ? "text-[var(--t-amber)]" : "text-[var(--t-green)]"}>
               [{m.value}]
             </span>
           </div>
         ))}
      </div>
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart cx="50%" cy="50%" outerRadius="60%" data={data}>
            <PolarGrid stroke="var(--t-border)" />
            <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--t-text)", fontSize: 9, fontFamily: "monospace" }} />
            <PolarRadiusAxis angle={30} domain={[0, 4]} tick={false} axisLine={false} />
            <Radar name="Threat" dataKey="A" stroke="var(--t-red)" fill="var(--t-red)" fillOpacity={0.25} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
