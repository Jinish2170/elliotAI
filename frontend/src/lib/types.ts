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
  status: "SUCCESS" | "CAPTCHA_BLOCKED" | "TIMEOUT" | "ERROR";
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

export type RiskLevel =
  | "trusted"
  | "probably_safe"
  | "suspicious"
  | "high_risk"
  | "likely_fraudulent"
  | "dangerous";

export type SecuritySeverity =
  | "LOW"
  | "MEDIUM"
  | "HIGH"
  | "CRITICAL"
  | "INFO";

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

  // Additional premium fields
  product_categories?: string[];
  risk_factors?: string[];
  shutdown_date?: string;        // For exit scams
  exit_scam_status?: boolean;
  anonymity_breach?: string;    // e.g. "high"
}

export interface DarknetAnalysisResult {
  has_onion_references: boolean;
  onion_urls_detected: string[];
  marketplace_threats: MarketplaceThreatData[];
  tor2web_exposure: boolean;
  darknet_risk_score: number;      // 0.0 to 1.0
  recommendations: string[];
  threat_level?: ExitRiskLevel;

  // Premium: Intelligence detail
  onion_validated?: boolean;
  marketplace_verified?: boolean;
  attack_patterns?: string[];     // MITRE techniques
  cve_associated?: string[];     // CVE IDs
}

export interface Tor2WebThreatData {
  gateway_domains: string[];
  de_anon_risk: ExitRiskLevel;
  referrer_leaks?: boolean;
  recommendation: string;
  anonymity_breach?: string;
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
  detection_count?: number;  // Number of sources confirming
}

export interface IOCDetectionResult {
  iocs: IOCIndicator[];
  threat_score: number;
  attack_patterns?: string[];  // MITRE techniques
  attribution?: ThreatAttribution;
}

export interface ThreatAttribution {
  threat_actor: string;
  attack_pattern: string;
  attack_tactic: string;
  technique_id?: string;
  confidence: number;
  explanation: string;
  all_techniques?: TechniqueMatch[];
}

// ========================================
// Premium Darknet Feature Types
// ========================================

export interface DarknetMarketplaceDetail {
  marketplace_name: string;
  marketplace_short_name: string;  // e.g., "Empire", "Alpha"
  status: "active" | "exit_scam" | "shutdown" | "unknown";
  exit_scam_date?: string;
  shutdown_date?: string;
  threat_score: number;          // 0.0-1.0
  active_since?: string;
  vendor_affected_count?: number;
  funds_stolen_estimate?: string;  // "millions in BTC", etc.
}

export interface MarketplaceListing {
  listing_id: string;
  marketplace: string;
  threat_type: "phishing_kit" | "credential_database" | "credit_card_dumps" |
                  "identity_theft" | "bank_account" | "crypto_wallet";
  title: string;
  price?: string;
  price_crypto?: string;
  seller_reputation?: number;
  date_posted?: string;
  description?: string;
  evidence_tokens?: string[];
  confidence: number;
}

// ========================================
// CVE / CVSS Types
// ========================================

export type CWMetricStatus =
  | "X"   // Not Defined
  | "N"   // Network / None
  | "A"   // Adjacent
  | "L"   // Local / Low (context-dependent)
  | "P"   // Physical
  | "H"   // High
  | "M"   // Medium
  | "R"   // Required
  | "C"   // Changed
  | "U"   // Unchanged;

export interface CVSSMetrics {
  attack_vector: CWMetricStatus;
  attack_complexity: CWMetricStatus;
  privileges_required: CWMetricStatus;
  user_interaction: CWMetricStatus;
  scope: CWMetricStatus;
  confidentiality: CWMetricStatus;
  integrity: CWMetricStatus;
  availability: CWMetricStatus;
}

export interface CVEEntry {
  cve_id: string;            // e.g., "CVE-2024-34351"
  name: string;
  description: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  cwe_id?: string;          // CWE identifier
  cvss_score?: number;       // 0.0-10.0
  cvss_vector?: string;     // e.g., "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N"
  attack_vector?: "N" | "A" | "L" | "P";
  exploitability?: "NONE" | "LOW" | "HIGH";
  impact?: string;           // Plain text impact description
  patch_available?: boolean;
  technical_notes?: string[];
  affected_components?: string[];
  references?: string[];
}

// ========================================
// MITRE ATT&CK Framework Types
// ========================================

export type MITRETactic =
  | "initial_access"
  | "execution"
  | "persistence"
  | "privilege_escalation"
  | "defense_evasion"
  | "credential_access"
  | "discovery"
  | "lateral_movement"
  | "collection"
  | "exfiltration"
  | "command_and_control"
  | "impact";

