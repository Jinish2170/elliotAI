"use client";
import React, { useState, useEffect } from "react";
import { GhostPanel } from "./TerminalPanel";

function TypewriterText({ text, speed = 15 }: { text: string; speed?: number }) {
  const [displayed, setDisplayed] = useState("");
  
  useEffect(() => {
    let i = 0;
    setDisplayed("");
    if (!text) return;
    const interval = setInterval(() => {
      setDisplayed(text.substring(0, i));
      i++;
      if (i > text.length) clearInterval(interval);
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);

  return <>{displayed}{displayed.length < text.length && <span className="animate-pulse">_</span>}</>;
}

export function VerdictPanel({
  verdict,
  trustScore,
  status,
  error
}: {
  verdict: Record<string, any> | null;
  trustScore: number | undefined;
  status?: string;
  error?: string | null;
}) {
  if (status === "error") {
    return (
      <div className="flex flex-col items-center justify-center p-4 text-center w-full h-full border border-[var(--t-red)] bg-[#1a0505]">
        <div className="text-[var(--t-red)] font-bold text-lg mb-2 glitch-text animate-pulse">
          [!] FATAL INITIATION ERROR
        </div>
        <div className="text-[var(--t-red)] text-xs font-mono uppercase tracking-widest break-words whitespace-pre-wrap max-w-full">
          {error || "TARGET UNREACHABLE OR OFFLINE. NO VERDICT CAN BE RENDERED."}
        </div>
      </div>
    );
  }

  if (!verdict && trustScore === undefined) {
    return <GhostPanel message="AWAITING VERDICT STREAM..." />;
  }

  const score = Number(trustScore ?? verdict?.trust_score_result?.final_score ?? 0);
  const isHighRisk = score < 40;
  const isMedium = score >= 40 && score < 70;
  const colorClass = isHighRisk
    ? "text-[var(--t-red)] glow-text-red"
    : isMedium
    ? "text-[var(--t-amber)] glow-text-amber"
    : "text-[var(--t-green)] glow-text-green";

  const riskLevel = verdict?.trust_score_result?.risk_level?.toUpperCase() ||
    (isHighRisk ? "CRITICAL RISK" : isMedium ? "MODERATE RISK" : "NOMINAL");

  // Build forensic narrative from available data
  const riskLevelText = verdict?.verdict_technical?.risk_level || riskLevel;
  const techNarrative = verdict?.forensic_narrative
    || verdict?.verdict_technical?.summary
    || (score !== undefined && status === "complete" ? `Trust assessment complete. Score: ${score.toFixed(1)}/100. Classification: ${riskLevelText}. ${isHighRisk ? 'Multiple critical trust signals detected. Exercise extreme caution.' : isMedium ? 'Several moderate risk indicators present. Proceed with caution.' : 'No significant threats identified.'}` : "Awaiting advanced synthesis...");
  const nonTechNarrative = verdict?.simple_narrative
    || verdict?.verdict_nontechnical?.executive_summary
    || verdict?.verdict_nontechnical?.summary
    || (score !== undefined && status === "complete" ? `This site received a trust score of ${score.toFixed(1)} out of 100, rated as ${riskLevelText}. ${isHighRisk ? 'We recommend avoiding this site.' : isMedium ? 'Use caution when interacting with this site.' : 'This site appears trustworthy.'}` : "Awaiting plain-text synthesis...");

  return (
    <div className="flex w-full h-full p-0">
      {/* 1) SCORE BLOCK (Left) */}
      <div className="flex flex-col items-center justify-center min-w-[140px] px-4 border-r border-[var(--t-border)]">
        <div className="text-[var(--t-dim)] text-[10px] uppercase mb-1 tracking-widest">
          [ TRUST_SCORE ]
        </div>
        <div className={`text-[64px] font-bold leading-none ${colorClass}`}>
          {isNaN(score) ? "0.0" : score.toFixed(1)}
        </div>
        <div className={`text-[12px] font-bold mt-2 px-2 py-0.5 bg-[#111] border border-[var(--t-border)] ${colorClass} tracking-widest`}>
          {riskLevel}
        </div>
      </div>

      {/* 2) DUAL VERDICT SPLIT (Right) */}
      <div className="flex-1 flex flex-row h-full overflow-hidden">
        {/* Technical Persona */}
        <div className="flex-1 flex flex-col p-4 border-r border-[var(--t-border)] overflow-y-auto">
          <div className="text-[var(--t-cyan)] text-[10px] uppercase mb-2 tracking-widest shrink-0 border-b border-[var(--t-cyan)] pb-1 w-full opacity-80">
            [ FORENSIC ANALYSIS ]
          </div>
          <div className="text-[12px] leading-relaxed text-[var(--t-text)] opacity-90 whitespace-pre-wrap font-mono pr-2">
            <TypewriterText text={techNarrative} />
          </div>
          {verdict?.recommendations && verdict.recommendations.length > 0 && (
            <div className="mt-4 flex flex-col gap-1">
              <div className="text-[10px] text-[var(--t-dim)] mb-1">REMEDIATION:</div>
              {verdict.recommendations.map((r: string, idx: number) => (
                <div key={idx} className="text-[10px] text-[var(--t-amber)]">► {r}</div>
              ))}
            </div>
          )}
        </div>

        {/* Non-Technical Persona */}
        <div className="flex-1 flex flex-col p-4 overflow-y-auto">
          <div className="text-[var(--t-green)] text-[10px] uppercase mb-2 tracking-widest shrink-0 border-b border-[var(--t-green)] pb-1 w-full opacity-80">
            [ EXECUTIVE SUMMARY ]
          </div>
          <div className="text-[13px] leading-relaxed text-[var(--t-text)] opacity-90 whitespace-pre-wrap font-sans pr-2">
            <TypewriterText text={nonTechNarrative} speed={20} />
          </div>
          {verdict?.simple_recommendations && verdict.simple_recommendations.length > 0 && (
            <div className="mt-4 flex flex-col gap-1">
              <div className="text-[10px] text-[var(--t-dim)] mb-1">ADVISORY:</div>
              {verdict.simple_recommendations.map((r: string, idx: number) => (
                <div key={idx} className="text-[11px] text-[var(--t-green)] font-sans">• {r}</div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}