"use client";

import { ArrowLeft, Download, Plus, Share2 } from "lucide-react";
import Link from "next/link";

interface ReportHeaderProps {
  url: string;
  date: string;
  auditId: string;
  mode: "simple" | "expert";
  onToggleMode: () => void;
}

export function ReportHeader({ url, date, auditId, mode, onToggleMode }: ReportHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <Link
            href={`/audit/${auditId}`}
            className="p-1.5 rounded-lg border border-white/10 hover:border-white/20 text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <h1 className="text-xl font-bold text-[var(--v-text)]">Veritas Forensic Report</h1>
        </div>
        <p className="text-sm text-[var(--v-text-secondary)] font-mono">{url}</p>
        <p className="text-xs text-[var(--v-text-tertiary)] mt-0.5">{date}</p>
      </div>

      <div className="flex items-center gap-3">
        {/* Mode toggle */}
        <div className="flex rounded-lg bg-white/5 p-0.5 border border-white/10">
          <button
            onClick={() => mode !== "simple" && onToggleMode()}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              mode === "simple"
                ? "bg-[var(--v-surface)] text-[var(--v-text)]"
                : "text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
            }`}
          >
            Simple
          </button>
          <button
            onClick={() => mode !== "expert" && onToggleMode()}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
              mode === "expert"
                ? "bg-[var(--v-surface)] text-[var(--v-text)]"
                : "text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)]"
            }`}
          >
            Expert
          </button>
        </div>

        {/* Actions */}
        <button className="p-2 rounded-lg border border-white/10 hover:border-white/20 text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors">
          <Download className="w-4 h-4" />
        </button>
        <button className="p-2 rounded-lg border border-white/10 hover:border-white/20 text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors">
          <Share2 className="w-4 h-4" />
        </button>
        <Link
          href="/"
          className="p-2 rounded-lg border border-white/10 hover:border-white/20 text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
        >
          <Plus className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
}
