/* ========================================
   Veritas — Zustand Audit Store
   Global state for the live audit session
   ======================================== */

import type {
    AuditResult,
    AuditStats,
    Finding,
    LogEntry,
    Phase,
    PhaseState,
    Screenshot,
    SecurityResultItem,
} from "@/lib/types";
import { create } from "zustand";
import { EventSequencer, type SequencedEvent } from "@/hooks/useEventSequencer";

// Module-level event sequencer singleton (shared across store instances)
let eventSequencer: EventSequencer | null = null;

function getEventSequencer(): EventSequencer {
  if (!eventSequencer) {
    eventSequencer = new EventSequencer();
  }
  return eventSequencer;
}

interface AuditStore {
  // Connection
  auditId: string | null;
  url: string | null;
  tier: string;
  status: "idle" | "connecting" | "running" | "complete" | "error";

  // Phase tracking
  currentPhase: Phase | null;
  phases: Record<Phase, PhaseState>;
  pct: number;

  // Data
  findings: Finding[];
  screenshots: Screenshot[];
  stats: AuditStats;
  logs: LogEntry[];
  siteType: string | null;
  siteTypeConfidence: number;
  securityResults: SecurityResultItem[];
  result: AuditResult | null;
  error: string | null;

  // Actions
  setAudit: (id: string, url: string, tier: string) => void;
  setStatus: (s: AuditStore["status"]) => void;
  handleEvent: (event: Record<string, unknown>) => void;
  reset: () => void;
}

const initialPhases: Record<Phase, PhaseState> = {
  init: { status: "waiting", message: "", pct: 0 },
  scout: { status: "waiting", message: "", pct: 0 },
  security: { status: "waiting", message: "", pct: 0 },
  vision: { status: "waiting", message: "", pct: 0 },
  graph: { status: "waiting", message: "", pct: 0 },
  judge: { status: "waiting", message: "", pct: 0 },
};

const initialStats: AuditStats = {
  pages_scanned: 0,
  screenshots: 0,
  findings: 0,
  ai_calls: 0,
  security_checks: 0,
  elapsed_seconds: 0,
};

export const useAuditStore = create<AuditStore>((set, get) => ({
  auditId: null,
  url: null,
  tier: "standard_audit",
  status: "idle",
  currentPhase: null,
  phases: { ...initialPhases },
  pct: 0,
  findings: [],
  screenshots: [],
  stats: { ...initialStats },
  logs: [],
  siteType: null,
  siteTypeConfidence: 0,
  securityResults: [],
  result: null,
  error: null,

  setAudit: (id, url, tier) => set({ auditId: id, url, tier, status: "connecting" }),

  setStatus: (s) => set({ status: s }),

  reset: () => {
    getEventSequencer().reset();
    set({
      auditId: null,
      url: null,
      tier: "standard_audit",
      status: "idle",
      currentPhase: null,
      phases: { ...initialPhases },
      pct: 0,
      findings: [],
      screenshots: [],
      stats: { ...initialStats },
      logs: [],
      siteType: null,
      siteTypeConfidence: 0,
      securityResults: [],
      result: null,
      error: null,
    });
  },

  handleEvent: (event) => {
    const type = event.type as string;
    const sequence = event.sequence as number | undefined;

    // Event sequencer integration: buffer events with sequence numbers
    if (sequence !== undefined) {
      const sequencer = getEventSequencer();
      sequencer.addEvent({ sequence, type, data: event });

      // Process ready events in order
      const readyEvents = sequencer.getReadyEvents();
      for (const readyEvent of readyEvents) {
        processSingleEvent(readyEvent.type, readyEvent.data, set, get);
      }
    } else {
      // No sequence number, process immediately (backward compatibility)
      processSingleEvent(type, event, set, get);
    }
  },
}));

/**
 * Process a single event (internal helper used by handleEvent)
 * This function contains all the event handling logic
 */
