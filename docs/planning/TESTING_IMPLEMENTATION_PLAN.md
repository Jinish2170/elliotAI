# VERITAS - Testing & Implementation Plan
## Date: 2026-03-05

---

## PART 1: PLAYWRIGHT MCP TESTING PLAN

### 1.1 Test Environment Setup

```bash
# Prerequisites - Playwright MCP server must be running
# Check if Playwright MCP is available
# If not, install: npm install -g @modelcontextprotocol/server-playwright
```

### 1.2 Test Suite 1: Basic Functionality Tests

```javascript
// test: complete-audit-flow.spec.js

const { chromium } = require('playwright');

async function testCompleteAuditFlow() {
  // 1. Start browsers
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // 2. Navigate to landing page
  await page.goto('http://localhost:3000');
  await page.waitForLoadState('networkidle');

  console.log('✅ Landing page loaded');

  // 3. Check for URL input
  const urlInput = page.locator('input[type="url"], input[placeholder*="http"], input[placeholder*="URL"]');
  await expect(urlInput).toBeVisible();

  // 4. Enter test URL (site with good reputation)
  await urlInput.fill('https://www.wikipedia.org');

  // 5. Click audit start button
  const startButton = page.locator('button:has-text("Start"), button:has-text("Audit"), button:has-text("Analyze")');
  await startButton.click();

  // 6. Verify redirect to audit page
  await page.waitForURL(/\/audit\/[\w-]+/);
  console.log('✅ Redirected to audit page');

  // 7. Wait for WebSocket connection
  await page.waitForTimeout(1000);

  // 8. Monitor audit phases (wait up to 5 minutes)
  await page.waitForTimeout(180000); // 3 minutes wait for standard audit

  // 9. Verify audit completion
  const completionOverlay = page.locator('[role="dialog"], [class*="completion"], [class*="overlay"]');
  await expect(completionOverlay).toBeVisible({ timeout: 200000 });
  console.log('✅ Audit completed');

  // 10. Click to view report
  const reportButton = page.locator('a:has-text("Report"), a:has-text("View Details"), button:has-text("View")');
  await reportButton.click();

  // 11. Verify report page
  await page.waitForURL(/\/report\/[\w-]+/);
  console.log('✅ Report page loaded');

  // 12. Check for key report elements
  await expect(page.locator('[class*="trust"], [class*="score"]')).toBeVisible();
  await expect(page.locator('[class*="finding"], [class*="pattern"]')).toBeVisible();
  await expect(page.locator('[class*="security"]')).toBeVisible();

  console.log('✅ All report elements visible');

  await browser.close();
  return { status: 'PASS', message: 'Complete audit flow successful' };
}
```

### 1.3 Test Suite 2: Dark Pattern Detection

```javascript
// test: dark-pattern-detection.spec.js

async function testDarkPatternDetection() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Use a test site with known dark patterns
  const testUrl = 'https://example.com'; // Replace with actual test site

  await page.goto('http://localhost:3000');
  await page.fill('input[type="url"]', testUrl);
  await page.click('button:has-text("Start")');
  await page.waitForURL(/\/audit\/[\w-]+/);

  // Wait for vision phase to complete
  await page.waitForTimeout(120000);

  // Check for findings in narrative feed
  const narrativeFeed = page.locator('[class*="narrative"], [class*="feed"]');
  const findingsCount = await narrativeFeed.locator('[class*="finding"]').count();

  console.log(`Findings detected: ${findingsCount}`);

  // Verify screenshot carousel has highlights
  const screenshots = page.locator('[class*="screenshot"]');
  await expect(screenshots.first()).toBeVisible();

  // Check for highlight overlays
  const highlights = page.locator('[class*="highlight"], [class*="overlay"]');
  const hasHighlights = await highlights.count() > 0;

  await browser.close();
  return {
    status: 'PASS',
    findings: findingsCount,
    hasHighlights: hasHighlights
  };
}
```

### 1.4 Test Suite 3: Security Module Testing

