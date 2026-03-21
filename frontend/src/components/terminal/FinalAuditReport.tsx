"use client";

import React from "react";
import { Finding } from "@/lib/types";

interface FinalAuditReportProps {
  url?: string;
  findings: Finding[];
  advancedData?: any;
  onClose: () => void;
  trustScore?: number;
  riskLevel?: string;
}

export function FinalAuditReport({ url, findings, advancedData, onClose, trustScore, riskLevel }: FinalAuditReportProps) {
  
  const handleExportJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify({ url, findings, advancedData, trustScore, riskLevel }, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "veritas_audit_report.json");
    document.body.appendChild(downloadAnchorNode); 
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  return (
    <div className="w-full h-full bg-[#050505] text-[var(--t-text)] font-mono p-4 md:p-8 overflow-y-auto animate-in fade-in duration-500">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-8 border-b border-[var(--t-border)] pb-4">
          <h1 className="text-2xl text-[var(--t-green)] font-bold uppercase tracking-widest flex items-center gap-3">
            <span className="text-[var(--t-cyan)] animate-pulse">#</span> FINAL AUDIT REPORT
          </h1>
          <div className="flex gap-4">
            <button 
              onClick={handleExportJson}
              className="border border-[var(--t-cyan)] text-[var(--t-cyan)] px-4 py-2 text-[10px] hover:bg-[var(--t-cyan)] hover:text-black transition-colors uppercase tracking-widest font-bold"
            >
              [ EXPORT JSON ]
            </button>
            <button 
              onClick={onClose}
              className="text-[var(--t-dim)] hover:text-white transition-colors uppercase tracking-widest text-[10px]"
            >
              [ CLOSE ]
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="col-span-2 border border-[var(--t-border)] p-6 bg-black/50">
            <h2 className="text-sm text-[var(--t-dim)] uppercase tracking-widest mb-4">EXECUTIVE SUMMARY</h2>
            <div className="grid grid-cols-2 gap-4 text-[13px] mb-6">
              <div>
                <div className="text-[var(--t-dim)] uppercase text-[10px] mb-1">Target</div>
                <div className="text-[var(--t-cyan)] truncate">{url || "UNKNOWN"}</div>
              </div>
              <div>
                <div className="text-[var(--t-dim)] uppercase text-[10px] mb-1">Total Findings</div>
                <div className="text-[var(--t-amber)]">{findings.length}</div>
              </div>
            </div>
            {advancedData?.narrative && (
              <div>
                <div className="text-[var(--t-dim)] uppercase text-[10px] mb-2">Narrative</div>
                <div className="text-[13px] opacity-90 leading-relaxed whitespace-pre-wrap text-[var(--t-text)]">
                  {advancedData.narrative}
                </div>
              </div>
            )}
            {advancedData?.verdict && (
               <div className="mt-4">
                <div className="text-[var(--t-dim)] uppercase text-[10px] mb-2">Judge Verdict</div>
                <div className="text-[13px] opacity-90 leading-relaxed whitespace-pre-wrap text-[var(--t-text)]">
                  {advancedData.verdict.overview || advancedData.verdict.technical_narrative}
                </div>
              </div>
            )}
          </div>

          <div className="border border-[var(--t-border)] p-6 bg-black/50 flex flex-col items-center justify-center text-center">
            <div className="text-[var(--t-dim)] uppercase text-[10px] tracking-widest mb-4">TRUST SCORE</div>
            <div className={`text-6xl font-bold mb-2 ${
              trustScore && trustScore >= 80 ? 'text-[var(--t-green)]' 
              : trustScore && trustScore >= 50 ? 'text-[var(--t-amber)]' 
              : 'text-[var(--t-red)]'
            }`}>
              {trustScore ?? "N/A"}
            </div>
            <div className="text-[var(--t-dim)] uppercase text-[10px] tracking-widest mt-4">RISK LEVEL</div>
            <div className={`text-lg font-bold uppercase tracking-widest mt-1 ${
              riskLevel === 'critical' || riskLevel === 'high' ? 'text-[var(--t-red)]' 
              : riskLevel === 'medium' ? 'text-[var(--t-amber)]' 
              : 'text-[var(--t-green)]'
            }`}>
              {riskLevel || "UNKNOWN"}
            </div>
          </div>
        </div>

        {advancedData?.verdict?.recommendations && advancedData.verdict.recommendations.length > 0 && (
          <div className="border border-[var(--t-border)] p-6 mb-8 bg-black/30">
            <h2 className="text-[12px] text-[var(--t-cyan)] font-bold mb-4 uppercase tracking-widest border-b border-[var(--t-border)] pb-2">
              ACTIONABLE REMEDIATION
            </h2>
            <ul className="space-y-3">
              {advancedData.verdict.recommendations.map((rec: string, i: number) => (
                <li key={i} className="flex gap-4 items-start text-[13px]">
                  <span className="text-[var(--t-cyan)] mt-1">▶</span>
                  <span className="opacity-90 leading-relaxed">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {findings.length > 0 && (
          <div className="border border-[var(--t-border)] p-6 mb-8 bg-black/30">
            <h2 className="text-[12px] text-white font-bold mb-4 uppercase tracking-widest border-b border-[var(--t-border)] pb-2 flex justify-between">
              <span>TECHNICAL BREAKDOWN</span>
              <span className="text-[var(--t-amber)]">{findings.length} ISSUES</span>
            </h2>
            <div className="flex flex-col gap-4">
              {findings.map((f, idx) => {
                const isHigh = f.severity === 'critical' || f.severity === 'high';
                const color = isHigh ? 'var(--t-red)' : f.severity === 'medium' ? 'var(--t-amber)' : 'var(--t-green)';
                
                return (
                  <div key={f.id || idx} className="border-l-2 pl-4 py-2" style={{ borderColor: color, backgroundColor: 'rgba(0,0,0,0.3)' }}>
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-bold text-[14px]" style={{ color }}>{f.category}</div>
                      <div className="text-[10px] px-2 py-1 rounded-sm uppercase tracking-wider font-bold" style={{ backgroundColor: `${color}20`, color }}>
                        {f.severity}
                      </div>
                    </div>
                    <div className="text-[12px] opacity-80 whitespace-pre-wrap">{f.description}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="text-center text-[10px] text-[var(--t-dim)] uppercase tracking-widest mt-12 pb-8">
          END OF REPORT / {new Date().toISOString()} / VERITAS SYSTEM.
        </div>
      </div>
    </div>
  );
}