function processSingleEvent(
  type: string,
  event: Record<string, unknown>,
  set: (partial: Partial<AuditStore>) => void,
  get: () => AuditStore
): void {
  const state = get();

  switch (type) {
    case "phase_start": {
      const phase = event.phase as Phase;
      set({
        status: "running",
        currentPhase: phase,
        pct: (event.pct as number) || state.pct,
        phases: {
          ...state.phases,
          [phase]: {
            status: "active",
            message: (event.message as string) || "",
            pct: (event.pct as number) || 0,
          },
        },
      });
      // Add log
      set({
        logs: [
          ...state.logs,
          {
            timestamp: new Date().toLocaleTimeString(),
            agent: (event.label as string) || phase,
            message: (event.message as string) || "",
            level: "info" as const,
          },
        ],
      });
      break;
    }

    case "phase_complete": {
      const phase = event.phase as Phase;
      set({
        pct: (event.pct as number) || state.pct,
        phases: {
          ...state.phases,
          [phase]: {
            status: "complete",
            message: (event.message as string) || "",
            pct: (event.pct as number) || 0,
            summary: (event.summary as Record<string, unknown>) || {},
          },
        },
      });
      break;
    }

    case "phase_error": {
      const phase = event.phase as Phase;
      set({
        phases: {
          ...state.phases,
          [phase]: {
            status: "error",
            message: (event.message as string) || "",
            pct: (event.pct as number) || 0,
            error: (event.error as string) || "",
          },
        },
      });
      break;
    }

    case "finding": {
      const f = event.finding as Finding;
      const updatedFindings = [...state.findings, f];

      // If finding has screenshot_index, update that screenshot's findings
      if (f.screenshot_index !== undefined) {
        const updatedScreenshots = state.screenshots.map((ss) => {
          if (ss.index === f.screenshot_index) {
            const existingFindings = ss.findings || [];
            return {
              ...ss,
              findings: [...existingFindings, f]
            };
          }
          return ss;
        });
        set({ findings: updatedFindings, screenshots: updatedScreenshots });
      } else {
        set({ findings: updatedFindings });
      }
      break;
    }

    case "screenshot": {
      const s: Screenshot = {
        url: event.url as string,
        label: event.label as string,
        index: event.index as number,
        data: event.data as string | undefined,
        width: (event.width as number) || undefined,
        height: (event.height as number) || undefined,
      };

      // Find findings associated with this screenshot
      const associatedFindings = state.findings.filter(
        (f) => f.screenshot_index === s.index
      );

      // Generate overlays from findings with bbox
      const overlays = associatedFindings
        .filter((f) => f.bbox)
        .map((f) => ({
          findingId: f.id,
          bbox: f.bbox as [number, number, number, number],
          severity: f.severity,
          opacity: f.confidence * 0.3,
        }));

      set({
        screenshots: [...state.screenshots, {
          ...s,
          findings: associatedFindings.length > 0 ? associatedFindings : undefined,
          overlays: overlays.length > 0 ? overlays : undefined
        }]
      });
      break;
    }

    case "stats_update": {
      set({ stats: event.stats as AuditStats });
      break;
    }

    case "log_entry": {
      const entry: LogEntry = {
        timestamp: (event.timestamp as string) || new Date().toLocaleTimeString(),
        agent: event.agent as string,
        message: event.message as string,
        level: (event.level as LogEntry["level"]) || "info",
        context: (event.context as LogEntry["context"]) || undefined,
        params: (event.params as Record<string, unknown>) || undefined,
      };
      set({ logs: [...state.logs, entry] });
      break;
    }

    case "site_type": {
      set({
        siteType: event.site_type as string,
        siteTypeConfidence: event.confidence as number,
      });
      break;
    }

    case "security_result": {
      set({
        securityResults: [
          ...state.securityResults,
          {
            module: event.module as string,
            result: event.result as Record<string, unknown>,
          },
        ],
      });
      break;
    }

    case "audit_result": {
      set({ result: event.result as AuditResult });
      break;
    }

    case "audit_complete": {
      set({ status: "complete" });
      break;
    }

    case "audit_error": {
      set({
        status: "error",
        error: (event.error as string) || "Unknown error",
      });
      break;
    }

    case "agent_personality": {
      // Handle agent personality events
      const agent = event.agent as Phase;
      const context = event.context as "working" | "complete" | "success" | "error";
      const params = (event.params as Record<string, unknown>) || {};

      // Update phase state message with personality message
      if (agent && agent !== "init") {
        set({
          phases: {
            ...state.phases,
            [agent]: {
              ...state.phases[agent],
              message: `Personality: ${context}`,
            },
          },
        });

        // Add personality log entry
        set({
          logs: [
            ...state.logs,
            {
              timestamp: new Date().toLocaleTimeString(),
              agent,
              message: `Personality: ${context}`,
              level: "info",
              context,
              params,
            },
          ],
        });
      }
      break;
    }

    // Vision pass events
    case "vision_pass_start": {
      const passNum = event.pass as number;
      set({
        phases: {
          ...state.phases,
          vision: {
            ...state.phases.vision,
            status: "active",
            activePass: passNum,
            message: (event.description as string) || `Starting Pass ${passNum}`,
          },
        },
      });
      break;
    }

    case "vision_pass_findings": {
      const findings = event.findings as Finding[];
      set({ findings: [...state.findings, ...findings] });
      break;
    }

    case "vision_pass_complete": {
      const passNum = event.pass as number;
      const currentCompletedPasses = (state.phases.vision?.completedPasses || []) as number[];
      set({
        phases: {
          ...state.phases,
          vision: {
            ...state.phases.vision,
            completedPasses: [...currentCompletedPasses, passNum],
            activePass: undefined,
            message: `Pass ${passNum} complete: ${event.findings_count} findings`,
          },
        },
      });
      break;
    }
  }
}
