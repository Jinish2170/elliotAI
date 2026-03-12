"use client";

/* ========================================
   EvidenceGallery — Screenshot Gallery
   Grid of screenshots with finding-linked
   bounding box overlays. Lightbox expand.
   ======================================== */

import { cn } from "@/lib/utils";
import { PanelChrome } from "@/components/layout/PanelChrome";
import { SeverityBadge } from "@/components/ui/SeverityBadge";
import type { Finding, Screenshot } from "@/lib/types";
import { X, ZoomIn, Maximize2 } from "lucide-react";
import Image from "next/image";
import { useCallback, useEffect, useState } from "react";

interface EvidenceGalleryProps {
  screenshots: Screenshot[];
  findings: Finding[];
  className?: string;
}

export function EvidenceGallery({ screenshots, findings, className }: EvidenceGalleryProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  const close = useCallback(() => setExpandedIndex(null), []);

  // ESC to close
  useEffect(() => {
    if (expandedIndex === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [expandedIndex, close]);

  if (!screenshots || screenshots.length === 0) return null;

  return (
    <PanelChrome
      title="Evidence Gallery"
      count={screenshots.length}
      elevation={2}
      className={className}
    >
      {/* Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {screenshots.map((shot, i) => {
          const src = shot.data
            ? `data:image/png;base64,${shot.data}`
            : shot.url || "";
          const linkedFindings = findings.filter(
            (f) => f.screenshot_index === i || f.screenshot_index === shot.index
          );

          return (
            <button
              key={shot.index ?? i}
              onClick={() => setExpandedIndex(i)}
              className="group relative rounded border border-[rgba(255,255,255,0.06)] overflow-hidden bg-black/20 aspect-video hover:border-[rgba(255,255,255,0.15)] transition-colors"
            >
              {src ? (
                <Image
                  src={src}
                  alt={shot.label || `Screenshot ${i + 1}`}
                  fill
                  className="object-cover"
                  sizes="200px"
                  unoptimized={!!shot.data}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-[var(--v-text-tertiary)] text-xs">
                  No image
                </div>
              )}

              {/* Hover overlay */}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <ZoomIn className="w-5 h-5 text-white/80" />
              </div>

              {/* Finding count badge */}
              {linkedFindings.length > 0 && (
                <div className="absolute bottom-1 right-1 px-1.5 py-0.5 rounded bg-red-500/80 text-[9px] font-mono font-bold text-white">
                  {linkedFindings.length}
                </div>
              )}

              {/* Label */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-2 py-1">
                <span className="text-[9px] font-mono text-white/70 truncate block">
                  {shot.label || `Screenshot ${(shot.index ?? i) + 1}`}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Lightbox */}
      {expandedIndex !== null && (
        <div
          className="fixed inset-0 z-[200] bg-black/90 flex items-center justify-center p-4 cursor-pointer"
          onClick={close}
          role="dialog"
          aria-modal="true"
        >
          <div
            className="relative max-w-4xl max-h-[85vh] w-full"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={close}
              className="absolute -top-10 right-0 p-2 text-white/60 hover:text-white transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Image */}
            {(() => {
              const shot = screenshots[expandedIndex];
              const src = shot?.data
                ? `data:image/png;base64,${shot.data}`
                : shot?.url || "";
              const linkedFindings = findings.filter(
                (f) =>
                  f.screenshot_index === expandedIndex ||
                  f.screenshot_index === shot?.index
              );

              return (
                <div className="relative">
                  {src ? (
                    <Image
                      src={src}
                      alt={shot?.label || `Screenshot ${expandedIndex + 1}`}
                      width={1200}
                      height={800}
                      className="rounded-lg object-contain w-full h-auto max-h-[75vh]"
                      unoptimized={!!shot?.data}
                    />
                  ) : (
                    <div className="w-full h-64 rounded-lg bg-[var(--v-surface)] flex items-center justify-center text-[var(--v-text-tertiary)]">
                      No image available
                    </div>
                  )}

                  {/* Bounding box overlays */}
                  {linkedFindings
                    .filter((f) => f.bbox)
                    .map((f, fi) => {
                      const b = f.bbox!;
                      return (
                        <div
                          key={fi}
                          className="absolute border-2 border-red-500 rounded-sm pointer-events-none"
                          style={{
                            left: `${b[0]}%`,
                            top: `${b[1]}%`,
                            width: `${b[2] - b[0]}%`,
                            height: `${b[3] - b[1]}%`,
                          }}
                        >
                          <span className="absolute -top-5 left-0 text-[9px] font-mono bg-red-500 text-white px-1 py-0.5 rounded-sm whitespace-nowrap">
                            {(f.pattern_type || "finding").replace(/_/g, " ")}
                          </span>
                        </div>
                      );
                    })}

                  {/* Linked findings list */}
                  {linkedFindings.length > 0 && (
                    <div className="mt-3 space-y-1">
                      {linkedFindings.map((f, fi) => (
                        <div
                          key={fi}
                          className="flex items-center gap-2 px-3 py-1.5 rounded bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.06)]"
                        >
                          <SeverityBadge severity={f.severity} size="sm" />
                          <span className="text-[12px] text-[var(--v-text-secondary)] truncate">
                            {(f.pattern_type || "").replace(/_/g, " ")} — {f.description || f.plain_english || "No details"}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Navigation */}
            <div className="flex items-center justify-between mt-3">
              <button
                onClick={() =>
                  setExpandedIndex((expandedIndex - 1 + screenshots.length) % screenshots.length)
                }
                className="px-3 py-1.5 rounded border border-[rgba(255,255,255,0.1)] text-[12px] font-mono text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
              >
                ← PREV
              </button>
              <span className="text-[12px] font-mono text-[var(--v-text-tertiary)]">
                {expandedIndex + 1} / {screenshots.length}
              </span>
              <button
                onClick={() =>
                  setExpandedIndex((expandedIndex + 1) % screenshots.length)
                }
                className="px-3 py-1.5 rounded border border-[rgba(255,255,255,0.1)] text-[12px] font-mono text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
              >
                NEXT →
              </button>
            </div>
          </div>
        </div>
      )}
    </PanelChrome>
  );
}
