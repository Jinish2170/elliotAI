/* ========================================
   Veritas — TypeScript Type Definitions
   ======================================== */

export type Phase = "init" | "scout" | "security" | "vision" | "graph" | "judge";

export type PhaseStatus = "waiting" | "active" | "complete" | "error";

export interface PhaseState {
  status: PhaseStatus;
  message: string;
  pct: number;
  summary?: Record<string, unknown>;
  error?: string;
  // Vision phase specific
  activePass?: number;
  completedPasses?: number[];
}

export interface Finding {
  id: string;
  category: string;
  pattern_type: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  description: string;
  plain_english: string;
  screenshot_index?: number;
  bbox?: [number, number, number, number]; // x, y, width, height percentages (0-100)
}

export interface Screenshot {
  url: string;
  label: string;
  index: number;
  data?: string; // base64
  width?: number; // actual pixel width
  height?: number; // actual pixel height
  findings?: Finding[]; // findings associated with this screenshot
  overlays?: HighlightOverlay[]; // pre-calculated highlight overlays
}

export interface AuditStats {
  pages_scanned: number;
  screenshots: number;
  findings: number;
  ai_calls: number;
  security_checks: number;
  elapsed_seconds: number;
}

// ========================================
// Vision Agent Advanced Types
// ========================================

export interface DarkPatternFinding {
  category_id: string;         // e.g., "visual_interference"
  pattern_type: string;        // e.g., "misdirected_click"
  confidence: number;          // 0.0 to 1.0
  severity: "low" | "medium" | "high" | "critical";
  evidence: string;            // Description of what was found
  screenshot_path: string;     // Which screenshot
  raw_vlm_response?: string;   // Full VLM response for audit trail
  model_used?: string;         // Which model produced this finding
  fallback_mode?: boolean;     // True if not using primary NIM VLM
}

export interface TemporalFinding {
  finding_type: string;        // "fake_countdown", "fake_scarcity", "consistent"
  value_at_t0: string;         // Timer/counter value at first capture
  value_at_t_delay: string;    // Timer/counter value at second capture
  delta_seconds: number;       // Time between captures
  is_suspicious: boolean;      // True if deception detected
  explanation: string;         // Human-readable explanation
  confidence: number;          // 0.0 to 1.0
}

export interface VisionPassSummary {
  pass_num: number;
  pass_name: string;           // "full_page_scan", "element_interaction", etc.
  findings_count: number;
  confidence: number;
  prompt_used?: string;
  model_used?: string;
}

// ========================================
// Scout Agent Advanced Types
// ========================================

export interface ScrollState {
  cycle: number;
  has_lazy_load: boolean;
  last_scroll_y: number;
  last_scroll_height: number;
  cycles_without_content: number;
  stabilized: boolean;
}

export interface ScrollResult {
  total_cycles: number;
  stabilized: boolean;
  lazy_load_detected: boolean;
  screenshots_captured: number;
  scroll_states: ScrollState[];
}

export interface PageVisit {
  url: string;
  status: "SUCCESS" | "TIMEOUT" | "ERROR";
  screenshot_path?: string;
  page_title: string;
  navigation_time_ms: number;
  scroll_result?: ScrollResult;
}

export interface ExplorationResult {
  base_url: string;
  total_pages: number;
  total_time_ms: number;
  breadcrumbs: string[];
  pages_visited: PageVisit[];
  links_discovered: LinkInfo[];
}

export interface LinkInfo {
  url: string;
  text: string;
  location: "nav" | "footer" | "content";
  priority: number;         // Lower = higher priority
  depth: number;
}

// ========================================
// OSINT / Graph Investigator Advanced Types
// ========================================

export type OSINTCategory =
  | "dns"
  | "whois"
  | "ssl"
  | "threat_intel"
  | "reputation"
  | "social";

export type SourceStatus =
  | "success"
  | "error"
  | "timeout"
  | "rate_limited";

export interface OSINTResult {
  source: string;
  category: OSINTCategory;
  query_type: string;
  query_value: string;
  status: SourceStatus;
  data?: Record<string, unknown>;
  confidence_score: number;
  cached_at?: string;        // ISO datetime
  error_message?: string;
}

export type ExitRiskLevel =
  | "none"
  | "low"
  | "medium"
  | "high"
  | "critical";

