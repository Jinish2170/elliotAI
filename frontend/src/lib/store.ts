/* ========================================
   Veritas — Zustand Audit Store
   Global state for the live audit session
   ======================================== */

import type {
    AuditResult,
    AuditStats,
    Finding,
    GreenFlag,
    LogEntry,
    Phase,
    PhaseState,
    Screenshot,
    SecurityResultItem,
    DarkPatternFinding,
    TemporalFinding,
    OSINTResult,
    MarketplaceThreatData,
    IOCIndicator,
    VisionPassSummary,
    DualVerdict,
    IOCDetectionResult,
    DarknetAnalysisResult,
    Tor2WebThreatData,
    CVEEntry,
    CVSSMetric,
    TechniqueMatch,
    ThreatAttribution,
    ExploitationAdvisory,
    AttackScenario,
    SecurityModuleResult,
    OWASPModuleResult,
    AgentPerformance,
    TaskMetric,
    KnowledgeGraph,
    GraphAnalysis,
    SiteClassification,
    BusinessEntity,
    ScoutResult,
    PageMetadata,
    VisionResult,
    GraphResult,
    SecurityResult,
    JudgeDecision,
    AuditEvidence,
    EntityClaim,
    VerificationResult,
    DomainIntel,
    GraphInconsistency,
    SecurityFindingDetailed,
    SecurityConfig,
    ConsensusResult,
    NavigationStartEvent,
    NavigationCompleteEvent,
    PageScannedEvent,
    ScrollEvent,
    ExplorationPath,
    CaptchaResult,
    FormDetection,
    APTGroupAttribution,
    TrustScoreResult,
    SubSignal,
    OverrideRule,
    SecuritySeverity,
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
  currentPhase: Phase | null;  // POPULATED via phase_start/phase_complete events
  phases: Record<Phase, PhaseState>;  // POPULATED via phase_start/phase_complete/phase_error
  pct: number;  // POPULATED via phase_start/phase_complete

  // Data
  findings: Finding[];  // POPULATED via finding and vision_pass_findings events
  screenshots: Screenshot[];  // POPULATED via screenshot events
  stats: AuditStats;  // POPULATED via stats_update and page_scanned events
  logs: LogEntry[];  // POPULATED via log_entry, phase_start, phase_complete, agent_personality
  siteType: string | null;  // POPULATED via site_type event
  siteTypeConfidence: number;  // POPULATED via site_type event
  securityResults: SecurityResultItem[];  // POPULATED via security_result event
  result: AuditResult | null;  // POPULATED via audit_result event
  error: string | null;  // POPULATED via audit_error event

  // Advanced Vision Data
  darkPatternFindings: DarkPatternFinding[];  // POPULATED via dark_pattern_finding event
  temporalFindings: TemporalFinding[];  // POPULATED via temporal_finding event
  visionPasses: VisionPassSummary[];  // POPULATED via vision_pass_complete event

  // Advanced OSINT Data
  osintResults: OSINTResult[];  // POPULATED via osint_result event
  marketplaceThreats: MarketplaceThreatData[];  // POPULATED via darknet_threat event
  iocIndicators: IOCIndicator[];  // POPULATED via ioc_indicator event
  iocDetection: IOCDetectionResult | null;  // POPULATED via ioc_detection_complete event

  // Advanced Judge Data
  dualVerdict: DualVerdict | null;  // POPULATED via verdict_technical/verdict_nontechnical/dual_verdict_complete

  // Premium Darknet Analysis Data
  darknetAnalysisResult: DarknetAnalysisResult | null;  // POPULATED via darknet_analysis_result event
  marketplaceDetails: MarketplaceThreatData[];  // POPULATED via marketplace_threat event
  tor2WebThreats: Tor2WebThreatData[];  // POPULATED via tor2web_anonymous_breach event

  // CVSS / CVE Technical Data
  cveEntries: CVEEntry[];  // POPULATED via cve_detected event
  cvssMetrics: CVSSMetric[];  // POPULATED via cvss_metrics/cvss_metric events
  cvssScore: number | null;  // POPULATED via cvss_metrics event

  // MITRE ATT&CK Data
  mitreTechniques: TechniqueMatch[];  // POPULATED via mitre_technique_mapped event
  threatAttribution: ThreatAttribution | null;  // POPULATED via threat_attribution event
  attackPatterns: string[];  // POPULATED via attack_pattern_detected event

  // Exploitation Advisory & Scenarios
  exploitationAdvisories: ExploitationAdvisory[];  // POPULATED via exploitation_advisory event
  attackScenarios: AttackScenario[];  // POPULATED via attack_scenario event

  // Security Module Results
  securityModuleResults: SecurityModuleResult[];  // POPULATED via security_module_result event
  owaspResults: OWASPModuleResult[];  // POPULATED via owasp_module_result event

  // Agent Performance Metrics
  agentPerformance: AgentPerformance[];  // POPULATED via agent_performance event
  taskMetrics: TaskMetric[];  // NOT YET WIRED — defined but no backend event sends this

  // Knowledge Graph Data
  knowledgeGraph: KnowledgeGraph | null;  // POPULATED via knowledge_graph event
  graphAnalysis: GraphAnalysis | null;  // POPULATED via graph_analysis event

  // Site Classification & Business Entity
  siteClassification: SiteClassification | null;  // POPULATED via site_classification event
  businessEntities: BusinessEntity[];  // NOT YET WIRED — no backend event sends this

  // Complete Agent Results
  scoutResult: ScoutResult | null;  // NOT YET WIRED — raw scout result not streamed directly
  pageMetadata: PageMetadata | null;  // NOT YET WIRED — extracted from audit_result if available
  complete_vision_result: VisionResult | null;  // NOT YET WIRED — full result not streamed
  complete_graph_result: GraphResult | null;  // NOT YET WIRED — full result not streamed
  complete_security_result: SecurityResult | null;  // NOT YET WIRED — full result not streamed

  // Judge Agent Data
  judge_decision: JudgeDecision | null;  // NOT YET WIRED — included in audit_result only
  audit_evidence: AuditEvidence | null;  // NOT YET WIRED — not currently streamed

  // Graph Investigation Data
  entityClaims: EntityClaim[];  // NOT YET WIRED — no backend event sends this directly
  verificationResults: VerificationResult[];  // NOT YET WIRED — included in audit_result only
  domainIntel: DomainIntel | null;  // NOT YET WIRED — included in audit_result.domain_info
  graphInconsistencies: GraphInconsistency[];  // NOT YET WIRED — included in audit_result only

  // Consensus Results
  consensusResults: ConsensusResult[];  // NOT YET WIRED — no backend event sends this

  // Scout Navigation Events
  navigationEvents: Array<NavigationStartEvent | NavigationCompleteEvent | PageScannedEvent | ScrollEvent>;  // POPULATED via navigation_start/complete/page_scanned/scroll_event
  explorationPath: ExplorationPath | null;  // POPULATED via exploration_path event
  captchaResults: CaptchaResult[];  // POPULATED via captcha_detected event
  formDetections: FormDetection[];  // POPULATED via form_detected event

  // APT Group Data
  aptGroupAttributions: APTGroupAttribution[];  // POPULATED via apt_group_attribution event

  // Trust Score Data
  trustScoreResult: TrustScoreResult | null;  // NOT YET WIRED — included in audit_result.judge_decision.trust_score_result

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

  // Advanced data initialization
  darkPatternFindings: [],
  temporalFindings: [],
  visionPasses: [],
  osintResults: [],
  marketplaceThreats: [],
  iocIndicators: [],
  iocDetection: null,
  dualVerdict: null,

  // Premium Darknet Analysis Data
  darknetAnalysisResult: null,
  marketplaceDetails: [],
  tor2WebThreats: [],

  // CVSS / CVE Technical Data
  cveEntries: [],
  cvssMetrics: [],
  cvssScore: null,

  // MITRE ATT&CK Data
  mitreTechniques: [],
  threatAttribution: null,
  attackPatterns: [],

  // Exploitation Advisory & Scenarios
  exploitationAdvisories: [],
  attackScenarios: [],

  // Security Module Results
  securityModuleResults: [],
  owaspResults: [],

  // Agent Performance Metrics
  agentPerformance: [],
  taskMetrics: [],

  // Knowledge Graph Data
  knowledgeGraph: null,
  graphAnalysis: null,

  // Site Classification & Business Entity
  siteClassification: null,
  businessEntities: [],

  // Complete Agent Results
  scoutResult: null,
  pageMetadata: null,
  complete_vision_result: null,
  complete_graph_result: null,
  complete_security_result: null,

  // Judge Agent Data
  judge_decision: null,
  audit_evidence: null,

  // Graph Investigation Data
  entityClaims: [],
  verificationResults: [],
  domainIntel: null,
  graphInconsistencies: [],

  // Consensus Results
  consensusResults: [],

  // Scout Navigation Events
  navigationEvents: [],
  explorationPath: null,
  captchaResults: [],
  formDetections: [],

  // APT Group Data
  aptGroupAttributions: [],

  // Trust Score Data
  trustScoreResult: null,

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
      // Reset advanced data
      darkPatternFindings: [],
      temporalFindings: [],
      visionPasses: [],
      osintResults: [],
      marketplaceThreats: [],
      iocIndicators: [],
      iocDetection: null,
      dualVerdict: null,
      // Reset premium data
      darknetAnalysisResult: null,
      marketplaceDetails: [],
      tor2WebThreats: [],
      cveEntries: [],
      cvssMetrics: [],
      cvssScore: null,
      mitreTechniques: [],
      threatAttribution: null,
      attackPatterns: [],
      exploitationAdvisories: [],
      attackScenarios: [],
      securityModuleResults: [],
      owaspResults: [],
      agentPerformance: [],
      taskMetrics: [],
      knowledgeGraph: null,
      graphAnalysis: null,
      siteClassification: null,
      businessEntities: [],
      // Reset complete agent results
      scoutResult: null,
      pageMetadata: null,
      complete_vision_result: null,
      complete_graph_result: null,
      complete_security_result: null,
      // Reset judge agent data
      judge_decision: null,
      audit_evidence: null,
      // Reset graph investigation data
      entityClaims: [],
      verificationResults: [],
      domainIntel: null,
      graphInconsistencies: [],
      // Reset consensus results
      consensusResults: [],
      // Reset navigation events
      navigationEvents: [],
      explorationPath: null,
      captchaResults: [],
      formDetections: [],
      // Reset APT group data
      aptGroupAttributions: [],
      // Reset trust score data
      trustScoreResult: null,
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
  const normalizeGreenFlags = (flags: unknown): GreenFlag[] => {
    if (!Array.isArray(flags)) return [];
    return flags.map((flag, index) => {
      if (typeof flag === "string") {
        return {
          id: `green-flag-${index}`,
          category: "trust",
          label: flag,
          icon: "✅",
        };
      }
      return flag as GreenFlag;
    });
  };
  const defaultTechnicalVerdict: DualVerdict["technical"] = {
    cwe_entries: [],
    cvss_metrics: [],
    cvss_base_score: 0,
    cvss_vector: "",
    iocs: [],
    threat_indicators: [],
    attack_techniques: [],
    exploitability: "LOW",
    impact: "LOW",
  };
  const defaultNonTechnicalVerdict: DualVerdict["non_technical"] = {
    risk_level: "suspicious",
    summary: "",
    key_findings: [],
    recommendations: [],
    warnings: [],
    green_flags: [],
    simple_explanation: "",
    what_to_do: [],
  };

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
      const summary = (event.summary as Record<string, unknown>) || {};
      
      // Attempt to extract live stats updates from phase completion summaries
      let updatedAiCalls = state.stats.ai_calls;
      let updatedSecChecks = state.stats.security_checks;
      
      if (phase === "vision" && typeof summary.nim_calls === "number") {
        updatedAiCalls = Math.max(state.stats.ai_calls, summary.nim_calls);
      }
      if (phase === "security" && Array.isArray(summary.modules)) {
        updatedSecChecks = Math.max(state.stats.security_checks, summary.modules.length);
      }
      
      let updatedVerdict = state.dualVerdict;
      if (phase === "judge" && typeof summary.trust_score === "number") {
        updatedVerdict = {
          ...state.dualVerdict,
          trust_score: summary.trust_score,
          risk_level: typeof summary.risk_level === "string" ? summary.risk_level : "unknown",
          confidence: "High",
          flags: [],
        } as AuditStore["dualVerdict"];
      }

      set({
        pct: (event.pct as number) || state.pct,
        dualVerdict: updatedVerdict,
        phases: {
          ...state.phases,
          [phase]: {
            status: "complete",
            message: (event.message as string) || "",
            pct: (event.pct as number) || 0,
            summary,
          },
        },
        stats: {
          ...state.stats,
          ai_calls: updatedAiCalls,
          security_checks: updatedSecChecks,
        }
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
        set({
          findings: updatedFindings,
          screenshots: updatedScreenshots,
          stats: { ...state.stats, findings: updatedFindings.length },
        });
      } else {
        set({
          findings: updatedFindings,
          stats: { ...state.stats, findings: updatedFindings.length },
        });
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

      const newScreenshots = [...state.screenshots, {
        ...s,
        findings: associatedFindings.length > 0 ? associatedFindings : undefined,
        overlays: overlays.length > 0 ? overlays : undefined
      }];
      set({
        screenshots: newScreenshots,
        stats: { ...state.stats, screenshots: newScreenshots.length },
      });
      break;
    }

    case "stats_update": {
      const stats = (event.stats as Record<string, unknown>) || {};
      set({
        stats: {
          pages_scanned: (stats.pages_scanned as number) || 0,
          screenshots: (stats.screenshots as number) || state.stats.screenshots,
          findings: (stats.findings as number) || (stats.findings_detected as number) || state.stats.findings,
          ai_calls: (stats.ai_calls as number) || state.stats.ai_calls,
          security_checks: (stats.security_checks as number) || state.stats.security_checks,
          elapsed_seconds: (stats.elapsed_seconds as number) || (stats.duration_seconds as number) || state.stats.elapsed_seconds,
        },
      });
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
      const result = event.result as AuditResult;
      set({
        result: {
          ...result,
          green_flags: normalizeGreenFlags(result.green_flags || []),
        } as AuditResult,
      });
      break;
    }

    case "green_flags": {
      const greenFlags = normalizeGreenFlags(event.green_flags || event.flags);
      // Update result with green flags
      if (state.result) {
        set({
          result: {
            ...state.result,
            green_flags: greenFlags,
          } as AuditResult,
        });
      }
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
      const merged = [...state.findings, ...findings];
      set({
        findings: merged,
        stats: { ...state.stats, findings: merged.length },
      });
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
        // Track vision pass summary
        visionPasses: [
          ...state.visionPasses,
          {
            pass_num: passNum,
            pass_name: (event.pass_name as string) || `Pass ${passNum}`,
            findings_count: event.findings_count as number,
            confidence: event.confidence as number,
            prompt_used: event.prompt_used as string | undefined,
            model_used: event.model_used as string | undefined,
          },
        ],
      });
      break;
    }

    // Advanced Vision Data Events
    case "dark_pattern_finding": {
      const raw = (event.finding || {}) as Record<string, unknown>;
      const finding: DarkPatternFinding = {
        category_id: (raw.category_id as string) || (raw.category as string) || "unknown",
        pattern_type: (raw.pattern_type as string) || "unknown",
        confidence: (raw.confidence as number) || 0,
        severity: ((raw.severity as DarkPatternFinding["severity"]) || "medium"),
        evidence: (raw.evidence as string) || (raw.description as string) || "",
        screenshot_path: (raw.screenshot_path as string) || "",
        raw_vlm_response: raw.raw_vlm_response as string | undefined,
        model_used: raw.model_used as string | undefined,
        fallback_mode: raw.fallback_mode as boolean | undefined,
      };
      set({ darkPatternFindings: [...state.darkPatternFindings, finding] });
      break;
    }

    case "temporal_finding": {
      const finding = event.finding as TemporalFinding;
      set({ temporalFindings: [...state.temporalFindings, finding] });
      break;
    }

    // Advanced OSINT Data Events
    case "osint_result": {
      const osintResult = event.result as OSINTResult;
      set({ osintResults: [...state.osintResults, osintResult] });
      break;
    }

    case "darknet_threat": {
      const threat = event.threat as MarketplaceThreatData;
      set({ marketplaceThreats: [...state.marketplaceThreats, threat] });
      break;
    }

    case "ioc_indicator": {
      const ioc = (event.indicator || event.ioc) as IOCIndicator;
      set({ iocIndicators: [...state.iocIndicators, ioc] });
      break;
    }

    case "ioc_detection_complete": {
      set({
        iocDetection: event.result as IOCDetectionResult,
      });
      break;
    }

    // Advanced Judge Data Events
    case "verdict_technical": {
      const verdict = (event.verdict || {}) as Record<string, unknown>;
      const existingVerdict = state.dualVerdict;
      set({
        dualVerdict: {
          ...(existingVerdict || {
            technical: defaultTechnicalVerdict,
            non_technical: defaultNonTechnicalVerdict,
            trust_score: 0,
            timestamp: new Date().toISOString(),
          }),
          technical: {
            ...defaultTechnicalVerdict,
            ...(verdict as unknown as Partial<DualVerdict["technical"]>),
            cvss_base_score:
              (verdict.cvss_base_score as number) ||
              (verdict.cvss_score as number) ||
              0,
            cvss_vector: (verdict.cvss_vector as string) || "",
          },
          trust_score: (verdict.trust_score as number) || existingVerdict?.trust_score || 0,
          timestamp: (event.timestamp as string) || existingVerdict?.timestamp || new Date().toISOString(),
        },
      });
      break;
    }

    case "verdict_nontechnical": {
      const verdict = (event.verdict || {}) as Record<string, unknown>;
      const existingVerdict = state.dualVerdict;
      set({
        dualVerdict: {
          ...(existingVerdict || {
            technical: defaultTechnicalVerdict,
            non_technical: defaultNonTechnicalVerdict,
            trust_score: 0,
            timestamp: new Date().toISOString(),
          }),
          non_technical: {
            ...defaultNonTechnicalVerdict,
            ...(verdict as unknown as Partial<DualVerdict["non_technical"]>),
            risk_level: (verdict.risk_level as DualVerdict["non_technical"]["risk_level"]) || "suspicious",
            summary: (verdict.summary as string) || "",
            key_findings: (verdict.key_findings as string[]) || [],
            recommendations: (verdict.recommendations as string[]) || (verdict.actionable_advice as string[]) || [],
            warnings: (verdict.warnings as string[]) || [],
            green_flags: normalizeGreenFlags(verdict.green_flags || []),
            simple_explanation: (verdict.simple_explanation as string) || (verdict.summary as string) || "",
            what_to_do: (verdict.actionable_advice as string[]) || [],
          },
          trust_score: existingVerdict?.trust_score || 0,
          timestamp: (event.timestamp as string) || existingVerdict?.timestamp || new Date().toISOString(),
        },
      });
      break;
    }

    case "dual_verdict_complete": {
      const payload = (event.dual_verdict || {}) as Record<string, unknown>;
      set({
        dualVerdict: {
          technical:
            ((payload.verdict_technical as DualVerdict["technical"] | undefined) || state.dualVerdict?.technical || defaultTechnicalVerdict),
          non_technical: {
            ...defaultNonTechnicalVerdict,
            ...((payload.verdict_nontechnical as Record<string, unknown>) || {}),
            green_flags: normalizeGreenFlags(((payload.verdict_nontechnical as Record<string, unknown> | undefined)?.green_flags) || []),
          },
          trust_score:
            (((payload.verdict_technical as Record<string, unknown> | undefined)?.trust_score) as number) ||
            state.dualVerdict?.trust_score ||
            0,
          timestamp:
            (((payload.metadata as Record<string, unknown> | undefined)?.timestamp) as string) ||
            state.dualVerdict?.timestamp ||
            new Date().toISOString(),
        },
      });
      break;
    }

    // ============================================================
    // Premium Darknet Events
    // ============================================================

    case "darknet_analysis_result": {
      set({
        darknetAnalysisResult: event.result as DarknetAnalysisResult,
      });
      break;
    }

    case "marketplace_threat": {
      const threat = event.threat as MarketplaceThreatData;
      set({
        marketplaceDetails: [...state.marketplaceDetails, threat],
      });
      break;
    }

    case "tor2web_anonymous_breach": {
      set({
        tor2WebThreats: [...state.tor2WebThreats, event.threat as Tor2WebThreatData],
      });
      break;
    }

    case "exit_scam_detected": {
      set({
        logs: [
          ...state.logs,
          {
            timestamp: new Date().toLocaleTimeString(),
            agent: "darknet",
            message: `⚠️ Exit scam detected: ${event.marketplace} (${event.shutdown_date})`,
            level: "error" as const,
            context: "error" as const,
            params: { marketplace: event.marketplace, shutdown_date: event.shutdown_date },
          },
        ],
      });
      break;
    }

    // ============================================================
    // CVSS / CVE Technical Events
    // ============================================================

    case "cvss_metrics": {
      set({
        cvssMetrics: event.metrics as CVSSMetric[],
        cvssScore: event.base_score as number,
      });
      break;
    }

    case "cve_detected": {
      set({
        cveEntries: [...state.cveEntries, event.cve as CVEEntry],
      });
      break;
    }

    // ============================================================
    // MITRE ATT&CK Events
    // ============================================================

    case "mitre_technique_mapped": {
      set({
        mitreTechniques: [...state.mitreTechniques, event.technique as TechniqueMatch],
      });
      break;
    }

    case "threat_attribution": {
      set({
        threatAttribution: event.attribution as ThreatAttribution,
      });
      break;
    }

    case "attack_pattern_detected": {
      set({
        attackPatterns: [...state.attackPatterns, event.pattern as string],
      });
      break;
    }

    // ============================================================
    // Exploitation & Scenario Events
    // ============================================================

    case "exploitation_advisory": {
      set({
        exploitationAdvisories: [...state.exploitationAdvisories, event.advisory as ExploitationAdvisory],
      });
      break;
    }

    case "attack_scenario": {
      set({
        attackScenarios: [...state.attackScenarios, event.scenario as AttackScenario],
      });
      break;
    }

    // ============================================================
    // Security Module Results Events
    // ============================================================

    case "security_module_result": {
      set({
        securityModuleResults: [...state.securityModuleResults, event.result as SecurityModuleResult],
      });
      break;
    }

    case "owasp_module_result": {
      set({
        owaspResults: [...state.owaspResults, event.result as OWASPModuleResult],
      });
      break;
    }

    case "agent_performance": {
      set({
        agentPerformance: [...state.agentPerformance, event.performance as AgentPerformance],
      });
      break;
    }

    // ============================================================
    // Knowledge Graph Events
    // ============================================================

    case "knowledge_graph": {
      set({
        knowledgeGraph: event.graph as KnowledgeGraph,
      });
      break;
    }

    case "graph_analysis": {
      set({
        graphAnalysis: event.analysis as GraphAnalysis,
      });
      break;
    }

    // ============================================================
    // Site Classification Events
    // ============================================================

    case "site_classification": {
      set({
        siteClassification: event.classification as SiteClassification,
      });
      break;
    }

    // ============================================================
    // Scout Agent Navigation & Detection Events
    // ============================================================

    case "cvss_metric": {
      const metric = event.metric as CVSSMetric;
      set({ cvssMetrics: [...state.cvssMetrics, metric] });
      break;
    }

    case "apt_group_attribution": {
      set({
        aptGroupAttributions: [...state.aptGroupAttributions, event as unknown as APTGroupAttribution],
      });
      break;
    }

    case "navigation_start": {
      const navigation = event as unknown as NavigationStartEvent;
      set({
        navigationEvents: [...state.navigationEvents, navigation],
        phases: {
          ...state.phases,
          scout: {
            ...state.phases.scout,
            status: "active",
            message: `Navigating to: ${navigation.url}`,
          },
        },
      });
      break;
    }

    case "navigation_complete": {
      const navigation = event as unknown as NavigationCompleteEvent;
      set({
        navigationEvents: [...state.navigationEvents, navigation],
        phases: {
          ...state.phases,
          scout: {
            ...state.phases.scout,
            message: `Navigation ${navigation.status}: ${navigation.duration_ms}ms`,
          },
        },
      });
      break;
    }

    case "page_scanned": {
      set({
        navigationEvents: [...state.navigationEvents, event as unknown as PageScannedEvent],
        stats: {
          ...state.stats,
          pages_scanned: (state.stats.pages_scanned || 0) + 1,
        },
      });
      break;
    }

    case "scroll_event": {
      const scrollEvent = event as unknown as ScrollEvent;
      set({
        navigationEvents: [...state.navigationEvents, scrollEvent],
        phases: {
          ...state.phases,
          scout: {
            ...state.phases.scout,
            message: `Scroll cycle ${scrollEvent.cycle}: lazy_load=${scrollEvent.has_lazy_load}, stabilized=${scrollEvent.stabilized}`,
          },
        },
      });
      break;
    }

    case "exploration_path": {
      const exploration = event as unknown as ExplorationPath;
      set({
        explorationPath: exploration,
        phases: {
          ...state.phases,
          scout: {
            ...state.phases.scout,
            message: `Explored ${exploration.total_pages} pages in ${exploration.total_time_ms}ms`,
          },
        },
      });
      break;
    }

    case "form_detected": {
      const formDetection = event as unknown as FormDetection;
      set({
        formDetections: [...state.formDetections, formDetection],
        phases: {
          ...state.phases,
          scout: {
            ...state.phases.scout,
            message: `${formDetection.count} form(s) detected`,
          },
        },
      });
      break;
    }

    case "captcha_detected": {
      const captcha = event as unknown as CaptchaResult;
      set({
        captchaResults: [...state.captchaResults, captcha],
        phases: {
          ...state.phases,
          scout: {
            ...state.phases.scout,
            message: captcha.detected
              ? `CAPTCHA detected: ${captcha.captcha_type || "unknown"} (${(captcha.confidence * 100).toFixed(0)}%)`
              : "No CAPTCHA detected",
          },
        },
      });
      break;
    }

    default: {
      // Unknown event type: log for debugging but don't throw
      if (process.env.NODE_ENV === "development") {
        console.debug(`[AuditStore] Unknown event type: ${type}`, event);
      }
      break;
    }
  }
}
