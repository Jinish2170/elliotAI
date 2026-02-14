"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Clock, ArrowLeft, ExternalLink } from "lucide-react";

interface AuditHeaderProps {
  url: string | null;
  status: string;
  auditId: string | null;
  elapsed: number;
}

export function AuditHeader({ url, status, auditId, elapsed }: AuditHeaderProps) {
  const [timer, setTimer] = useState(elapsed);

  useEffect(() => {
    if (status !== "running") return;
    const interval = setInterval(() => setTimer((t) => t + 1), 1000);
    return () => clearInterval(interval);
  }, [status]);

  // Sync from backend-reported elapsed
  useEffect(() => {
    if (elapsed > 0) setTimer(elapsed);
  }, [elapsed]);

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}m ${sec.toString().padStart(2, "0")}s`;
  };

  const statusStyles: Record<string, string> = {
    connecting: "text-amber-400",
    running: "text-cyan-400",
    complete: "text-emerald-400",
    error: "text-red-400",
  };

  return (
    <div className="flex items-center justify-between px-1 mb-4">
      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="p-1.5 rounded-lg border border-white/10 hover:border-white/20 text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-sm font-bold text-[var(--v-text)] flex items-center gap-2">
            Veritas Audit
            <span className={`text-[10px] font-medium ${statusStyles[status] || ""}`}>
              {status === "running" ? "● LIVE" : status.toUpperCase()}
            </span>
          </h1>
          {url && (
            <p className="text-xs text-[var(--v-text-secondary)] flex items-center gap-1 font-mono">
              {url}
              <ExternalLink className="w-3 h-3" />
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 text-[var(--v-text-secondary)]">
        <Clock className="w-3.5 h-3.5" />
        <span className="text-sm font-mono tabular-nums">{formatTime(timer)}</span>
      </div>
    </div>
  );
}
