---
phase: 10-cybersecurity-deep-dive
plan: 03
subsystem: Compliance Security
tags: [pci-dss, gdpr, security, compliance]
completed_date: "2026-02-28"
duration_min: 5
---

# Phase 10 Plan 03: PCI DSS and GDPR Compliance Modules Summary

**One-liner:** Two MEDIUM-tier compliance modules implementing PCI DSS (5 requirements) and GDPR (5 articles) with CWE ID mapping and CVSS severity scoring.

## Implementation Overview

Added two compliance security modules to the Veritas analysis framework, each detecting specific regulatory violations in web applications. Both modules only report findings when relevant data collection or payment forms are detected to minimize false positives.

### Deliverables

| File | Tier | Provides | Exports |
|------|------|----------|---------|
| `veritas/analysis/security/pci_dss.py` | MEDIUM | PCI DSS compliance checking (3.3, 3.4, 4.1, 6.5.1, 8.2) | `PCIDSSComplianceModule` |
| `veritas/analysis/security/gdpr.py` | MEDIUM | GDPR compliance checking (Art. 7, 17, 25, 32, 35) | `GDPRComplianceModule` |

### Technical Approach

Both modules follow the SecurityModule base class pattern:
- MEDIUM tier with 12-second timeout
- Normalize headers to lowercase per HTTP RFC 7230
- Only report findings when relevant data patterns detected
- Use `cvss_calculate_score()` and `PRESET_METRICS` for CVSS scoring
- Map findings to appropriate CWE IDs from Phase 9 registry

### Module Details

#### PCIDSSComplianceModule

**PCI DSS 3.2.1 Requirements Checked:**

1. **Req 3.3: Mask PAN when displayed**
   - Pattern: Credit card numbers shown without masking (regex: `\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}`)
   - Detection: Finds unmasked PANs, excludes masked patterns (`**** **** **** 1234`)
   - Confidence: 0.70 if credit card forms present
   - CWE: CWE-359 (Exposure of Private Personal Information)
   - CVSS: 7.0 (high_risk preset)

2. **Req 3.4: Encrypt PAN at rest**
   - Pattern: Credit card inputs without encryption indicators
   - Detection: Checks for `data-encrypt` attribute or `aria-label` mentioning encryption
   - Confidence: 0.60
   - CWE: CWE-311 (Missing Encryption of Sensitive Data)
   - CVSS: 7.0 (high_risk preset)

3. **Req 4.1: Encrypt transmission over open networks**
   - Pattern: Payment forms over HTTP (not HTTPS)
   - Detection: Checks form action URLs and page protocol
   - Confidence: 0.90
   - CWE: CWE-319 (Cleartext Transmission)
   - CVSS: 9.0 (critical_web preset)

4. **Req 6.5.1: SQL injection protection**
   - Pattern: Payment forms without input validation
   - Detection: Looks for `pattern`, `maxlength`, or numeric type attributes
   - Confidence: 0.50 (recommends OWASP A03 scan confirmation)
   - CWE: CWE-89 (SQL Injection)
   - CVSS: 9.0 (critical_web preset)

5. **Req 8.2: Strong authentication**
   - Pattern: Password fields with weak requirements
   - Detection: Checks for `minlength`, `pattern`, and `autocomplete='new-password'`
   - Confidence: 0.60
   - CWE: CWE-521 (Weak Password Requirements)
   - CVSS: 7.0 (high_risk preset)

#### GDPRComplianceModule

**GDPR Articles Checked:**

1. **Art. 7: Consent requirements**
   - Pattern: Data collection forms without explicit consent checkbox
   - Detection: Checks for consent-like checkboxes with `required` attribute
   - Confidence: 0.70
   - CWE: CWE-359 (Exposure of Private Information)
   - CVSS: 7.0 (high_risk preset)

2. **Art. 17: Right to erasure**
   - Pattern: No data deletion/account deletion mechanism
   - Detection: Searches for deletion keywords on pages with account forms
   - Confidence: 0.50
   - CWE: CWE-200 (Exposure of Sensitive Information)
   - CVSS: 2.0 (low_risk preset)

3. **Art. 25: Privacy by design and by default**
   - Pattern: Pre-checked consent checkboxes
   - Detection: Finds `checked` attribute on consent/marketing checkboxes
   - Confidence: 0.80
   - CWE: CWE-359 (Exposure of Private Information)
   - CVSS: 7.0 (high_risk preset)

