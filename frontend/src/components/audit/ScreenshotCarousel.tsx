"use client";

import type { Finding, HighlightOverlay, Screenshot } from "@/lib/types";
import { bboxToPixels, SEVERITY_OVERLAY_COLOR, SEVERITY_SOLID_COLOR } from "@/lib/types";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, ChevronRight, Maximize2, Minimize2, ToggleLeft, ToggleRight } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

interface ScreenshotCarouselProps {
  screenshots: Screenshot[];
  initialIndex?: number;
  onFindings?: (screenshotIndex: number) => Finding[]; // callback to get findings
  onHighlightFinding?: (findingId: string) => void; // callback when user clicks on overlay
}

export function ScreenshotCarousel({
  screenshots,
  initialIndex = 0,
  onFindings,
  onHighlightFinding,
}: ScreenshotCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [showOverlays, setShowOverlays] = useState(true);
  const [zoom, setZoom] = useState(1.0);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const containerRef = useRef<HTMLDivElement>(null);

  // Reset zoom/pan when changing screenshots
  useEffect(() => {
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
  }, [currentIndex]);

  // Get current screenshot
  const currentScreenshot = screenshots[currentIndex];

  // Get overlays for current screenshot (either from screenshot.overlays or generate from findings)
  const currentOverlays: HighlightOverlay[] = useMemo(() => {
    if (!currentScreenshot) return [];

    // If pre-calculated overlays exist, use them
    if (currentScreenshot.overlays) return currentScreenshot.overlays;

    // Otherwise generate from findings
    const findings = onFindings ? onFindings(currentIndex) : currentScreenshot.findings || [];
    return findings
      .filter((f) => f.bbox)
      .map((f) => ({
        findingId: f.id,
        bbox: f.bbox as [number, number, number, number],
        severity: f.severity,
        opacity: f.confidence * 0.3, // transparency based on confidence
      }));
  }, [currentScreenshot, currentIndex, onFindings]);

  // Count findings for each screenshot
  const findingCounts = useMemo(() => {
    return screenshots.map((ss, idx) => {
      const findings = onFindings ? onFindings(idx) : ss.findings || [];
      return findings.length;
    });
  }, [screenshots, onFindings]);

  // Navigation functions
  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? screenshots.length - 1 : prev - 1));
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === screenshots.length - 1 ? 0 : prev + 1));
  };

  const goToIndex = (idx: number) => {
    setCurrentIndex(idx);
  };

  // Zoom functions
  const zoomIn = () => {
    setZoom((prev) => Math.min(prev + 0.25, 3.0));
  };

  const zoomOut = () => {
    setZoom((prev) => Math.max(prev - 0.25, 0.5));
  };

  const resetZoom = () => {
    setZoom(1.0);
    setPan({ x: 0, y: 0 });
  };

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    e.preventDefault();
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case "ArrowLeft":
          goToPrevious();
          break;
        case "ArrowRight":
          goToNext();
          break;
        case "+":
        case "=":
          zoomIn();
          break;
        case "-":
        case "_":
          zoomOut();
          break;
        case "h":
        case "H":
          setShowOverlays((prev) => !prev);
          break;
        case "Escape":
          resetZoom();
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Finding tooltip state
  const [hoveredFinding, setHoveredFinding] = useState<Finding | null>(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  if (screenshots.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-[var(--v-text-tertiary)]">
        No screenshots available
      </div>
    );
  }

  // Get finding details for tooltip
  const getFinding = (findingId: string): Finding | undefined => {
    const findings = onFindings ? onFindings(currentIndex) : currentScreenshot?.findings || [];
    return findings.find((f) => f.id === findingId);
  };

  // Default dimensions if not provided
  const imageWidth = currentScreenshot?.width || 1920;
  const imageHeight = currentScreenshot?.height || 1080;

  return (
    <div className="flex flex-col gap-3">
      {/* Main carousel */}
      <div
        ref={containerRef}
        className="relative bg-black/50 rounded-lg overflow-hidden border border-white/10"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Navigation buttons */}
        {screenshots.length > 1 && (
          <>
            <button
              onClick={goToPrevious}
              className="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-black/60 hover:bg-black/80 text-white rounded-full p-2 transition-colors"
              title="Previous (←)"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={goToNext}
              className="absolute right-2 top-1/2 -translate-y-1/2 z-10 bg-black/60 hover:bg-black/80 text-white rounded-full p-2 transition-colors"
              title="Next (→)"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </>
        )}

        {/* Image container with zoom/pan */}
        <div
          className="relative w-full flex items-center justify-center min-h-[300px]"
          style={{ height: imageHeight > imageWidth ? "auto" : "400px" }}
        >
          <div
            className={`relative ${zoom > 1 ? "cursor-move" : "cursor-default"}`}
            style={{
              transform: `scale(${zoom}) translate(${pan.x}px, ${pan.y}px)`,
              transition: isDragging ? "none" : "transform 0.2s ease-out",
            }}
          >
            {/* Image */}
            {currentScreenshot?.data ? (
              <img
                src={`data:image/jpeg;base64,${currentScreenshot.data}`}
                alt={currentScreenshot.label}
                className="max-w-full max-h-[500px] object-contain"
                style={{ width: imageWidth > 0 ? `${imageWidth}px` : "auto" }}
                draggable={false}
              />
            ) : currentScreenshot?.url ? (
              <img
                src={currentScreenshot.url}
                alt={currentScreenshot.label}
                className="max-w-full max-h-[500px] object-contain"
                draggable={false}
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-center text-[var(--v-text-tertiary)] py-16">
                <div className="text-4xl mb-2">📸</div>
                <div className="text-sm">{currentScreenshot?.label || "Screenshot"}</div>
              </div>
            )}

            {/* SVG Overlay layer */}
            <AnimatePresence>
              {showOverlays && currentOverlays.length > 0 && (
                <svg
                  className="absolute inset-0 pointer-events-none"
                  width={imageWidth}
                  height={imageHeight}
                  viewBox={`0 0 ${imageWidth} ${imageHeight}`}
                  style={{ pointerEvents: zoom > 1 ? "none" : "auto" }}
                >
                  {currentOverlays.map((overlay) => {
                    const pixels = bboxToPixels(overlay.bbox, imageWidth, imageHeight);
                    const finding = getFinding(overlay.findingId);
                    return (
                      <g
                        key={overlay.findingId}
                        style={{ pointerEvents: "auto" }}
                        onMouseEnter={(e) => {
                          const rect = (e.target as SVGElement).getBoundingClientRect();
                          setTooltipPos({
                            x: rect.left + rect.width / 2,
                            y: rect.top - 10,
                          });
                          setHoveredFinding(finding || null);
                        }}
                        onMouseLeave={() => {
                          setHoveredFinding(null);
                        }}
                        onClick={() => {
                          if (onHighlightFinding && overlay.findingId) {
                            onHighlightFinding(overlay.findingId);
                          }
                        }}
                      >
                        {/* Highlight rectangle with fill */}
                        <rect
                          x={pixels.x}
                          y={pixels.y}
                          width={pixels.width}
                          height={pixels.height}
                          fill={SEVERITY_OVERLAY_COLOR[overlay.severity]}
                          stroke={SEVERITY_SOLID_COLOR[overlay.severity]}
                          strokeWidth={2}
                          opacity={overlay.opacity}
                          className="hover:opacity-100 transition-opacity cursor-pointer"
                          style={{ opacity: overlay.opacity }}
                        />
                      </g>
                    );
                  })}
                </svg>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Tooltip */}
        <AnimatePresence>
          {hoveredFinding && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="absolute z-20 pointer-events-none"
              style={{
                left: tooltipPos.x,
                top: tooltipPos.y,
                transform: "translate(-50%, -100%)",
              }}
            >
              <div className="bg-gray-900/95 border border-white/20 rounded-lg px-3 py-2 max-w-[300px]">
                <div className="text-xs font-semibold text-white mb-1">
                  {hoveredFinding.pattern_type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </div>
                <div className="text-[11px] text-gray-300">{hoveredFinding.description}</div>
                <div className="text-[10px] text-gray-400 mt-1">
                  Confidence: {Math.round(hoveredFinding.confidence * 100)}%
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Control bar */}
        <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between px-3 py-2 bg-black/70 backdrop-blur-sm">
          {/* Left controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowOverlays((prev) => !prev)}
              className="text-white/80 hover:text-white transition-colors"
              title="Toggle overlays (H)"
            >
              {showOverlays ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
            </button>
            <span className="text-[10px] text-white/60">{currentOverlays.length} findings</span>
          </div>

          {/* Center indicator */}
          <div className="text-xs font-medium text-white">
            {currentIndex + 1} / {screenshots.length}
          </div>

          {/* Right controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={zoomOut}
              className="text-white/80 hover:text-white transition-colors"
              title="Zoom out (-)"
              disabled={zoom <= 0.5}
            >
              <Minimize2 className="w-4 h-4" />
            </button>
            <span className="text-[10px] text-white/60 w-12 text-center">{Math.round(zoom * 100)}%</span>
            <button
              onClick={zoomIn}
              className="text-white/80 hover:text-white transition-colors"
              title="Zoom in (+)"
              disabled={zoom >= 3}
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            {zoom !== 1 && (
              <button
                onClick={resetZoom}
                className="text-[10px] text-cyan-400 hover:text-cyan-300 transition-colors ml-1"
                title="Reset (Esc)"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Thumbnail navigation strip */}
      {screenshots.length > 1 && (
        <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin">
          {screenshots.map((ss, idx) => (
            <motion.button
              key={idx}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: idx * 0.05 }}
              onClick={() => goToIndex(idx)}
              className={`flex-shrink-0 relative rounded-lg overflow-hidden border-2 transition-all ${
                idx === currentIndex
                  ? "border-cyan-500 ring-2 ring-cyan-500/30"
                  : "border-white/10 hover:border-cyan-500/50"
              }`}
              style={{ width: "80px", height: "60px" }}
              title={`${ss.label} (${findingCounts[idx]} findings)`}
            >
              {ss.data ? (
                <img
                  src={`data:image/jpeg;base64,${ss.data}`}
                  alt={ss.label}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full bg-white/5 flex items-center justify-center text-xs">
                  📸
                </div>
              )}
              {/* Finding count badge */}
              {findingCounts[idx] > 0 && (
                <div className="absolute top-1 right-1 bg-red-500/90 text-white text-[10px] font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {findingCounts[idx] > 9 ? "9+" : findingCounts[idx]}
                </div>
              )}
              {/* Selection indicator */}
              {idx === currentIndex && (
                <div className="absolute bottom-0 left-0 right-0 bg-cyan-500/50 h-0.5" />
              )}
            </motion.button>
          ))}
        </div>
      )}

      {/* Keyboard shortcuts hint */}
      <div className="text-[10px] text-[var(--v-text-tertiary)] text-center">
        Arrow keys to navigate • +/- to zoom • H to toggle overlays • Esc to reset
      </div>
    </div>
  );
}