export interface MITRETechnique {
  technique_id: string;      // e.g., "T1566.001"
  technique_name: string;
  tactic: MITRETactic;
  description: string;
  detection_markers: string[];  // Keywords/patterns
  matched_markers?: string[];   // Which markers matched
  confidence?: number;         // 0.0 to 1.0
}

export interface TechniqueMatch {
  technique_id: string;
  technique_name: string;
  tactic: string;
  confidence: number;          // 0.0 to 1.0
  matched_markers: string[];
}

// ========================================
// Exploitation & Scenario Types
// ========================================

export interface ExploitationAdvisory {
  cve: string;
  title: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  priority: "IMMEDIATE" | "URGENT" | "SCHEDULED";
  remediation: string;
  advisory_note: string;
  affected_components?: string[];
  attack_vector_description?: string;
  exploit_complexity?: string;
}

export interface AttackScenarioStep {
  step_number: number;
  description: string;
  technique_used?: string;  // MITRE technique ID
  expected_outcome: string;
  prerequisites?: string[];
  tools_required?: string[];
}

export interface AttackScenario {
  cve?: string;
  title: string;
  attack_flow: AttackScenarioStep[];
  potential_impact: string;
  technique_id?: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  estimated_complexity?: "LOW" | "MEDIUM" | "HIGH";
  actor_groups?: string[];     // Threat actors using this
  required_privileges?: string[];
}

// ========================================
// Premium Category System
// ========================================

export interface PremiumDarknetCategory {
  id: string;
  name: string;
  tier: "standard" | "premium" | "darknet_premium";
  requires_tor: boolean;
  description: string;
  price_usd?: number;        // For premium features
  features: string[];        // What this tier includes
}

export const DARKNET_CATEGORIES: PremiumDarknetCategory[] = [
  {
    id: "onion_detection",
    name: "Onion Address Detection",
    tier: "standard",
    requires_tor: false,
    description: "Detect .onion URLs in site content",
    features: ["Pattern detection", "Address validation", "Onion URL extraction"],
  },
  {
    id: "marketplace_monitoring",
    name: "Darknet Marketplace Monitoring",
    tier: "premium",
    requires_tor: false,
    description: "Monitor 6 major marketplaces for mentions",
    features: ["AlphaBay", "Empire", "Hansa", "Dream", "WallStreet", "Alpha2", "Marketplace threat tracking"],
    price_usd: 99,
  },
  {
    id: "credential_leak_check",
    name: "Credential Leak Database Check",
    tier: "premium",
    requires_tor: false,
    description: "Check leaked credential databases",
    features: ["Breach compilation", "Username search", "Password hash matching", "Compromised credential notifications"],
    price_usd: 149,
  },
  {
    id: "phishing_kit_detection",
    name: "Phishing Kit Database",
    tier: "darknet_premium",
    requires_tor: true,
    description: "Access hidden phishing kit database via TOR",
    features: ["Kit fingerprinting", "Operator tracking", "Campaign detection", "Active kit monitoring"],
    price_usd: 499,
  },
  {
    id: "exit_scam_tracking",
    name: "Exit Scam Database",
    tier: "darknet_premium",
    requires_tor: true,
    description: "Real-time exit scam tracking",
    features: ["Exit scam alerts", "Vendor compensation tracking", "Shutdown notifications", "Risk scoring"],
    price_usd: 599,
  },
  {
    id: "attribution_engine",
    name: "Threat Attribution Engine",
    tier: "darknet_premium",
    requires_tor: true,
    description: "Advanced threat actor attribution",
    features: ["APT group mapping", "Technique correlation", "Actor identification", "Attribution confidence scoring"],
    price_usd: 999,
  },
];

// ========================================
// Security Module Result Types
// ========================================

export interface OWASPModuleResult {
  owasp_id: string;          // e.g., "A01", "A02"
  owasp_name: string;        // e.g., "Broken Access Control"
  cwe_id?: string;           // Associated CWE
  findings_count: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  details: Record<string, unknown>;
  remediation?: string;
}

export interface SecurityFinding {
  id: string;
  category: string;
  pattern_type: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  confidence: number;
  description: string;
  plain_english: string;
  screenshot_index?: number;
  bbox?: [number, number, number, number];
}

export interface SecurityModuleResult {
  module_name: string;     // e.g., "security_headers", "tls_ssl_analysis"
  category: string;          // "owasp", "gdpr", "pci_dss", "darknet", etc.
  findings_count: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  composite_score: number;
  execution_time_ms: number;
  findings: SecurityFinding[];
  details: Record<string, unknown>;
  recommendations?: string[];
}

