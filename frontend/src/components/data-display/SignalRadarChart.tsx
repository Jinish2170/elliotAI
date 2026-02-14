"use client";

import {
    PolarAngleAxis,
    PolarGrid,
    PolarRadiusAxis,
    Radar,
    RadarChart as RechartsRadarChart,
    ResponsiveContainer,
} from "recharts";

interface SignalRadarChartProps {
  scores: Record<string, number>;
}

const SIGNAL_LABELS: Record<string, string> = {
  visual: "Visual",
  structural: "Structure",
  temporal: "Temporal",
  graph: "Identity",
  meta: "Meta",
  security: "Security",
};

export function SignalRadarChart({ scores }: SignalRadarChartProps) {
  const data = Object.entries(SIGNAL_LABELS).map(([key, label]) => ({
    signal: label,
    score: scores[key] ?? 0,
    fullMark: 100,
  }));

  return (
    <div className="w-full h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
          <PolarGrid
            stroke="rgba(255,255,255,0.08)"
            strokeDasharray="3 3"
          />
          <PolarAngleAxis
            dataKey="signal"
            tick={{ fill: "#9CA3AF", fontSize: 11 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fill: "#6B7280", fontSize: 9 }}
            tickCount={5}
          />
          <Radar
            name="Trust Signals"
            dataKey="score"
            stroke="#06B6D4"
            fill="#06B6D4"
            fillOpacity={0.15}
            strokeWidth={2}
          />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
}
