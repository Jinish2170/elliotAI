"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { usePathname } from "next/navigation";

export function Navbar() {
  const pathname = usePathname();
  const isAuditPage = pathname?.startsWith("/audit");
  const isReportPage = pathname?.startsWith("/report");

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 bg-[var(--v-deep)]/80 backdrop-blur-xl"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white group-hover:shadow-[0_0_15px_rgba(6,182,212,0.4)] transition-shadow">
            V
          </div>
          <span className="font-bold text-sm tracking-widest text-[var(--v-text)]">
            VERITAS
          </span>
        </Link>

        {/* Right links */}
        <div className="flex items-center gap-6">
          {(isAuditPage || isReportPage) && (
            <Link
              href="/"
              className="text-xs text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
            >
              New Audit
            </Link>
          )}
          <Link
            href="/#how-it-works"
            className="text-xs text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors hidden sm:block"
          >
            How It Works
          </Link>
          <Link
            href="/#dark-patterns"
            className="text-xs text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors hidden sm:block"
          >
            Dark Patterns
          </Link>
        </div>
      </div>
    </motion.nav>
  );
}
