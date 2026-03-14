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
  return (
    <div className={`t-panel ${className}`}>
      <div className="t-panel-header">
        <span>[{title}]</span>
        {status && <span className="opacity-80">{status}</span>}
      </div>
      <PanelErrorBoundary>
        {/* We use flex-1 and hidden overflow so inner content can scroll if needed */}
        <div className="flex-1 overflow-hidden flex flex-col relative w-full h-full">
          {children}
        </div>
      </PanelErrorBoundary>
    </div>
  );
}

export function GhostPanel({ message = "AWAITING STREAM..." }: { message?: string }) {
  return (
    <div className="flex-1 flex items-center justify-center p-4">
      <span className="text-[var(--t-dim)] font-mono text-[10px] uppercase tracking-widest animate-pulse">
        [ {message} ]
      </span>
    </div>
  );
}
