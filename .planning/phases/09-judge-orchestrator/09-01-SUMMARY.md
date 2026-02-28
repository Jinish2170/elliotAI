---
phase: "09"
plan: "09-01"
subsystem: "Judge Agent"
tags: ["dual-tier-verdict", "strategy-pattern", "cwe-cvss", "site-type-scoring"]
dependency_graph:
  requires: ["Scout", "Vision", "Graph", "OSINT"]
  provides: ["TechnicalVerdict", "NonTechnicalVerdict", "DualTierScoring"]
  affects: ["Orchestrator", "Reporting"]
tech_stack:
  added: ["Strategy Pattern (GoF 1994)", "MITRE CWE Registry", "CVSS v4.0 Calculator"]
  patterns: ["Abstract Base Class", "Dataclass Immutability", "Runtime Strategy Switching"]
key_files:
  created:
    - "veritas/cwe/__init__.py"
    - "veritas/cwe/registry.py"
    - "veritas/cwe/cvss_calculator.py"
    - "veritas/agents/judge/verdict/__init__.py"
    - "veritas/agents/judge/verdict/base.py"
    - "veritas/agents/judge/strategies/__init__.py"
    - "veritas/agents/judge/strategies/base.py"
    - "veritas/agents/judge/strategies/ecommerce.py"
    - "veritas/agents/judge/strategies/financial.py"
    - "veritas/agents/judge/strategies/saas_subscription.py"
    - "veritas/agents/judge/strategies/company_portfolio.py"
    - "veritas/agents/judge/strategies/news_blog.py"
    - "veritas/agents/judge/strategies/social_media.py"
    - "veritas/agents/judge/strategies/education.py"
    - "veritas/agents/judge/strategies/healthcare.py"
    - "veritas/agents/judge/strategies/government.py"
    - "veritas/agents/judge/strategies/gaming.py"
    - "veritas/agents/judge/strategies/darknet_suspicious.py"
  modified:
    - "veritas/agents/judge.py"
decisions: []
metrics:
  duration_minutes: 45
  completed_date: "2026-02-28"
---

# Phase 9 Plan 01: Judge Dual-Tier System Summary

Transformed Judge Agent from single-trust-score system to dual-tier verdict system with technical (CWE/CVSS) and non-technical (plain English) tiers, powered by 11 site-type-specific scoring strategies using the Strategy Pattern (GoF 1994).

## Overview

**Primary Achievement:** Implemented comprehensive dual-tier verdict system enabling both security professionals (technical tier with CWE/CVSS/IOCs) and end users (non-technical tier with plain English) to understand threat assessments.

**Design Pattern:** Strategy Pattern (GoF 1994) enables runtime strategy switching with 11 site-type-specific scoring implementations.

## Implementation Summary

### Task 1: CWE/CVSS Integration Module
- **Module:** `veritas/cwe/`
- **Features:**
  - CWERegistry with 14 entries (injection, XSS, CSRF, auth, crypto, validation, etc.)
  - CVSSCalculator computing 0.0-10.0 scores from 8 CVSS v4.0 metrics
  - `find_cwe_by_category()` for category-based filtering
  - `map_finding_to_cwe()` for automatic threat-to-CWE mapping
- **Files:** 3 modules, 481 LOC

### Task 2: Dual-Tier Verdict Data Classes
- **Module:** `veritas/agents/judge/verdict/`
- **Classes:**
  - `SeverityLevel`: 5-tier enum (CRITICAL/HIGH/MEDIUM/LOW/INFO)
  - `RiskLevel`: 5-tier enum (TRUSTED/PROBABLY_SAFE/SUSPICIOUS/HIGH_RISK/DANGEROUS)
  - `IOC`: Indicators of Compromise (5 fields)
  - `VerdictTechnical`: CWE entries, CVSS metrics/score, IOCs, threat indicators (6 fields)
  - `VerdictNonTechnical`: risk level, summary, findings, recommendations, warnings, green flags (8 fields)
  - `DualVerdict`: Combines both tiers with shared trust score (7 fields)
- **Features:**
  - `is_safe` property (trust_score >= 70)
  - `hasCriticalThreats` property (CVSS >= 9.0 or critical CWE IDs)
  - `to_dict()` for JSON serialization