// ========================================
// Agent Process Performance Types
// ========================================

export interface AgentPerformance {
  agent: Phase;
  tasks_completed: number;
  tasks_total: number;
  accuracy: number;          // 0-100
  processing_time_ms: number;
  finding_rate: number;       // findings per second
  memory_usage_mb?: number;
  cache_hit_rate?: number;   // For NIM cache
  ai_calls_made?: number;      // NIM call count
  fallback_used?: boolean;     // Used fallback AI
}

export interface TaskMetric {
  task_id: string;
  task_name: string;
  agent: Phase;
  start_time: string;         // ISO datetime
  end_time: string;           // ISO datetime
  duration_ms: number;
  success: boolean;
  error_message?: string;
  resources_used?: string[];  // "NIM", "cache", "fallback", etc.
  confidence?: number;
}

// ========================================
// Knowledge Graph Types
// ========================================

export interface KnowledgeGraphNode {
  id: string;
  node_type: "domain" | "entity" | "osint_source" | "darknet_threat" | "ioc" | "attribute";
  attributes: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship_type: string;
  weight: number;            // Edge weight for importance
  confidence: number;         // 0.0-1.0
  timestamp?: string;
}

export interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  edges: GraphEdge[];
  node_count?: number;
  edge_count?: number;
  graph_density?: number;     // Sparsity metric
  avg_clustering?: number;   // Community clustering
  largest_component_size?: number;
  isolated_nodes?: number;
}

export interface GraphAnalysis {
  graph_sparsity: number;
  avg_clustering: number;
  strongly_connected?: boolean;
  shortest_path_to_darknet?: number;
  osint_clusters?: OSINTCluster[];
  centrality_scores?: NodeCentrality[];
}

export interface OSINTCluster {
  source: string;
  connected_entities: string[];
  cluster_strength: number;
  confidence?: number;
}

export interface NodeCentrality {
  node_id: string;
  degree_centrality: number;
  eigenvector_centrality: number;
  betweenness_centrality: number;
  page_rank?: number;
}

// ========================================
// Site Classification Types
// ========================================

export interface SiteClassification {
  site_type: string;         // e.g., "ecommerce", "news", "gaming", "financial"
  site_type_confidence: number; // 0.0-1.0
  primary_signals: Record<string, number>;
  additional_signals: string[];
  content_categories: string[];
  detected_technologies: string[];
  risk_indicators: string[];
  green_flags: string[];
}

export interface BusinessEntity {
  entity_id: string;
  entity_name: string;
  entity_type: "company" | "organization" | "brand" | "individual";
  verification_status: "verified" | "unverified" | "conflicted";
  confidence: number;
  sources_supporting: string[];
  verification_links: string[];
  registration_info?: {
    business_number?: string;
    incorporation_date?: string;
    jurisdiction?: string;
  };
  contact_info?: {
    phone?: string;
    email?: string;
    address?: string;
    social_profiles?: string[];
  };
}

// ========================================
// Scan Configuration Types
// ========================================

export interface AuditConfiguration {
  audit_id: string;
  url: string;
  tier: "quick_scan" | "standard_audit" | "deep_forensic" | "darknet_investigation";
  verdict_mode: "simple" | "expert";
  premium_features: PremiumFeatureConfig;
  security_modules: SecurityModuleConfig;
  vision_config: VisionConfig;
  osint_config: OSINTConfig;
  graph_config: GraphConfig;
}

export interface PremiumFeatureConfig {
  darknet_enabled: boolean;
  darknet_category: string;     // Which premium category
  phishing_kit_scan: boolean;
  exit_scan_monitoring: boolean;
  tor_access: boolean;           // Whether to use TOR for darknet checks
  attribution_engine: boolean;
  threat_feed_correlation: boolean;
  advanced_ioc_analysis: boolean;
}

export interface VisionConfig {
  passes: number;             // 1-5
  multi_pass_enabled: boolean;
  ssim_enabled: boolean;
  confidence_threshold: number;
  model_fallback: boolean;
  capture_temporal: boolean;
}

export interface OSINTConfig {
  sources_enabled: string[];    // Which OSINT sources to use
  timeout_per_source: number;  // seconds
  max_parallel_sources: number;
  cache_enabled: boolean;
  darknet_sources: string[];    // Which darknet sources
}

