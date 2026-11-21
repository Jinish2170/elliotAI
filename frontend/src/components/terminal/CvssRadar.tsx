"use client";
import React, { useMemo, memo } from "react";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import { GhostPanel } from "./TerminalPanel";
import type { CVSSMetric, CVSSMeta } from "@/lib/types";

/* CVSS panel
   Shows the industry-standard CVSS v3.1 estimate in plain English:
   every metric has a question, an answer and the evidence that set it,
   plus the vector string and a link to FIRST.org's calculator so anyone
   can re-compute the score themselves. */

const BAND_PLAIN: Record<string, string> = {
  none: "No measurable risk was found.",
  low: "Small risk. Worth knowing, not alarming.",
  medium: "Moderate risk. Some issues need attention before you trust this site with anything sensitive.",
  high: "Serious risk. Be careful with this site.",
  critical: "Severe risk. Avoid entering any information here.",
};

function levelColor(level: number | undefined, abbr?: string): string {
  // Impact metrics (C, I, A): more = worse. Reach metrics are context, shown neutral.
  if (abbr === "C" || abbr === "I" || abbr === "A" || abbr === "S") {
    return (level ?? 0) >= 4 ? "var(--t-red)" : (level ?? 0) >= 2 ? "var(--t-amber)" : "var(--t-green)";
  }
  return "var(--t-dim)";
}

function CvssRadarComponent({
  metrics,
  status,
  score,
  meta,
}: {
  metrics: CVSSMetric[];
  status?: string;
  score?: number | null;
  meta?: CVSSMeta | null;
}) {
  const rows = useMemo(() => (metrics && metrics.length ? metrics : []), [JSON.stringify(metrics)]);

  const data = useMemo(
    () =>
      rows.map((m, idx) => ({
        subject: (m.label || m.name || `metric_${idx}`).toString(),
        A: typeof m.level === "number" ? m.level : 0,
      })),
    [rows]
  );

  if (rows.length === 0) {
    if (status === "complete") {
      return (
        <div className="w-full h-full flex flex-col items-center justify-center p-4 text-center bg-[var(--t-green)]/5">
          <span className="text-[var(--t-green)]/50 font-mono text-[11px] uppercase tracking-widest">
            [ NO CVSS RISK SCORE FOR THIS AUDIT ]
          </span>
        </div>
      );
    }
    return <GhostPanel message="AWAITING VECTOR CALCULATION" />;
  }

  const band = (meta?.severity || "").toLowerCase();

  return (
    <div className="w-full h-full overflow-y-auto p-3 font-mono text-[11px] text-[var(--t-text)]">
      {/* Headline in plain language */}
      <div className="mb-3 border border-[var(--t-border)] bg-[#0a0a0a] p-2">
        <div className="flex items-baseline gap-3">
          <span className="text-[22px] font-bold text-[var(--t-amber)]">
            {typeof score === "number" ? score.toFixed(1) : "-"}
            <span className="text-[11px] text-[var(--t-dim)]"> / 10</span>
          </span>
          {band && <span className="uppercase tracking-widest text-[var(--t-amber)]">{band}</span>}
        </div>
        <p className="mt-1 opacity-80 leading-relaxed">
          This is a <b>CVSS v3.1</b> score, the standard security teams use to rate how risky a problem is
          (0 = harmless, 10 = severe). {BAND_PLAIN[band] ?? ""} It is calculated from what elliotAI actually found on
          this site, not guessed.
        </p>
      </div>

      <div className="flex gap-3 items-start">
        {/* Radar: taller = more concerning on that question */}
        <div className="w-[38%] min-w-[150px] h-[190px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="62%" data={data}>
              <PolarGrid stroke="var(--t-border)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--t-text)", fontSize: 9, fontFamily: "monospace" }} />
              <PolarRadiusAxis angle={30} domain={[0, 4]} tick={false} axisLine={false} />
              <Radar name="Risk" dataKey="A" stroke="var(--t-red)" fill="var(--t-red)" fillOpacity={0.25} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Every metric: question, answer, evidence */}
        <div className="flex-1 min-w-0 flex flex-col gap-2">
          {rows.map((m, i) => (
            <div key={i} className="border-l-2 pl-2" style={{ borderColor: levelColor(m.level, m.abbr) }}>
              <div className="flex justify-between gap-2">
                <span className="opacity-90">{m.question || m.name}</span>
                <span className="uppercase font-bold whitespace-nowrap">{m.value}</span>
              </div>
              {m.why && <div className="text-[10px] text-[var(--t-dim)] leading-snug">{m.why}</div>}
            </div>
          ))}
        </div>
      </div>

      {/* Proof: anyone can reproduce the number */}
      {meta?.vector && (
        <div className="mt-3 border-t border-[var(--t-border)] pt-2 text-[10px] text-[var(--t-dim)] leading-relaxed">
          <div>
            Vector: <span className="text-[var(--t-green)] break-all">{meta.vector}</span>
          </div>
          {meta.calculatorUrl && (
            <div>
              Verify it yourself:{" "}
              <a href={meta.calculatorUrl} target="_blank" rel="noopener noreferrer" className="text-[var(--t-amber)] underline">
                open this vector in FIRST.org&apos;s official calculator
              </a>{" "}
              and you will get the same {typeof score === "number" ? score.toFixed(1) : "score"}.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export const CvssRadar = memo(CvssRadarComponent, (prev, next) => {
  return (
    prev.status === next.status &&
    prev.score === next.score &&
    JSON.stringify(prev.meta) === JSON.stringify(next.meta) &&
    JSON.stringify(prev.metrics) === JSON.stringify(next.metrics)
  );
});
