"use client";

/* ========================================
   SectionNav — Left-Rail Sticky Navigation
   Scrollspy-enabled section nav for report page.
   Shows filled/empty circle + section name.
   ======================================== */

import { cn } from "@/lib/utils";
import { useCallback, useEffect, useRef, useState } from "react";

interface Section {
  id: string;
  label: string;
  /** Optional inline summary (e.g., "4 of 6 below threshold") */
  summary?: string;
}

interface SectionNavProps {
  sections: Section[];
  className?: string;
}

export function SectionNav({ sections, className }: SectionNavProps) {
  const [activeId, setActiveId] = useState<string>(sections[0]?.id || "");
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Scrollspy via IntersectionObserver
  useEffect(() => {
    if (typeof window === "undefined") return;

    observerRef.current = new IntersectionObserver(
      (entries) => {
        // Find the first visible section
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible.length > 0) {
          setActiveId(visible[0].target.id);
        }
      },
      {
        rootMargin: "-80px 0px -60% 0px",
        threshold: 0,
      }
    );

    sections.forEach((s) => {
      const el = document.getElementById(s.id);
      if (el) observerRef.current?.observe(el);
    });

    return () => observerRef.current?.disconnect();
  }, [sections]);

  const scrollTo = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    // Update URL hash without scroll
    window.history.replaceState(null, "", `#${id}`);
  }, []);

  return (
    <nav
      className={cn(
        "sticky top-20 w-[160px] flex flex-col gap-0.5",
        className
      )}
      aria-label="Report sections"
    >
      {sections.map((s) => {
        const isActive = activeId === s.id;
        return (
          <button
            key={s.id}
            onClick={() => scrollTo(s.id)}
            className={cn(
              "flex items-start gap-2 px-2 py-1.5 rounded text-left transition-all duration-200",
              "hover:bg-[rgba(255,255,255,0.04)]",
              isActive && "bg-[rgba(255,255,255,0.04)]"
            )}
          >
            {/* Circle indicator */}
            <div className="mt-[3px] shrink-0">
              <div
                className={cn(
                  "w-2 h-2 rounded-full border transition-all duration-200",
                  isActive
                    ? "bg-[var(--v-text)] border-[var(--v-text)]"
                    : "bg-transparent border-[rgba(255,255,255,0.2)]"
                )}
              />
            </div>
            <div className="min-w-0">
              <span
                className={cn(
                  "block text-[13px] leading-snug transition-colors duration-200",
                  isActive
                    ? "text-[var(--v-text)] font-medium"
                    : "text-[var(--v-text-tertiary)]"
                )}
              >
                {s.label}
              </span>
              {s.summary && (
                <span className="block text-[9px] font-mono text-[var(--v-text-tertiary)] leading-tight mt-0.5 truncate">
                  {s.summary}
                </span>
              )}
            </div>
          </button>
        );
      })}
    </nav>
  );
}