4. **Art. 32: Security of processing**
   - Pattern: Missing security headers for data protection
   - Detection: Checks for HSTS, CSP, X-Frame-Options (report if 2+ missing)
   - Confidence: 0.60
   - CWE: CWE-319 (Cleartext Transmission)
   - CVSS: 5.0 (medium_risk preset)

5. **Art. 35: Data Protection Impact Assessment (DPIA)**
   - Pattern: High-risk data processing without privacy policy
   - Detection: Searches for health/financial/biometric keywords and privacy policy indicators
   - Confidence: 0.50
   - CWE: CWE-200 (Exposure of Sensitive Information)
   - CVSS: 5.0 (medium_risk preset)

## Deviations from Plan

None - plan executed exactly as specified.

## Key Decisions

1. **Low-confidence checks with confirmations:** For SQL injection risk (Req 6.5.1), used 0.50 confidence and recommended OWASP A03 scan for confirmation, balancing detection rate with false positive prevention.

2. **Multi-missing-header threshold:** For GDPR Art. 32, only reported security header findings when at least 2 critical headers missing (HSTS, CSP, X-Frame-Options) to reduce noise for simple implementations.

3. **Payment form gate:** PCI DSS module only reports findings when payment-related forms detected (credit card fields, payment URLs, checkout indicators) to avoid false positives on informational pages discussing payment topics.

4. **Data collection gate:** GDPR module only reports findings when data collection fields detected (email, name, phone, account forms) to avoid false positives on non-data-collection pages.

## Dependencies

**Requires:**
- `veritas.analysis.security.base.SecurityModule`
- `veritas.cwe.cvss_calculator` (PRESET_METRICS)
- `veritas.cwe.registry` (map_finding_to_cwe)

**Provides:**
- PCI DSS compliance checking (req 3.3, 3.4, 4.1, 6.5.1, 8.2)
- GDPR compliance checking (art 7, 17, 25, 32, 35)

## Testing

**Automated verification:**
```python
from veritas.analysis.security.pci_dss import PCIDSSComplianceModule
m = PCIDSSComplianceModule()
# Output: pci_dss, tier: SecurityTier.MEDIUM, timeout: 12

from veritas.analysis.security.gdpr import GDPRComplianceModule
m = GDPRComplianceModule()
# Output: gdpr, tier: SecurityTier.MEDIUM, timeout: 12
```

## Integration

These modules integrate with the existing security module architecture via:
- Auto-discovery through SecurityModule base class
- Tier-based execution (MEDIUM tier, 12s timeout)
- CWE ID mapping for professional vulnerability reporting
- CVSS scoring using Phase 9 calculator

Both modules follow the header normalization pattern (lowercase keys) for HTTP RFC 7230 compliance.

## Commits

| Hash | Message |
|------|---------|
| 2496920 | feat(10-03): implement PCI DSS compliance module |
| f22330d | feat(10-03): implement GDPR compliance module |

## Success Criteria Met

- [x] PCIDSSComplianceModule extends SecurityModule, category_id="pci_dss", tier=MEDIUM, timeout=12
- [x] GDPRComplianceModule extends SecurityModule, category_id="gdpr", tier=MEDIUM, timeout=12
- [x] PCI DSS module checks Req 3.3: PAN masking (search for credit card patterns)
- [x] PCI DSS module checks Req 3.4: PAN encryption at rest (forms without encryption indicator)
- [x] PCI DSS module checks Req 4.1: HTTPS transmission (payment forms over HTTP)
- [x] PCI DSS module checks Req 6.5.1: SQL injection protection (weak input validation)
- [x] PCI DSS module checks Req 8.2: Strong authentication (weak password requirements)
- [x] GDPR module checks Art. 7: Consent requirements (no consent checkbox)
- [x] GDPR module checks Art. 17: Right to erasure (no deletion mechanism)
- [x] GDPR module checks Art. 25: Pre-checked consent boxes (not privacy by default)
- [x] GDPR module checks Art. 32: Security headers (missing HSTS/CSP)
- [x] GDPR module checks Art. 35: DPIA for high-risk data (sensitive data without privacy policy)
- [x] Both modules only report findings when data collection/payment detected
- [x] All findings include cwe_id via CWEMapper mapping
- [x] Plan committed with atomic task commits

## Next Steps

Consider updating `veritas/analysis/security/__init__.py` to export the new modules for easier imports, enabling auto-discovery via `get_all_security_modules()`.
