"use client";

/* ========================================
   PanelChrome — Bloomberg-style Panel Wrapper
   Every panel in the War Room gets this chrome:
   - 28px title bar with ALL CAPS label
   - Optional item count badge
   - Optional minimize/maximize controls
   - Left accent stripe in contextual color
   ======================================== */

import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, Maximize2, Minimize2 } from "lucide-react";
import { useCallback, useState, type ReactNode } from "react";

export type ElevationTier = 1 | 2 | 3 | 4 | 5;

const ELEVATION_CLASSES: Record<ElevationTier, string> = {
  1: "bg-[#080A0F]",
  2: "bg-[rgba(10,15,30,0.85)] backdrop-blur-[4px] border border-[rgba(255,255,255,0.06)]",
  3: "bg-[rgba(15,20,40,0.9)] backdrop-blur-[8px] border border-[rgba(255,255,255,0.10)] shadow-[0_2px_8px_rgba(0,0,0,0.3)]",
  4: "bg-[rgba(20,25,50,0.95)] backdrop-blur-[16px] border border-[rgba(255,255,255,0.15)] shadow-[0_4px_16px_rgba(0,0,0,0.5)]",
  5: "bg-[rgba(8,10,20,0.98)] backdrop-blur-[24px] border-2 border-[var(--agent-primary,rgba(255,255,255,0.15))] shadow-[0_8px_32px_rgba(0,0,0,0.7)]",
};

interface PanelChromeProps {
  /** Panel title — rendered ALL CAPS in JetBrains Mono */
  title: string;
  /** Item count badge shown in title bar */
  count?: number;
  /** Left accent color — defaults to agent color via CSS var */
  accentColor?: string;
  /** Elevation tier (1-5) */
  elevation?: ElevationTier;
  /** Allow minimize/maximize */
  collapsible?: boolean;
  /** Start collapsed */
  defaultCollapsed?: boolean;
  /** Allow fullscreen expand */
  expandable?: boolean;
  /** Called when expand clicked */
  onExpand?: () => void;
  /** Additional className for the outer container */
  className?: string;
  /** Additional className for the content area */
  contentClassName?: string;
  /** Icon to show before title */
  icon?: ReactNode;
  /** Children — the panel content */
  children: ReactNode;
  /** Right-side slot in title bar (custom controls) */
  titleActions?: ReactNode;
}

export function PanelChrome({
  title,
  count,
  accentColor,
  elevation = 2,
  collapsible = false,
  defaultCollapsed = false,
  expandable = false,
  onExpand,
  className,
  contentClassName,
  icon,
  children,
  titleActions,
}: PanelChromeProps) {
  const [collapsed, setCollapsed] = useState(defaultCollapsed);

  const toggleCollapse = useCallback(() => {
    setCollapsed((prev) => !prev);
  }, []);

  const accentStyle = accentColor
    ? { backgroundColor: accentColor }
    : { backgroundColor: "var(--agent-primary, rgba(255,255,255,0.15))" };

  return (
    <div
      className={cn(
        "rounded-lg overflow-hidden flex flex-col",
        ELEVATION_CLASSES[elevation],
        className
      )}
    >
      {/* Title bar — 28px */}
      <div
        className="h-7 min-h-[28px] flex items-center gap-2 px-2 select-none"
        style={{ background: "rgba(5, 8, 18, 0.9)" }}
      >
        {/* Left accent stripe */}
        <div
          className="w-0.5 h-3.5 rounded-full shrink-0 transition-colors duration-300"
          style={accentStyle}
        />

        {/* Icon */}
        {icon && (
          <span className="shrink-0 text-[rgba(255,255,255,0.5)]">{icon}</span>
        )}

        {/* Title */}
        <span className="font-mono text-[10px] font-semibold tracking-[0.12em] text-[rgba(255,255,255,0.5)] uppercase truncate">
          {title}
        </span>

        {/* Count badge */}
        {count !== undefined && (
          <span className="font-mono text-[10px] text-[rgba(255,255,255,0.35)] shrink-0">
            [{count}]
          </span>
        )}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Title actions slot */}
        {titleActions}

        {/* Controls */}
        <div className="flex items-center gap-1">
          {collapsible && (
            <button
              onClick={toggleCollapse}
              className="p-0.5 rounded hover:bg-white/5 text-[rgba(255,255,255,0.3)] hover:text-[rgba(255,255,255,0.6)] transition-colors"
              aria-label={collapsed ? "Expand panel" : "Collapse panel"}
            >
              {collapsed ? (
                <ChevronDown className="w-3 h-3" />
              ) : (
                <ChevronUp className="w-3 h-3" />
              )}
            </button>
          )}
          {expandable && (
            <button
              onClick={onExpand}
              className="p-0.5 rounded hover:bg-white/5 text-[rgba(255,255,255,0.3)] hover:text-[rgba(255,255,255,0.6)] transition-colors"
              aria-label="Expand to fullscreen"
            >
              {collapsed ? (
                <Maximize2 className="w-3 h-3" />
              ) : (
                <Minimize2 className="w-3 h-3" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Content area */}
      <div
        className={cn(
          "transition-[max-height,opacity] duration-200 ease-out overflow-hidden",
          collapsed ? "max-h-0 opacity-0" : "max-h-[9999px] opacity-100",
          contentClassName
        )}
      >
        {children}
      </div>
    </div>
  );
}