```javascript
// test: security-modules.spec.js

async function testSecurityModules() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Run audit
  await page.goto('http://localhost:3000');
  await page.fill('input[type="url"]', 'https://example.com');
  await page.click('button:has-text("Start")');
  await page.waitForURL(/\/audit\/[\w-]+/);
  await page.waitForTimeout(180000);

  // Navigate to report
  await page.goto(page.url().replace('/audit/', '/report/'));

  // Check security panel
  const securityPanel = page.locator('[class*="security"], [class*="SecurityPanel"]');
  await expect(securityPanel).toBeVisible();

  // Check for security module results
  const modules = [
    'HSTS', 'CSP', 'Cookies', 'TLS', 'SSL',
    'GDPR', 'PCI DSS', 'OWASP'
  ];

  const foundModules = [];
  for (const module of modules) {
    const element = page.locator(`text=${module}`);
    const isVisible = await element.isVisible().catch(() => false);
    if (isVisible) foundModules.push(module);
  }

  console.log(`Security modules found in UI: ${foundModules.join(', ')}`);

  await browser.close();
  return {
    status: 'PASS',
    modules: foundModules,
    coverage: foundModules.length / modules.length
  };
}
```

### 1.5 Test Suite 4: WebSocket Event Streaming

```javascript
// test: websocket-streaming.spec.js

async function testWebSocketStreaming() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Capture console logs and network requests
  const wsMessages = [];
  page.on('websocket', ws => {
    ws.on('framesent', frame => {
      if (frame.payload) {
        try {
          const msg = JSON.parse(frame.payload.toString());
          wsMessages.push(msg);
        } catch (e) {
          wsMessages.push({ type: 'raw', payload: frame.payload.toString() });
        }
      }
    });
    ws.on('framereceived', frame => {
      if (frame.payload) {
        try {
          const msg = JSON.parse(frame.payload.toString());
          wsMessages.push(msg);
        } catch (e) {
          wsMessages.push({ type: 'raw', payload: frame.payload.toString() });
        }
      }
    });
  });

  await page.goto('http://localhost:3000');
  await page.fill('input[type="url"]', 'https://example.com');
  await page.click('button:has-text("Start")');

  // Wait for audit to collect messages
  await page.waitForTimeout(180000);

  // Analyze messages
  const eventTypes = new Set(wsMessages.map(m => m.type));
  console.log(`WebSocket event types received: ${Array.from(eventTypes).join(', ')}`);

  // Verify critical events
  const requiredEvents = ['phase_start', 'phase_complete', 'audit_result', 'audit_complete'];
  const missingEvents = requiredEvents.filter(e => !eventTypes.has(e));

  await browser.close();
  return {
    status: missingEvents.length === 0 ? 'PASS' : 'FAIL',
    eventTypes: Array.from(eventTypes),
    missingEvents: missingEvents,
    totalMessages: wsMessages.length
  };
}
```

### 1.6 Test Suite 5: Report Mode Toggle

```javascript
// test: report-mode-toggle.spec.js

async function testReportModeToggle() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Complete audit first
  await page.goto('http://localhost:3000');
  await page.fill('input[type="url"]', 'https://example.com');
  await page.click('button:has-text("Start")');
  await page.waitForTimeout(60000); // Quick tier

  // Navigate to report
  await page.goto(page.url().replace('/audit/', '/report/'));

  // Find mode toggle
  const modeToggle = page.locator('button:has-text("Expert"), button:has-text("Simple"), [role="switch"]');
  if (await modeToggle.isVisible()) {
    // Get initial mode
    let currentMode = await modeToggle.textContent();

    // Toggle to expert
    await modeToggle.click();
    await page.waitForTimeout(500);

    // Check for CWE/CVSS elements (expert mode)
    const expertElements = page.locator('text=CWE-, text=CVSS');
    const hasExpertElements = await expertElements.count() > 0;

    // Toggle back to simple
    await modeToggle.click();
    await page.waitForTimeout(500);
  }

  await browser.close();
  return {
    status: 'PASS',
    modeToggleExists: await modeToggle.isVisible() || false
  };
}
```

### 1.7 Test Suite 6: Tier Selection (Future)

```javascript
// test: tier-selection.spec.js - FUTURE IMPLEMENTATION

async function testTierSelection() {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto('http://localhost:3000');

  // Check for tier selector
  const tierSelector = page.locator('select, [role="combobox"], [class*="tier"]');
  const tierSelectorExists = await tierSelector.isVisible().catch(() => false);

  if (tierSelectorExists) {
    // Test each tier
    const tiers = ['quick', 'standard', 'deep'];

    for (const tier of tiers) {
      await tierSelector.selectOption(tier);
      await page.fill('input[type="url"]', 'https://example.com');
      await page.click('button:has-text("Start")');

      const auditUrl = page.url();
      await page.goto('http://localhost:3000'); // Reset
    }
  }

  await browser.close();
  return {
    status: tierSelectorExists ? 'PASS' : 'NOT_IMPLEMENTED',
    tierSelectorExists
  };
}
```