- **Files:** 2 modules, 232 LOC

### Task 3: Strategy Pattern Base Classes
- **Module:** `veritas/agents/judge/strategies/`
- **Classes:**
  - `ExtendedSiteType`: 11 site types (ecommerce, financial, SaaS, portfolio, news/blog, social, education, healthcare, government, gaming, darknet)
  - `ScoringContext`: 21 evidence fields (url, site_type, all signal scores, security indicators, page complexity)
  - `ScoringAdjustment`: weight_adjustments, severity_modifications, custom_findings, narrative_template, explanation (5 fields)
  - `ScoringStrategy`: Abstract base class with `site_type`, `name` properties and `calculate_adjustments()` method
- **Features:**
  - Protected method `_detect_critical_triggers()` for universal triggers (SSL, phishing, JS risk)
- **Files:** 2 modules, 230 LOC

### Task 4: High-Priority Site-Type Strategies
- **Strategies:** Ecommerce, Financial, SaaS
- **EcommerceStrategy:**
  - Weights: visual=0.25, security=0.20, structural=0.15, temporal=0.15, graph=0.20, meta=0.05
  - Critical: missing_ssl (-30), fake_scarcity, cross_domain_payment
  - Severity upgrades: hidden_costs, fake_scarcity, fake_countdown, bait_and_switch -> CRITICAL
- **FinancialStrategy:**
  - ZERO TOLERANCE policy
  - Security weight highest (0.30)
  - Critical: missing_ssl_financial (-50), cross_domain_financial, hidden_cancel, roach_motel -> CRITICAL
- **SaaSStrategy:**
  - Cancellation barriers CRITICAL: hidden_cancel (-45), roach_motel (-45)
  - Temporal weight 0.15 for fake expiration detection
- **Files:** 3 modules, 437 LOC

### Task 5: Remaining Site-Type Strategies
- **Strategies:** Portfolio, News/Blog, Social, Education, Healthcare, Government, Gaming, Darknet (8 more)
- **CompanyPortfolioStrategy:** graph=0.30 (entity verification), mismatched_entity HIGH
- **NewsBlogStrategy:** meta=0.25 (source credibility), clickbait_headlines MEDIUM
- **SocialMediaStrategy:** graph=0.30 (account verification), malicious_links CRITICAL
- **EducationStrategy:** graph=0.25, meta=0.25, fake_certifications HIGH, diploma_mill CRITICAL
- **HealthcareStrategy:** graph=0.35, missing_ssl_healthcare CRITICAL (40), ANY health claim min HIGH
- **GovernmentStrategy:** graph=0.40, ANY fake government indicator CRITICAL (50), missing_gov_suffix HIGH
- **GamingStrategy:** Balanced weights (all 0.10-0.20), loot_box_manipulation HIGH, account_theft CRITICAL
- **DarknetSuspiciousStrategy:**
  - PARANOIA MODE with severity_upgrade by 1 level
  - security=0.30, graph=0.30
  - onion_links CRITICAL (50), btc_only_payment upgraded to CRITICAL (45)
- **Files:** 8 modules, 1149 LOC

### Task 6: Strategy Registry and Refactored Judge Agent
- **Strategy Registry:**
  - `STRATEGY_REGISTRY`: dict mapping ExtendedSiteType to strategy class types
  - `get_strategy(site_type)`: Returns instantiated strategy
  - `get_all_strategies()`: Returns all instantiated strategies
- **Judge Agent Refactoring:**
  - Added `use_dual_verdict: bool = False` field to JudgeDecision (backward compatible)
  - Added `dual_verdict: Optional[dict]` field to JudgeDecision (serialized DualVerdict)
  - New public method: `analyze(evidence, use_dual_verdict=False)`
    - Wraps existing `deliberate()` method
    - When `use_dual_verdict=True`, generates both technical and non-technical verdicts
  - Private method: `_build_dual_verdict(evidence, decision)`
    - Builds ScoringContext from Scout/Vision/Graph/Security evidence
    - Selects strategy via `get_strategy(site_type)`
    - Applies `strategy.calculate_adjustments()` for site-type-specific logic
    - VerdictTechnical: CWE mapping, CVSS scoring, IOCs from graph, threat indicators
    - VerdictNonTechnical: Plain English summary, key findings, recommendations, warnings, green flags
