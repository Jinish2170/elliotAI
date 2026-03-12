"use client";

/* ========================================
   ChromaticProvider — Agent Color Atmosphere
   Wraps the audit page. Sets CSS custom properties on <body>
   to drive the full-viewport chromatic shift per active agent.
   ======================================== */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  type ReactNode,
} from "react";
import { AGENT_CONFIGS, type AgentId } from "@/config/agents";

interface ChromaticContextValue {
  activeAgent: AgentId | null;
  setActiveAgent: (agent: AgentId | null) => void;
}

const ChromaticContext = createContext<ChromaticContextValue>({
  activeAgent: null,
  setActiveAgent: () => {},
});

export function useChromatic() {
  return useContext(ChromaticContext);
}

const CSS_VARS = [
  "--agent-primary",
  "--agent-glow",
  "--agent-tint",
  "--agent-border",
  "--agent-text",
  "--agent-bg-subtle",
  "--agent-border-subtle",
] as const;

const TRANSITION_DURATION = 400; // ms — matches plan spec

function applyAgentVars(el: HTMLElement, agent: AgentId | null) {
  if (!agent) {
    // Reset to neutral (no active agent)
    el.style.setProperty("--agent-primary", "rgba(255,255,255,0.15)");
    el.style.setProperty("--agent-glow", "none");
    el.style.setProperty("--agent-tint", "none");
    el.style.setProperty("--agent-border", "rgba(255,255,255,0.06)");
    el.style.setProperty("--agent-text", "rgba(255,255,255,0.6)");
    el.style.setProperty("--agent-bg-subtle", "rgba(255,255,255,0.04)");
    el.style.setProperty("--agent-border-subtle", "rgba(255,255,255,0.08)");
    el.dataset.activeAgent = "";
    return;
  }

  const cfg = AGENT_CONFIGS[agent];
  el.style.setProperty("--agent-primary", cfg.color.primary);
  el.style.setProperty("--agent-glow", cfg.color.glow);
  el.style.setProperty("--agent-tint", cfg.color.tint);
  el.style.setProperty("--agent-border", cfg.color.border);
  el.style.setProperty("--agent-text", cfg.color.text);
  el.style.setProperty("--agent-bg-subtle", cfg.color.bgSubtle);
  el.style.setProperty("--agent-border-subtle", cfg.color.borderSubtle);
  el.dataset.activeAgent = agent;
}

interface ChromaticProviderProps {
  children: ReactNode;
  /** Initial agent (optional — can drive from store externally) */
  initialAgent?: AgentId | null;
}

export function ChromaticProvider({
  children,
  initialAgent = null,
}: ChromaticProviderProps) {
  const agentRef = useRef<AgentId | null>(initialAgent);
  const bodyRef = useRef<HTMLElement | null>(null);

  // On mount, grab <body> and apply initial vars
  useEffect(() => {
    bodyRef.current = document.body;

    // Set transition CSS for smooth chromatic shift
    const transitionProps = CSS_VARS.map((v) => `${v} ${TRANSITION_DURATION}ms cubic-bezier(0.4, 0, 0.2, 1)`).join(", ");
    bodyRef.current.style.transition = transitionProps;

    applyAgentVars(bodyRef.current, agentRef.current);

    return () => {
      // Cleanup on unmount — reset vars
      if (bodyRef.current) {
        CSS_VARS.forEach((v) => bodyRef.current!.style.removeProperty(v));
        bodyRef.current.style.transition = "";
        delete bodyRef.current.dataset.activeAgent;
      }
    };
  }, []);

  const setActiveAgent = useCallback((agent: AgentId | null) => {
    agentRef.current = agent;
    if (bodyRef.current) {
      applyAgentVars(bodyRef.current, agent);
    }
  }, []);

  // Sync with initialAgent prop changes (e.g., from Zustand store)
  useEffect(() => {
    if (initialAgent !== agentRef.current) {
      setActiveAgent(initialAgent);
    }
  }, [initialAgent, setActiveAgent]);

  return (
    <ChromaticContext.Provider value={{ activeAgent: agentRef.current, setActiveAgent }}>
      {/* Atmospheric overlay — the full-viewport tint */}
      <div
        className="chromatic-overlay pointer-events-none fixed inset-0 z-0"
        style={{
          background: "var(--agent-tint, none)",
          transition: `background ${TRANSITION_DURATION}ms cubic-bezier(0.4, 0, 0.2, 1)`,
        }}
        aria-hidden="true"
      />
      {children}
    </ChromaticContext.Provider>
  );
}