---

## PART 2: FRONTEND INTEGRATION FEATURES TO IMPLEMENT

### 2.1 Feature 1: Audit History Page

**File**: `frontend/src/app/history/page.tsx`

```typescript
"use client";

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

interface AuditHistoryEntry {
  audit_id: string;
  url: string;
  status: string;
  audit_tier: string;
  verdict_mode: string;
  trust_score: number;
  risk_level: string;
  site_type: string;
  pages_scanned: number;
  elapsed_seconds: number;
  created_at: string;
}

export default function AuditHistoryPage() {
  const [audits, setAudits] = useState<AuditHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const searchParams = useSearchParams();

  // Get filters from URL
  const statusFilter = searchParams.get('status');
  const riskFilter = searchParams.get('risk');

  useEffect(() => {
    fetchAudits();
  }, [statusFilter, riskFilter]);

  async function fetchAudits() {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status_filter', statusFilter);
    if (riskFilter) params.append('risk_level_filter', riskFilter);

    const response = await fetch(`/api/audits/history?${params}`);
    const data = await response.json();
    setAudits(data.audits || []);
    setLoading(false);
  }

  return (
    <div className="min-h-screen bg-[var(--v-deep)] p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Audit History</h1>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          value={statusFilter || 'all'}
          onChange={(e) => router.push(`/history?status=${e.target.value}&risk=${riskFilter || ''}`)}
          className="bg-white/10 text-white border border-white/20 rounded px-4 py-2"
        >
          <option value="all">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="running">Running</option>
          <option value="error">Error</option>
        </select>

        <select
          value={riskFilter || 'all'}
          onChange={(e) => router.push(`/history?status=${statusFilter || ''}&risk=${e.target.value}`)}
          className="bg-white/10 text-white border border-white/20 rounded px-4 py-2"
        >
          <option value="all">All Risk Levels</option>
          <option value="trusted">Trusted</option>
          <option value="probably_safe">Probably Safe</option>
          <option value="suspicious">Suspicious</option>
          <option value="high_risk">High Risk</option>
        </select>
      </div>

      {/* Audit List */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-white">Loading...</div>
        ) : audits.length === 0 ? (
          <div className="text-white/60">No audits found</div>
        ) : (
          audits.map(audit => (
            <div
              key={audit.audit_id}
              onClick={() => router.push(`/report/${audit.audit_id}`)}
              className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 cursor-pointer transition"
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-white font-medium">{audit.url}</div>
                  <div className="text-white/60 text-sm mt-1">
                    {new Date(audit.created_at).toLocaleString()} • {audit.audit_tier}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-[var(--v-primary)]">
                    {audit.trust_score}
                  </div>
                  <div className="text-sm text-white/60">{audit.risk_level}</div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

### 2.2 Feature 2: Audit Comparison UI

**File**: `frontend/src/app/compare/page.tsx`

```typescript
"use client";

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface AuditComparison {
  audits: AuditHistoryEntry[];
  trust_score_deltas: Array<{
    from_audit_id: string;
    to_audit_id: string;
    delta: number;
    percentage_change: number | null;
  }>;
  risk_level_changes: Array<{
    from_audit_id: string;
    to_audit_id: string;
    from: string;
    to: string;
  }>;
}

