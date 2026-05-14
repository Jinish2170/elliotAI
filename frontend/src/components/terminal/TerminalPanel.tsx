"use client";

import React from "react";

interface TerminalPanelProps {
  title: string;
  status?: string;
  children: React.ReactNode;
  className?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class PanelErrorBoundary extends React.Component<{ children: React.ReactNode }, ErrorBoundaryState> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex-1 flex items-center justify-center bg-[var(--t-panel)] border border-[var(--t-red)] p-4 text-center overflow-hidden">
          <div className="text-[var(--t-red)] font-mono text-xs">
            <span className="block mb-2">[MODULE_PANIC_ERR]</span>
            <span className="opacity-70">{this.state.error?.message || "Unknown rendering failure"}</span>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export function TerminalPanel({ title, status, children, className = "" }: TerminalPanelProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const baseClasses = "t-panel isolate";
  const layoutClasses = isExpanded 
    ? "fixed inset-4 z-[100] m-0 !h-[calc(100vh-2rem)] !w-[calc(100vw-2rem)] shadow-[0_0_50px_rgba(0,0,0,0.9)] border border-[var(--t-amber)] bg-[#050505]"
    : `relative ${className}`;

  return (
    <>
      {/* If expanded, optionally leave a placeholder block here to maintain layout flow if needed, though mostly optional if the grid scales without it */}
      {isExpanded && <div className={`t-panel ${className} relative opacity-10 border-dashed m-0 pointer-events-none`} />}
      
      <div className={`${baseClasses} ${layoutClasses}`}>
        <div className="t-panel-header z-10 flex justify-between items-center bg-[#0a0a0a]">
          <div className="flex gap-2 items-center">
            <span className="text-[var(--t-amber)] font-bold text-[11px] tracking-widest">[ {title} ]</span>
            {status && <span className="opacity-80 font-normal ml-2 text-[11px] uppercase">{status}</span>}
          </div>
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[var(--t-dim)] hover:text-[var(--t-text)] transition-colors text-[11px] px-1 font-mono hover:bg-white/10 rounded cursor-pointer"
            title={isExpanded ? "Collapse View" : "Expand View"}
          >
            {isExpanded ? "[ _ ]" : "[ + ]"}
          </button>
        </div>
        <PanelErrorBoundary>
          {/* We use flex-1 and hidden overflow so inner content can scroll if needed */}
          <div className="flex-1 overflow-auto flex flex-col relative w-full h-full p-2 bg-[#050505]/50 outline-none">
            {children}
          </div>
        </PanelErrorBoundary>
      </div>
    </>
  );
}

export function GhostPanel({ message = "AWAITING STREAM..." }: { message?: string }) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 overflow-hidden relative" style={{ minHeight: '100px' }}>
      <div className="relative z-10 w-full flex items-center justify-center">
        <span className="bg-black/80 px-2 py-1 text-[var(--t-amber)] font-mono text-[11px] uppercase tracking-widest border border-[var(--t-amber)]/20 shadow-[0_0_10px_rgba(255,170,0,0.1)]">
          <span className="animate-pulse mr-2">▶</span> {message}
        </span>
      </div>
    </div>
  );
}
