"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { 
  GitCompare, 
  ArrowLeft, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  AlertCircle,
  Shield,
  ExternalLink,
  ChevronRight,
  Target,
  FileText,
  Activity
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AuditSummary {
  audit_id: string;
  url: string;
  status: string;
  trust_score: number | null;
  risk_level: string | null;
  site_type: string | null;
  created_at: string;
  completed_at: string | null;
  findings_summary: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  screenshots_count: number;
}

interface TrustScoreDelta {
  from_audit_id: string;
  to_audit_id: string;
  delta: number;
  percentage_change: number | null;
}

interface RiskLevelChange {
  from_audit_id: string;
  to_audit_id: string;
  from: string;
  to: string;
}

interface CompareResponse {
  audits: AuditSummary[];
  trust_score_deltas: TrustScoreDelta[];
  risk_level_changes: RiskLevelChange[];
}

export default function ComparePage() {
  const params = useParams();
  const idsParam = params?.ids as string;
  const auditIds = idsParam ? idsParam.split(",") : [];

  const [data, setData] = useState<CompareResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (auditIds.length > 0) {
      fetchComparison();
    }
  }, [idsParam]);

  const fetchComparison = async () => {
    setLoading(true);
    try {
      const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${BASE_URL}/api/audits/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ audit_ids: auditIds }),
      });
      
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to fetch comparison data");
      }
      
      const result: CompareResponse = await res.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="pt-32 flex flex-col items-center justify-center gap-4">
        <GitCompare className="w-12 h-12 text-cyan-500 animate-pulse" />
        <p className="font-mono text-xs text-zinc-500 uppercase tracking-widest animate-pulse">Running delta analysis...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pt-32 max-w-xl mx-auto px-6 text-center">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-white mb-2">Comparison Error</h2>
        <p className="text-zinc-400 text-sm mb-6">{error}</p>
        <Link href="/history" className="text-cyan-400 font-mono text-xs uppercase underline">Back to History</Link>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="pt-24 pb-20 px-6 max-w-7xl mx-auto min-h-screen">
      {/* Header */}
      <div className="flex items-center gap-4 mb-12">
        <Link 
          href="/history" 
          className="p-2 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-500 hover:text-white hover:border-zinc-700 transition-all"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-cyan-500 mb-1">
            <GitCompare className="w-4 h-4" />
            <span className="font-mono text-[10px] tracking-[0.2em] uppercase">Comparative Forensic Analytics</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white line-clamp-1">
            Audit Comparison <span className="text-zinc-600">—</span> <span className="text-zinc-400">{data.audits[0].url}</span>
          </h1>
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {data.audits.map((audit, idx) => (
          <div key={audit.audit_id} className="relative group">
            <div className="absolute -top-3 left-4 px-2 py-0.5 bg-zinc-950 border border-zinc-800 rounded text-[9px] font-mono text-zinc-500 z-10">
              AUDIT_{idx + 1}
            </div>
            
            <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-6 shadow-xl group-hover:border-zinc-700 transition-all">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <p className="text-[10px] font-mono text-zinc-500 uppercase mb-1">{new Date(audit.created_at).toLocaleDateString()}</p>
                  <Link href={`/audit/${audit.audit_id}`} className="text-white font-bold text-sm hover:text-cyan-400 flex items-center gap-1.5 transition-colors">
                    {audit.audit_id.slice(0, 12)}...
                    <ExternalLink className="w-3 h-3 opacity-50" />
                  </Link>
                </div>
                <div className={cn(
                  "w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold font-mono",
                  audit.trust_score! > 70 ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                  audit.trust_score! > 40 ? "bg-amber-500/10 text-amber-500 border border-amber-500/20" :
                  "bg-rose-500/10 text-rose-500 border border-rose-500/20"
                )}>
                  {audit.trust_score}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-zinc-900">
                <div className="space-y-1">
                  <p className="text-[9px] font-mono text-zinc-600 uppercase">Risk Level</p>
                  <p className={cn("text-xs font-bold uppercase", 
                    audit.risk_level === 'CRITICAL' ? 'text-rose-500' : 
                    audit.risk_level === 'HIGH' ? 'text-orange-500' :
                    'text-zinc-300'
                  )}>{audit.risk_level || 'SECURE'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[9px] font-mono text-zinc-600 uppercase">Findings</p>
                  <p className="text-xs font-bold text-zinc-300">{audit.findings_summary.total}</p>
                </div>
              </div>

               {/* Findings breakdown dots */}
               <div className="mt-6 flex gap-1 h-1.5 w-full rounded-full overflow-hidden bg-zinc-900">
                  <div className="bg-rose-500 h-full" style={{ width: `${(audit.findings_summary.critical + audit.findings_summary.high) / (audit.findings_summary.total || 1) * 100}%` }} />
                  <div className="bg-amber-500 h-full" style={{ width: `${audit.findings_summary.medium / (audit.findings_summary.total || 1) * 100}%` }} />
                  <div className="bg-emerald-500 h-full flex-1" />
               </div>
            </div>
          </div>
        ))}
      </div>

      {/* Delta Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
        {/* Score Trends */}
        <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-8">
           <div className="flex items-center gap-3 mb-8">
             <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
               <TrendingUp className="w-5 h-5 text-cyan-400" />
             </div>
             <div>
               <h3 className="text-white font-bold text-lg">Trust Score Drift</h3>
               <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Chronological variance analysis</p>
             </div>
           </div>

           <div className="space-y-6">
             {data.trust_score_deltas.length === 0 ? (
               <div className="py-12 text-center text-zinc-600 font-mono text-xs">NO DELTA DETECTED</div>
             ) : (
               data.trust_score_deltas.map((delta, i) => (
                 <div key={i} className="flex items-center gap-6 group">
                   <div className="flex flex-col items-center">
                     <div className="w-2 h-2 rounded-full bg-zinc-800" />
                     <div className="w-px h-12 bg-zinc-900 group-last:hidden" />
                   </div>
                   <div className="flex-1 bg-zinc-900/40 border border-zinc-900 px-4 py-3 rounded-xl flex items-center justify-between">
                     <div className="flex items-center gap-2">
                       <span className="text-[10px] font-mono text-zinc-500">#{i+1} → #{i+2}</span>
                       <ChevronRight className="w-3 h-3 text-zinc-700" />
                     </div>
                     <div className="flex items-center gap-4">
                        <div className={cn(
                          "flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-bold font-mono",
                          delta.delta > 0 ? "text-emerald-400 bg-emerald-500/10" :
                          delta.delta < 0 ? "text-rose-500 bg-rose-500/10" :
                          "text-zinc-500 bg-zinc-800"
                        )}>
                          {delta.delta > 0 ? <TrendingUp className="w-3 h-3" /> : 
                           delta.delta < 0 ? <TrendingDown className="w-3 h-3" /> : 
                           <Minus className="w-3 h-3" />}
                          {delta.delta > 0 ? '+' : ''}{delta.delta} PTS
                        </div>
                        {delta.percentage_change !== null && (
                          <span className="text-[10px] font-mono text-zinc-600">({delta.percentage_change.toFixed(1)}%)</span>
                        )}
                     </div>
                   </div>
                 </div>
               ))
             )}
           </div>
        </div>

        {/* Change Log */}
        <div className="bg-zinc-950 border border-zinc-800 rounded-2xl p-8">
           <div className="flex items-center gap-3 mb-8">
             <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center">
               <Shield className="w-5 h-5 text-orange-400" />
             </div>
             <div>
               <h3 className="text-white font-bold text-lg">Systemic Changes</h3>
               <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">Risk & Site Identity Shifts</p>
             </div>
           </div>

           <div className="space-y-4">
             {data.risk_level_changes.length === 0 && data.audits.every((a, i, arr) => i === 0 || a.site_type === arr[i-1].site_type) ? (
                <div className="py-20 text-center flex flex-col items-center gap-3">
                   <Target className="w-8 h-8 text-emerald-500/20" />
                   <p className="text-zinc-600 font-mono text-xs tracking-widest uppercase">No significant risk mutations detected</p>
                </div>
             ) : (
               <>
                {data.risk_level_changes.map((change, i) => (
                  <div key={i} className="bg-rose-500/5 border border-rose-500/10 p-4 rounded-xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <AlertCircle className="w-4 h-4 text-rose-500" />
                      <div>
                        <p className="text-[9px] font-mono text-rose-400/60 uppercase mb-0.5">Risk Mutation</p>
                        <p className="text-xs text-white font-medium">Escalation from <span className="text-zinc-500 uppercase">{change.from}</span> to <span className="text-white font-bold uppercase">{change.to}</span></p>
                      </div>
                    </div>
                  </div>
                ))}
                
                {data.audits.map((audit, i) => (
                   i > 0 && audit.site_type !== data.audits[i-1].site_type && (
                    <div key={`type-${i}`} className="bg-cyan-500/5 border border-cyan-500/10 p-4 rounded-xl flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Activity className="w-4 h-4 text-cyan-500" />
                        <div>
                          <p className="text-[9px] font-mono text-cyan-400/60 uppercase mb-0.5">Identity Shift</p>
                          <p className="text-xs text-white font-medium">Site re-classified as <span className="text-white font-bold uppercase">{audit.site_type}</span></p>
                        </div>
                      </div>
                    </div>
                   )
                ))}
               </>
             )}
           </div>
        </div>
      </div>

      {/* Summary table for detailed drilldown */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-2xl overflow-hidden">
        <div className="px-8 py-6 border-b border-zinc-900 bg-zinc-900/30">
          <h4 className="text-sm font-bold text-white uppercase tracking-widest font-mono">Cross-Artifact Drilldown</h4>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <tbody className="divide-y divide-zinc-900">
              <tr className="bg-zinc-950">
                <td className="px-8 py-4 text-[10px] font-mono text-zinc-500 uppercase tracking-widest bg-zinc-900/20 w-48">Audit ID</td>
                {data.audits.map(a => (
                  <td key={a.audit_id} className="px-8 py-4 text-xs font-mono text-zinc-400">{a.audit_id.slice(0, 16)}...</td>
                ))}
              </tr>
              <tr>
                <td className="px-8 py-4 text-[10px] font-mono text-zinc-500 uppercase tracking-widest bg-zinc-900/20">Critical/High Findings</td>
                {data.audits.map(a => (
                  <td key={a.audit_id} className="px-8 py-4 text-xs font-bold text-rose-500">{a.findings_summary.critical + a.findings_summary.high}</td>
                ))}
              </tr>
              <tr>
                <td className="px-8 py-4 text-[10px] font-mono text-zinc-500 uppercase tracking-widest bg-zinc-900/20">Medium Findings</td>
                {data.audits.map(a => (
                  <td key={a.audit_id} className="px-8 py-4 text-xs font-bold text-amber-500">{a.findings_summary.medium}</td>
                ))}
              </tr>
              <tr>
                <td className="px-8 py-4 text-[10px] font-mono text-zinc-500 uppercase tracking-widest bg-zinc-900/20">Low Findings</td>
                {data.audits.map(a => (
                  <td key={a.audit_id} className="px-8 py-4 text-xs font-bold text-emerald-400">{a.findings_summary.low}</td>
                ))}
              </tr>
              <tr>
                <td className="px-8 py-4 text-[10px] font-mono text-zinc-500 uppercase tracking-widest bg-zinc-900/20">Site Classification</td>
                {data.audits.map(a => (
                  <td key={a.audit_id} className="px-8 py-4 text-xs font-bold text-white uppercase tracking-wider">{a.site_type || 'Unknown'}</td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