export interface GraphConfig {
  build_knowledge_graph: boolean;
  calculate_centrality: boolean;
  detect_communities: boolean;
  max_depth: number;
  max_nodes: number;
}

export interface SecurityModuleConfig {
  enabled_modules: string[];
  timeout_per_module: number;
  include_owasp_modules: boolean;
  include_gdpr_checks: boolean;
  include_pci_dss: boolean;
  darknet_level: "none" | "basic" | "advanced" | "premium";
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
  risk_level: "trusted" | "probably_safe" | "suspicious" | "high_risk" | "likely_fraudulent" | "dangerous";
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
  // TODO: Wire from backend — these fields exist in judge_decision but are not currently forwarded to audit_result event
  dual_verdict?: DualVerdict;
  trust_score_result?: TrustScoreResult;
  judge_decision?: JudgeDecision;
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

// ========================================
// Additional Backend Agent Result Types
// ========================================

// Scout Agent Types
export interface PageMetadata {
  title: string;
  description: string;
  keywords: string[];
  og_tags: Record<string, string>;
  canonical_url: string;
  language: string;
  scripts_count: number;
  external_scripts: string[];
  forms: Record<string, unknown>[];
  links_internal: string[];
  links_external: string[];
  images_count: number;
  has_ssl: boolean;
  cookies_count: number;
}

export interface ScoutResult {
  url: string;
  status: "SUCCESS" | "CAPTCHA_BLOCKED" | "TIMEOUT" | "ERROR";
  screenshots: string[];
  screenshot_timestamps: number[];
  screenshot_labels: string[];
  page_title: string;
  page_metadata: PageMetadata;
  links: string[];
  forms_detected: number;
  captcha_detected: boolean;
  ioc_detected: boolean;
  ioc_indicators: Record<string, unknown>[];
  onion_detected: boolean;
  onion_addresses: string[];
  error_message: string;
  navigation_time_ms: number;
  viewport_used: string;
  user_agent_used: string;
  trust_modifier: number;
  trust_notes: string[];
  site_type: string;
  site_type_confidence: number;
  dom_analysis: Record<string, unknown>;
  form_validation: Record<string, unknown>;
  scroll_result?: ScrollResult;
  end_time?: string;
}

// Vision Agent Types
export interface VisionResult {
  dark_patterns: DarkPatternFinding[];
  temporal_findings: TemporalFinding[];
  visual_score: number;
  temporal_score: number;
  screenshots_analyzed: number;
  prompts_sent: number;
  nim_calls_made: number;
  cache_hits: number;
  fallback_used: boolean;
  errors: string[];
  end_time?: string;
}

// Graph/OSINT Types
export interface EntityClaim {
  id: string;
  entity_type: "company" | "person" | "address" | "phone" | "email" | "founding_date";
  entity_value: string;
  source_page: string;
  context: string;
}

export interface VerificationResult {
  id: string;
  claim: EntityClaim;
  status: "confirmed" | "denied" | "contradicted" | "unverifiable";
  evidence_source: string;
  evidence_detail: string;
  confidence: number;
  timestamp: string;
}

export interface DomainIntel {
  id: string;
  domain: string;
  registrar: string;
  creation_date: string | null;
  expiration_date: string | null;
  age_days: number;
  registrant_country: string;
  registrant_org: string;
  name_servers: string[];
  ip_address: string;
  ip_country: string;
  ssl_issuer: string;
  is_privacy_protected: boolean;
  raw_whois: string;
  errors: string[];
}

export interface GraphInconsistency {
  id: string;
  claim_text: string;
  evidence_text: string;
  inconsistency_type: string;
  severity: "low" | "medium" | "high" | "critical";
  confidence: number;
  explanation: string;
}

export interface GraphResult {
  id: string;
  url: string;
  domain_intel: DomainIntel | null;
  claims_extracted: EntityClaim[];
  verifications: VerificationResult[];
  inconsistencies: GraphInconsistency[];
  graph: Record<string, unknown> | null;
  graph_node_count: number;
  graph_edge_count: number;
  graph_score: number;
  meta_score: number;
  meta_analysis: Record<string, unknown>;
  ip_geolocation: Record<string, string | number>;
  tavily_searches: number;
  errors: string[];
  osint_sources: Record<string, OSINTResult>;
  osint_consensus: Record<string, unknown>;
  osint_indicators: unknown[];
  cti_techniques: MITRETechnique[];
  threat_attribution: ThreatAttribution;
  threat_level: ExitRiskLevel;
  osint_confidence: number;
  end_time?: string;
}

// Security Agent Types
export interface SecurityConfig {
  timeout: number;
  retry_count: number;
  fail_fast: boolean;
}

export interface SecurityFindingDetailed extends Omit<SecurityFinding, "id"> {
  id?: string;
  source_module: string;
  timestamp: string;
  cvss_score?: number;
  recommendation: string;
  url_finding: boolean;
}

export interface SecurityResult {
  id: string;
  url: string;
  audit_id: string | null;
  timestamp: string;
  composite_score: number;
  findings: SecurityFindingDetailed[];
  modules_results: Record<string, unknown>;
  modules_run: string[];
  modules_failed: string[];
  modules_executed: number;
  errors: string[];
  analysis_time_ms: number;
  darknet_correlation: Record<string, unknown> | null;
  end_time?: string;
}

// Quality Foundation Types
export interface FindingSource {
  id: string;
  agent_type: "vision" | "osint" | "security";
  finding_id: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
  confidence: number;
  timestamp: string;
}

export interface ConsensusResult {
  finding_key: string;
  sources: FindingSource[];
  status: "UNCONFIRMED" | "CONFIRMED" | "CONFLICTED" | "PENDING";
  aggregated_confidence: number;
  conflict_notes: string[];
  confidence_breakdown: Record<string, number>;
}

// Scout Navigation Events
export interface NavigationStartEvent {
  type: "navigation_start";
  url: string;
  timestamp: string;
}

export interface NavigationCompleteEvent {
  type: "navigation_complete";
  url: string;
  status: "SUCCESS" | "CAPTCHA_BLOCKED" | "TIMEOUT" | "ERROR";
  duration_ms: number;
  screenshots_count: number;
  timestamp: string;
}

export interface PageScannedEvent {
  type: "page_scanned";
  url: string;
  page_title: string;
  navigation_time_ms: number;
  timestamp: string;
}

export interface ScrollEvent {
  type: "scroll_event";
  cycle: number;
  has_lazy_load: boolean;
  last_scroll_y: number;
  scroll_height: number;
  stabilized: boolean;
  screenshot_count: number;
}

export interface ExplorationPath {
  type: "exploration_path";
  base_url: string;
  visited_urls: string[];
  breadcrumbs: string[];
  total_pages: number;
  total_time_ms: number;
}

export interface CaptchaResult {
  type: "captcha_detected";
  detected: boolean;
  captcha_type: string | null;
  confidence: number;
  timestamp: string;
}

export interface FormDetection {
  type: "form_detected";
  count: number;
  forms: Array<{
    id: string;
    action?: string;
    method: string;
    inputs: number;
    has_password: boolean;
  }>;
  timestamp: string;
}

// APT Group Attribution
export interface APTGroupAttribution {
  type: "apt_group_attribution";
  threat_actor: string;
  attack_pattern: string;
  technique_id: string;
  confidence: number;
  attribution_details: Record<string, unknown>;
}

// Judge Agent Types
export interface JudgeDecision {
  id: string;
  action: "RENDER_VERDICT" | "REQUEST_MORE_INVESTIGATION";
  reason: string;
  investigate_urls: string[];
  investigate_reason: string;
  trust_score_result: TrustScoreResult | null;
  forensic_narrative: string;
  simple_narrative: string;
  recommendations: string[];
  simple_recommendations: string[];
  dark_pattern_summary: Record<string, unknown>[];
  entity_verification_summary: Record<string, unknown>[];
  evidence_timeline: Record<string, unknown>[];
  site_type: string;
  verdict_mode: "simple" | "expert";
  use_dual_verdict: boolean;
  dual_verdict: DualVerdict | null;
  timestamp: string;
}

export interface AuditEvidence {
  url: string;
  scout_results: ScoutResult[];
  vision_result: VisionResult | null;
  graph_result: GraphResult | null;
  iteration: number;
  max_iterations: number;
  site_type: string;
  site_type_confidence: number;
  verdict_mode: string;
  security_results: Record<string, unknown>;
}

export interface TrustScoreResult {
  final_score: number;
  risk_level: RiskLevel | string;
  sub_signals: SubSignal[];
  weighted_breakdown: Record<string, number>;
  overrides_applied: OverrideRule[];
  pre_override_score: number;
  explanation: string;
}

export interface SubSignal {
  name: string;
  raw_score: number;
  confidence: number;
  evidence_count: number;
  details: Record<string, unknown>;
}

export interface OverrideRule {
  id: string;
  name: string;
  description: string;
  condition: string;
  action: string;
  value: number;
  priority: number;
}

// ========================================
// Severity to overlay color mapping
// ========================================

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