export type DarknetMarketplaceType =
  | "marketplace"
  | "forum"
  | "exchange"
  | "hacking"
  | "carding"
  | "drugs"
  | "weapons"
  | "unknown";

export interface MarketplaceThreatData {
  marketplace_name: string;
  marketplace_type: DarknetMarketplaceType;
  onion_address: string;
  threat_level: ExitRiskLevel;
  confidence: number;
  description: string;
  indicators: string[];
  source: string;
}

// IOC (Indicators of Compromise) Types
export type IOCType =
  | "url"
  | "domain"
  | "ipv4"
  | "ipv6"
  | "email"
  | "md5"
  | "sha1"
  | "sha256"
  | "filename"
  | "onion";

export interface IOCIndicator {
  type: IOCType;
  value: string;
  confidence: number;
  source: string;
  context?: string;
}

export interface IOCDetectionResult {
  iocs: IOCIndicator[];
  threat_score: number;
  attack_patterns?: string[];  // MITRE ATT&CK techniques
}

// ========================================
// Judge Agent Dual-Verdict Types
// ========================================

export interface CWEEntry {
  cwe_id: string;            // e.g., "CWE-79"
  name: string;
  description: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
}

export interface CVSSMetric {
  name: string;
  value: string;
  severity: "NONE" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
}

export interface VerdictTechnical {
  cwe_entries: CWEEntry[];
  cvss_metrics: CVSSMetric[];
  cvss_base_score: number;
  cvss_vector: string;
  iocs: IOCIndicator[];
  threat_indicators: string[];
  attack_techniques: string[];  // MITRE ATT&CK
  exploitability: "NONE" | "LOW" | "HIGH";
  impact: "NONE" | "LOW" | "HIGH";
}

export interface VerdictNonTechnical {
  risk_level: "trusted" | "probably_safe" | "suspicious" | "high_risk" | "likely_fraudulent";
  summary: string;
  key_findings: string[];
  recommendations: string[];
  warnings: string[];
  green_flags: GreenFlag[];
  simple_explanation: string;
  what_to_do: string[];
}

export interface DualVerdict {
  technical: VerdictTechnical;
  non_technical: VerdictNonTechnical;
  trust_score: number;
  timestamp: string;
}

// ========================================
// Agent Theater Types
// ========================================

export interface AgentPersonality {
  agent: Phase;
  context: "working" | "complete" | "success" | "error";
  message: string;
  params?: Record<string, unknown>;
  animation?: string;
}

export interface LogEntry {
  timestamp: string;
  agent: string;
  message: string;
  level: "info" | "warn" | "error";
  context?: "working" | "complete" | "success" | "error"; // for personality context
  params?: Record<string, unknown>; // for message substitution
}
  timestamp: string;
  agent: string;
  message: string;
  level: "info" | "warn" | "error";
  context?: "working" | "complete" | "success" | "error"; // for personality context
  params?: Record<string, unknown>; // for message substitution
}

export interface SecurityResultItem {
  module: string;
  result: Record<string, unknown>;
}

export interface DomainInfo {
  age_days?: number | null;
  registrar?: string | null;
  country?: string | null;
  ip?: string | null;
  ssl_issuer?: string | null;
  inconsistencies?: string[];
  entity_verified?: boolean;
}

export interface AuditResult {
  url: string;
  status: string;
  audit_tier?: string;
  trust_score: number;
  risk_level: string;
  signal_scores: Record<string, number>;
  overrides: string[];
  narrative: string;
  recommendations: string[];
  findings: Finding[];
  dark_pattern_summary: Record<string, unknown>;
  security_results: Record<string, unknown>;
  site_type: string;
  site_type_confidence: number;
  domain_info: DomainInfo;
  pages_scanned: number;
  screenshots_count: number;
  elapsed_seconds: number;
  errors: string[];
  verdict_mode: string;
  green_flags?: GreenFlag[]; // list of positive indicators
}

export interface VisionPassStartEvent {
  type: 'vision_pass_start';
  pass: number;
  description: string;
  screenshots: number;
}

export interface VisionPassFindingsEvent {
  type: 'vision_pass_findings';
  pass: number;
  findings: Finding[];
  count: number;
  batch: boolean;
}

export interface VisionPassCompleteEvent {
  type: 'vision_pass_complete';
  pass: number;
  findings_count: number;
  confidence: number;
}

export interface AuditEvent {
  type: string;
  [key: string]: unknown;
}

