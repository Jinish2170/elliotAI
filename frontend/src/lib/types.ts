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
}

export interface Screenshot {
  url: string;
  label: string;
  index: number;
  data?: string; // base64
}

export interface AuditStats {
  pages_scanned: number;
  screenshots: number;
  findings: number;
  ai_calls: number;
  security_checks: number;
  elapsed_seconds: number;
}

export interface LogEntry {
  timestamp: string;
  agent: string;
  message: string;
  level: "info" | "warn" | "error";
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
