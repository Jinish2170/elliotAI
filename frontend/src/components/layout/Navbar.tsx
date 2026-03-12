"use client";

import { Activity, Clock, Plus, Shield } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function Navbar() {
  const pathname = usePathname();
  const isAuditPage = pathname?.startsWith("/audit");
  const isReportPage = pathname?.startsWith("/report");
  const isHistoryPage = pathname?.startsWith("/history");

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-[rgba(255,255,255,0.04)] bg-[var(--v-deep)]/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-12 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <Shield className="w-4 h-4 text-cyan-500 group-hover:text-cyan-400 transition-colors" />
          <span className="font-bold text-[12px] font-mono tracking-[0.2em] text-[var(--v-text)]">
            VERITAS
          </span>
          <span className="text-[8px] font-mono text-[var(--v-text-tertiary)] border border-[rgba(255,255,255,0.08)] rounded px-1 py-0.5">
            v2.0
          </span>
        </Link>

        {/* Center — status */}
        <div className="hidden sm:flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span className="text-[9px] font-mono text-[var(--v-text-tertiary)] uppercase tracking-wider">
            System Online
          </span>
        </div>

        {/* Right nav */}
        <div className="flex items-center gap-1">
          <Link
            href="/history"
            className={cn(
              "flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[11px] font-mono transition-colors",
              isHistoryPage
                ? "text-cyan-400 bg-cyan-500/10"
                : "text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] hover:bg-[rgba(255,255,255,0.03)]"
            )}
          >
            <Clock className="w-3 h-3" />
            HISTORY
          </Link>

          {(isAuditPage || isReportPage) && (
            <Link
              href="/"
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded text-[11px] font-mono text-[var(--v-text-tertiary)] hover:text-[var(--v-text-secondary)] hover:bg-[rgba(255,255,255,0.03)] transition-colors"
            >
              <Plus className="w-3 h-3" />
              NEW
            </Link>
          )}

          {isAuditPage && (
            <div className="flex items-center gap-1.5 px-2.5 py-1.5">
              <Activity className="w-3 h-3 text-cyan-400 animate-pulse" />
              <span className="text-[9px] font-mono text-cyan-400 uppercase">LIVE</span>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