// Phase metadata for the UI
export const PHASE_META: Record<Phase, { label: string; icon: string; description: string }> = {
  init: {
    label: "Initialization",
    icon: "⚙️",
    description: "Preparing the audit environment",
  },
  scout: {
    label: "Browser Reconnaissance",
    icon: "🔎",
    description: "Stealth browser agent visiting the website to capture evidence",
  },
  security: {
    label: "Security Audit",
    icon: "🛡️",
    description: "Analyzing security headers, checking phishing databases",
  },
  vision: {
    label: "Visual Intelligence",
    icon: "👁️",
    description: "AI vision analyzing screenshots for deceptive patterns",
  },
  graph: {
    label: "Intelligence Network",
    icon: "🌐",
    description: "Cross-referencing domain records, business registries",
  },
  judge: {
    label: "Forensic Judge",
    icon: "⚖️",
    description: "Weighing all evidence to compute final trust score",
  },
};

// Risk level colors
export const RISK_COLORS: Record<string, string> = {
  trusted: "#10B981",
  probably_safe: "#06B6D4",
  suspicious: "#F59E0B",
  high_risk: "#F97316",
  likely_fraudulent: "#EF4444",
};

export const RISK_LABELS: Record<string, string> = {
  trusted: "Trusted",
  probably_safe: "Probably Safe",
  suspicious: "Suspicious",
  high_risk: "High Risk",
  likely_fraudulent: "Likely Fraudulent",
};

// ========================================
// Screenshot Carousel Types (Plan 11-02)
// ========================================

export interface HighlightOverlay {
  findingId: string;
  bbox: [number, number, number, number]; // x, y, width, height percentages
  severity: Finding["severity"];
  opacity: number; // 0.0-1.0, based on confidence
}

// Bounding box to pixel conversion utility
export function bboxToPixels(
  bbox: [number, number, number, number],
  imageWidth: number,
  imageHeight: number
): { x: number; y: number; width: number; height: number } {
  return {
    x: (bbox[0] / 100) * imageWidth,
    y: (bbox[1] / 100) * imageHeight,
    width: (bbox[2] / 100) * imageWidth,
    height: (bbox[3] / 100) * imageHeight,
  };
}

// Severity to overlay color mapping
export const SEVERITY_OVERLAY_COLOR: Record<Finding["severity"], string> = {
  critical: "rgba(239, 68, 68, 0.3)", // red-500 with opacity
  high: "rgba(249, 115, 22, 0.3)", // orange-500
  medium: "rgba(245, 158, 11, 0.3)", // amber-500
  low: "rgba(34, 197, 94, 0.3)", // green-500
};

// Severity to solid color for stroke
export const SEVERITY_SOLID_COLOR: Record<Finding["severity"], string> = {
  critical: "rgba(239, 68, 68, 0.8)",
  high: "rgba(249, 115, 22, 0.8)",
  medium: "rgba(245, 158, 11, 0.8)",
  low: "rgba(34, 197, 94, 0.8)",
};

// ========================================
// Green Flag Types (Plan 11-03)
// ========================================

export interface GreenFlag {
  id: string;
  category: "security" | "privacy" | "compliance" | "trust";
  label: string; // human-readable description
  icon: string; // emoji icon
}

// Common green flags for positive audits
export const COMMON_GREEN_FLAGS: GreenFlag[] = [
  { id: "ssl-valid", category: "security", label: "Valid SSL Certificate", icon: "🔒" },
  { id: "https-enforced", category: "security", label: "HTTPS Enforced", icon: "🛡️" },
  { id: "contact-visible", category: "trust", label: "Contact Information Visible", icon: "📞" },
  { id: "privacy-policy", category: "privacy", label: "Privacy Policy Found", icon: "📄" },
  { id: "terms-of-service", category: "compliance", label: "Terms of Service Found", icon: "⚖️" },
  { id: "no-dark-patterns", category: "trust", label: "No Dark Patterns Detected", icon: "✨" },
  { id: "valid-domain-age", category: "trust", label: "Valid Domain Age", icon: "📅" },
];

// Relative time formatting utility
export function formatRelativeTime(timestamp: string): string {
  const now = Date.now();
  const then = new Date(timestamp).getTime();
  const diff = now - then;

  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (seconds < 60) return `${seconds}s ago`;
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return new Date(timestamp).toLocaleDateString();
}