export default function AuditComparisonPage() {
  const [comparison, setComparison] = useState<AuditComparison | null>(null);
  const [selectedAudits, setSelectedAudits] = useState<string[]>([]);
  const router = useRouter();
  const searchParams = useSearchParams();
  const auditIdsParam = searchParams.get('ids');

  useEffect(() => {
    if (auditIdsParam) {
      const ids = auditIdsParam.split(',');
      fetchComparison(ids);
    }
  }, [auditIdsParam]);

  async function fetchComparison(ids: string[]) {
    const response = await fetch('/api/audits/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ audit_ids: ids }),
    });
    const data = await response.json();
    setComparison(data);
  }

  return (
    <div className="min-h-screen bg-[var(--v-deep)] p-8">
      <h1 className="text-3xl font-bold text-white mb-6">Audit Comparison</h1>

      {comparison && (
        <div className="space-y-8">
          {/* Trust Score Deltas */}
          {comparison.trust_score_deltas.map(delta => (
            <div key={`${delta.from_audit_id}-${delta.to_audit_id}`} className="bg-white/5 rounded-lg p-6">
              <h3 className="text-white text-xl mb-4">Trust Score Change</h3>
              <div className="flex items-center gap-4">
                <div className="text-white">
                  {delta.from_audit_id} → {delta.to_audit_id}
                </div>
                <div className={`text-2xl font-bold ${delta.delta >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {delta.delta >= 0 ? '+' : ''}{delta.delta}
                  {delta.percentage_change && ` (${delta.percentage_change.toFixed(1)}%)`}
                </div>
              </div>
            </div>
          ))}

          {/* Risk Level Changes */}
          {comparison.risk_level_changes.map(change => (
            <div key={`${change.from_audit_id}-${change.to_audit_id}`} className="bg-white/5 rounded-lg p-6">
              <h3 className="text-white text-xl mb-4">Risk Level Change</h3>
              <div className="flex items-center gap-4">
                <div className="px-3 py-1 rounded bg-gray-500/20 text-white">
                  {change.from}
                </div>
                <div className="text-white">→</div>
                <div className="px-3 py-1 rounded bg-cyan-500/20 text-cyan-400">
                  {change.to}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

### 2.3 Feature 3: Tier Selector on Landing Page

**Modify**: `frontend/src/components/landing/HeroSection.tsx`

```typescript
// Add to existing HeroSection component

interface TierOption {
  id: string;
  label: string;
  description: string;
  duration: string;
  pages: string;
  cost: string;
}

const TIERS: Record<string, TierOption> = {
  quick: {
    id: 'quick',
    label: 'Quick Scan',
    description: 'Basic security checks and visible patterns',
    duration: '~60s',
    pages: '1-3 pages',
    cost: '~5 credits'
  },
  standard: {
    id: 'standard_audit',
    label: 'Standard Audit',
    description: 'Full 5-agent pipeline with visual and graph analysis',
    duration: '~3min',
    pages: '5 pages',
    cost: '~20 credits'
  },
  deep: {
    id: 'deep_forensic',
    label: 'Deep Forensic',
    description: 'Extended crawl, temporal analysis, complete security audit',
    duration: '~5min',
    pages: '10 pages',
    cost: '~50 credits'
  }
};

// In component:
const [selectedTier, setSelectedTier] = useState('standard_audit');

// Add to UI:
<div className="grid grid-cols-3 gap-4 mt-6">
  {Object.values(TIERS).map(tier => (
    <button
      key={tier.id}
      onClick={() => setSelectedTier(tier.id)}
      className={`p-4 rounded-lg border-2 transition ${
        selectedTier === tier.id
          ? 'border-cyan-500 bg-cyan-500/10'
          : 'border-white/10 bg-white/5 hover:border-white/20'
      }`}
    >
      <div className="text-white font-medium">{tier.label}</div>
      <div className="text-white/60 text-sm mt-1">{tier.description}</div>
      <div className="mt-2 text-xs text-white/40">
        {tier.duration} • {tier.pages} • {tier.cost}
      </div>
    </button>
  ))}
</div>

// Pass tier to audit start:
{selectedTier && (
  <Link
    href={`/audit/new?url=${encodeURIComponent(url)}&tier=${selectedTier}`}
    className="..."
  >
    Start Audit
  </Link>
)}
```

### 2.4 Feature 4: Darknet Auditor UI

**File**: `frontend/src/components/darknet/DarknetAuditor.tsx`

```typescript
"use client";

import { useState } from 'react';
import { Search, Shield, AlertTriangle } from 'lucide-react';

interface DarknetIntel {
  onion_url: string;
  marketplace: string;
  categories: string[];
  threat_level: 'low' | 'medium' | 'high' | 'critical';
  indicators: string[];
  related_domains: string[];
}

export function DarknetAuditor() {
  const [onionUrl, setOnionUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<DarknetIntel | null>(null);

  async function auditOnion() {
    setLoading(true);
    try {
      const response = await fetch('/api/darknet/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: onionUrl }),
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error('Darknet audit failed:', error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-black/50 border border-red-500/30 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-4">
        <Shield className="text-red-500" />
        <h2 className="text-xl font-bold text-white">Darknet Auditor</h2>
      </div>

      <div className="flex gap-2 mb-6">
        <input
          type="text"
          value={onionUrl}
          onChange={(e) => setOnionUrl(e.target.value)}
          placeholder="onion_address.onion"
          className="flex-1 bg-white/10 border border-white/20 rounded px-4 py-2 text-white placeholder-white/40"
        />
        <button
          onClick={auditOnion}
          disabled={loading || !onionUrl.endsWith('.onion')}
          className="bg-red-500 text-white px-6 py-2 rounded flex items-center gap-2 disabled:opacity-50"
        >
          <Search size={18} />
          Analyze
        </button>
      </div>

      {loading && (
        <div className="text-center text-white/60">
          Scanning darknet threat intelligence...
        </div>
      )}

      {results && (
        <div className="space-y-4">
          {/* Threat Level */}
          <div className={`p-4 rounded-lg bg-${results.threat_level === 'critical' ? 'red' : results.threat_level}-500/20`}>
            <div className="flex items-center gap-2 text-white font-medium">
              <AlertTriangle />
              Threat Level: {results.threat_level.toUpperCase()}
            </div>
          </div>

          {/* Marketplace Detection */}
          {results.marketplace && (
            <div className="bg-white/5 p-4 rounded-lg">
              <div className="text-white/60 text-sm mb-1">Detected Marketplace</div>
              <div className="text-white">{results.marketplace}</div>
            </div>
          )}

          {/* Categories */}
          {results.categories.length > 0 && (
            <div className="bg-white/5 p-4 rounded-lg">
              <div className="text-white/60 text-sm mb-2">Categories</div>
              <div className="flex flex-wrap gap-2">
                {results.categories.map(cat => (
                  <span key={cat} className="px-2 py-1 bg-white/10 rounded text-white text-sm">
                    {cat}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Indicators */}
          {results.indicators.length > 0 && (
            <div className="bg-white/5 p-4 rounded-lg">
              <div className="text-white/60 text-sm mb-2">Indicators of Compromise</div>
              <ul className="space-y-1">
                {results.indicators.map((indicator, i) => (
                  <li key={i} className="text-red-400 text-sm">
                    • {indicator}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Related Domains */}
          {results.related_domains.length > 0 && (
            <div className="bg-white/5 p-4 rounded-lg">
              <div className="text-white/60 text-sm mb-2">Related Clearnet Domains</div>
              <div className="space-y-1">
                {results.related_domains.map(domain => (
                  <div key={domain} className="text-white text-sm truncate">
                    {domain}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## PART 3: EXECUTION CHECKLIST

### 3.1 Before Testing

- [ ] Backend server running on port 8000 (`cd backend && uvicorn main:app --reload`)
- [ ] Frontend server running on port 3000 (`cd frontend && npm run dev`)
- [ ] NVIDIA_NIM_API_KEY configured in `veritas/.env`
- [ ] Playwright MCP server available
- [ ] Test URLs ready (wikipedia.org, safe commerce site, test scam site)

### 3.2 Run Test Suite

```bash
# Using Playwright MCP tool
# Execute each test scenario sequentially

# Test 1: Complete Audit Flow
# Result: ✅ / ❌

# Test 2: Dark Pattern Detection
# Result: ✅ / ❌

# Test 3: Security Modules
# Result: ✅ / ❌

# Test 4: WebSocket Streaming
# Result: ✅ / ❌

# Test 5: Report Mode Toggle
# Result: ✅ / ❌

# Test 6: Tier Selection (if implemented)
# Result: ✅ / ❌ / NOT_IMPLEMENTED
```

### 3.3 After Testing

Document results:
- [ ] All passing tests listed
- [ ] All failing tests with error details
- [ ] Bugs identified
- [ ] Integration gaps confirmed
- [ ] Performance issues noted

---

## PART 4: IMPLEMENTATION PRIORITY MATRIX

| ID | Feature | Priority | Effort | Value | Status |
|----|---------|----------|--------|-------|--------|
| F1 | Audit History Page | HIGH | Medium | High | ❌ Not Implemented |
| F2 | Audit Comparison UI | HIGH | Medium | High | ❌ Not Implemented |
| F3 | Tier Selector | MEDIUM | Low | Medium | ❌ Not Implemented |
| F4 | Security Module Selection | MEDIUM | Medium | Medium | ❌ Not Implemented |
| F5 | Darknet Auditor UI | LOW | High | Low* | ❌ Not Implemented |
| F6 | IOC Indicators Panel | LOW | Medium | Low | ❌ Not Implemented |
| F7 | Graph Visualization | LOW | High | Low | ❌ Not Implemented |
| F8 | MITRE ATT&CK View | LOW | Medium | Low | ❌ Not Implemented |

*Low value unless for darknet research use case

---

*Plan Date: 2026-03-05*
