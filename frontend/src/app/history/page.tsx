"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  Shield, 
  Search, 
  Filter, 
  ArrowRight, 
  Activity, 
  AlertTriangle, 
  FileText, 
  CheckCircle2, 
  XCircle,
  Clock,
  ExternalLink,
  GitCompare,
  Trash2,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";

interface AuditHistoryItem {
  audit_id: string;
  url: string;
  status: string;
  audit_tier: string;
  verdict_mode: string;
  trust_score: number | null;
  risk_level: string | null;
  site_type: string | null;
  created_at: string;
  completed_at: string | null;
  findings_count?: number;
}

interface HistoryResponse {
  audits: AuditHistoryItem[];
  count: number;
  limit: number;
  offset: number;
}

export default function HistoryPage() {
  const [audits, setAudits] = useState<AuditHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  
  // Selection for comparison
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [riskFilter, setRiskFilter] = useState<string>("");

  useEffect(() => {
    fetchHistory();
  }, [offset, statusFilter, riskFilter]);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      let url = `${BASE_URL}/api/audits/history?limit=${limit}&offset=${offset}`;
      if (statusFilter) url += `&status_filter=${statusFilter}`;
      if (riskFilter) url += `&risk_level_filter=${riskFilter}`;
      
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch history");
      const data: HistoryResponse = await res.json();
      setAudits(data.audits);
      setTotal(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(i => i !== id) 
        : [...prev, id].slice(0, 3) // Max 3 for comparison
    );
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "completed": return "text-emerald-400";
      case "error": return "text-rose-500";
      case "running": return "text-cyan-400";
      default: return "text-zinc-500";
    }
  };

  const getRiskColor = (risk: string | null) => {
    if (!risk) return "text-zinc-500";
    switch (risk.toLowerCase()) {
      case "critical": return "text-rose-500";
      case "high": return "text-orange-500";
      case "medium": return "text-amber-500";
      case "low": return "text-emerald-400";
      case "secure": return "text-cyan-400";
      default: return "text-zinc-400";
    }
  };

  return (
    <div className="pt-24 pb-12 px-6 max-w-7xl mx-auto min-h-screen">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-cyan-500 mb-2">
            <Clock className="w-5 h-5" />
            <span className="font-mono text-xs tracking-widest uppercase">Records Archive</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-white drop-shadow-sm">
            Audit <span className="text-zinc-500">History</span>
          </h1>
          <p className="text-zinc-400 max-w-xl text-sm leading-relaxed">
            Review past forensic investigations, track site security trends, and compare multiple reports to identify drifts in trust scoring.
          </p>
        </div>

        {/* Quick Actions / Compare Button */}
        <div className="flex items-center gap-3">
          {selectedIds.length > 0 && (
            <Link
              href={`/compare/${selectedIds.join(",")}`}
              className={cn(
                "flex items-center gap-2 px-6 py-2.5 rounded-full font-mono text-xs transition-all",
                selectedIds.length >= 2 
                  ? "bg-cyan-500 text-black font-bold hover:bg-cyan-400" 
                  : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
              )}
            >
              <GitCompare className="w-4 h-4" />
              COMPARE SELECTED ({selectedIds.length}/3)
            </Link>
          )}
        </div>
      </div>

      {/* Filters bar */}
      <div className="flex flex-wrap items-center gap-4 mb-8 bg-zinc-900/50 border border-zinc-800 p-4 rounded-xl">
        <div className="flex items-center gap-3 bg-zinc-950 border border-zinc-800 px-3 py-1.5 rounded-lg focus-within:border-cyan-500/50 transition-all">
          <Search className="w-4 h-4 text-zinc-500" />
          <input 
            type="text" 
            placeholder="Search URL..." 
            className="bg-transparent border-none text-xs text-zinc-300 focus:outline-none w-48 font-mono"
          />
        </div>

        <div className="h-4 w-px bg-zinc-800 mx-2" />

        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-zinc-500" />
          <select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-400 rounded-lg px-2 py-1.5 focus:outline-none focus:border-cyan-500/50 appearance-none pr-8 relative"
            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 0.5rem center', backgroundSize: '1rem' }}
          >
            <option value="">Status: All</option>
            <option value="completed">Completed</option>
            <option value="error">Error</option>
            <option value="running">Running</option>
          </select>
          
          <select 
            value={riskFilter}
            onChange={(e) => setRiskFilter(e.target.value)}
            className="bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-400 rounded-lg px-2 py-1.5 focus:outline-none focus:border-cyan-500/50 appearance-none pr-8 relative"
            style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 0.5rem center', backgroundSize: '1rem' }}
          >
            <option value="">Risk: All</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div className="flex-1" />

        <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest leading-none">
          Showing {audits.length} of {total} records
        </div>
      </div>

      {/* Table / Grid */}
      <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-2xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-zinc-800 bg-zinc-900/30">
              <th className="px-6 py-4 text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest w-12">
                <GitCompare className="w-4 h-4 opacity-30" />
              </th>
              <th className="px-6 py-4 text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest">Target Artifact</th>
              <th className="px-6 py-4 text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest">Investigation Date</th>
              <th className="px-6 py-4 text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest">Status</th>
              <th className="px-6 py-4 text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest text-center">Score</th>
              <th className="px-6 py-4 text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest">Risk Level</th>
              <th className="px-6 py-4 text-[10px] font-mono font-bold text-zinc-500 uppercase tracking-widest text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="animate-pulse">
                  <td colSpan={7} className="px-6 py-6 border-b border-zinc-900">
                    <div className="h-4 bg-zinc-900/50 rounded w-full" />
                  </td>
                </tr>
              ))
            ) : audits.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-20 text-center">
                  <div className="flex flex-col items-center gap-3">
                    <FileText className="w-10 h-10 text-zinc-800" />
                    <p className="text-zinc-500 font-mono text-xs uppercase tracking-widest">No audit records found</p>
                  </div>
                </td>
              </tr>
            ) : (
              audits.map((audit) => (
                <tr 
                  key={audit.audit_id} 
                  className={cn(
                    "group hover:bg-zinc-900/40 transition-colors cursor-pointer",
                    selectedIds.includes(audit.audit_id) && "bg-cyan-500/5"
                  )}
                  onClick={() => toggleSelection(audit.audit_id)}
                >
                  <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                    <input 
                      type="checkbox" 
                      checked={selectedIds.includes(audit.audit_id)}
                      onChange={() => toggleSelection(audit.audit_id)}
                      className="w-4 h-4 rounded border-zinc-800 bg-zinc-950 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-zinc-950"
                    />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-white truncate max-w-[300px] mb-0.5">{audit.url}</span>
                      <span className="text-[10px] font-mono text-zinc-600 uppercase">{audit.audit_id.slice(0, 12)}...</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-col">
                      <span className="text-xs text-zinc-400">{new Date(audit.created_at).toLocaleDateString()}</span>
                      <span className="text-[10px] font-mono text-zinc-600 uppercase">
                        {new Date(audit.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                       {audit.status === 'completed' ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : 
                        audit.status === 'error' ? <XCircle className="w-3 h-3 text-rose-500" /> : 
                        <Activity className="w-3 h-3 text-cyan-400 animate-pulse" />}
                       <span className={cn("text-[10px] font-mono uppercase tracking-wider", getStatusColor(audit.status))}>
                         {audit.status}
                       </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={cn(
                      "text-sm font-bold font-mono",
                      audit.trust_score !== null ? (audit.trust_score > 70 ? "text-emerald-400" : audit.trust_score > 40 ? "text-amber-500" : "text-rose-500") : "text-zinc-700"
                    )}>
                      {audit.trust_score !== null ? audit.trust_score : '--'}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn("text-[10px] font-mono uppercase font-bold", getRiskColor(audit.risk_level))}>
                      {audit.risk_level || (audit.status === 'completed' ? 'SECURE' : 'PENDING')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <Link 
                      href={`/audit/${audit.audit_id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:border-zinc-600 transition-all text-[11px] font-mono"
                      onClick={(e) => e.stopPropagation()}
                    >
                      DETAILS
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        
        {/* Pagination bar */}
        {!loading && total > limit && (
          <div className="flex items-center justify-between px-6 py-4 bg-zinc-900/30 border-t border-zinc-800">
            <div className="text-[10px] font-mono text-zinc-500 uppercase">
              Page {Math.floor(offset / limit) + 1} of {Math.ceil(total / limit)}
            </div>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setOffset(Math.max(0, offset - limit))}
                disabled={offset === 0}
                className="p-1.5 rounded-lg border border-zinc-800 text-zinc-500 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button 
                onClick={() => setOffset(offset + limit)}
                disabled={offset + limit >= total}
                className="p-1.5 rounded-lg border border-zinc-800 text-zinc-500 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Stats row or subtle footer info */}
      <div className="mt-8 flex items-center justify-center">
        <div className="flex items-center gap-8 bg-zinc-950/40 border border-zinc-900/50 px-8 py-3 rounded-full">
          <div className="flex flex-col items-center">
            <span className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest mb-1">Database Integrity</span>
            <span className="text-[11px] font-mono text-emerald-500 flex items-center gap-1.5">
              <Shield className="w-3 h-3" /> VERIFIED
            </span>
          </div>
          <div className="w-px h-6 bg-zinc-900" />
          <div className="flex flex-col items-center">
            <span className="text-[10px] font-mono text-zinc-600 uppercase tracking-widest mb-1">Uptime SLA</span>
            <span className="text-[11px] font-mono text-white">99.98%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