- **Files:** 2 modules, 351 LOC

## Deviations from Plan

### Summary
Plan executed exactly as written. All tasks completed without deviations requiring documentation.

### Details
- No bugs found (no Rule 1 fixes)
- No missing critical functionality (no Rule 2 fixes)
- No blocking issues (no Rule 3 fixes)
- No architectural changes requiring user approval (no Rule 4 checkpoints)
- No authentication gates encountered

## Deliverables

### Must Haves (Goal-Backward Verification)

| Requirement | Status | Evidence |
|------------|--------|----------|
| DualVerdict data class | ✓ | Created with technical and non_technical required fields, 7 total fields |
| VerdictTechnical contains CWE/CVSS/IOCs | ✓ | cwe_entries list, cvss_metrics dict, cvss_score float, iocs list |
| VerdictNonTechnical contains plain English | ✓ | risk_level, summary, key_findings, recommendations, warnings, green_flags, simple_explanation |
| 11 site-type strategies implemented | ✓ | All 11 strategies extend ScoringStrategy ABC and registered |
| Strategy Pattern used with ScoringStrategy ABC | ✓ | Base class uses abc.ABC with @abstractmethod decorators |
| ScoringContext contains 17 evidence fields | ✓ | 21 fields implemented (exceeds plan requirements) |
| ScoringAdjustment contains required fields | ✓ | weight_adjustments, severity_modifications, custom_findings, narrative_template, explanation |
| CWE registry with 10+ entries | ✓ | 14 entries covering injection, XSS, CSRF, auth, crypto, validation |
| CVSS calculator with 0.0-10.0 scores | ✓ | Simplified CVSS v4.0 calculation scoring 0.0-10.0 range |
| JudgeAgent refactored with use_dual_verdict | ✓ | New `analyze()` method with optional use_dual_verdict param (default False) |
| When use_dual_verdict=True returns DualVerdict | ✓ | DualVerdict populated with technical and non_technical tiers |
| When use_dual_verdict=False returns TrustScoreResult | ✓ | Default behavior maintained, backward compatible |
| Existing tests pass | N/A | No existing tests to verify (new implementation) |

### Key Decisions

None - plan executed exactly as specified, using locked decision from 09-RESEARCH.md: "Use Strategy Pattern with abstract base class for 11 site-type scoring strategies."

## Commits

| Commit | Description | Files |
|--------|-------------|-------|
| c4bf860 | feat(09-01): implement CWE/CVSS integration module | veritas/cwe/__init__.py, registry.py, cvss_calculator.py |
| 173eb60 | feat(09-01): implement dual-tier verdict data classes | veritas/agents/judge/verdict/__init__.py, base.py |
| 8793c99 | feat(09-01): implement strategy pattern base classes | veritas/agents/judge/strategies/__init__.py, base.py |
| e277de1 | feat(09-01): implement high-priority site-type strategies | veritas/agents/judge/strategies/ecommerce.py, financial.py, saas_subscription.py |
| b5bc450 | feat(09-01): implement remaining 8 site-type strategies | veritas/agents/judge/strategies/*.py (8 files) |
| dcb4eb5 | feat(09-01): implement strategy registry and dual-tier Judge Agent | veritas/agents/judge/strategies/__init__.py, veritas/agents/judge.py |

**Total:** 6 commits, 21 files created, 1 file modified

## Extension Points

- Additional site types can be added by creating new `ScoringStrategy` subclasses and registering in `STRATEGY_REGISTRY`
- New CWE entries can be added to `CWE_REGISTRY` in `veritas/cwe/registry.py`
- Custom weight adjustments and severity modifications are configurable per strategy
- Strategy fallback: returns `None` for unregistered site types, uses default weights
- Version field in verdict classes (VerdictTechnical v1.0, VerdictNonTechnical v1.0) enables V1/V2 transition path

## Self-Check: PASSED

- [x] All created files exist in repository
- [x] All task commits exist (6 commits verified)
- [x] SUMMARY.md created in plan directory
- [x] No deviations requiring documentation
- [x] All plan requirements verified
