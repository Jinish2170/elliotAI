# Architecture Patterns: VERITAS v2.0 Enhancement

**Domain:** Forensic Web Auditing Platform Enhancement  
**Researched:** 2026-02-23

---

## Recommended Architecture

VERITAS v2.0 extends the existing agent-based architecture with new capabilities while maintaining the established patterns. The architecture follows a microservices-inspired approach where each agent is an independent module communicating through shared state models.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VERITAS v2.0 Architecture                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │   Scout     │───▶│  Security   │───▶│   Vision    │───▶│   Graph     │ │
│  │  Agent      │    │  Agent      │    │  Agent      │    │Investigator │ │
│  │             │    │             │    │  (5-pass)   │    │  (+OSINT)   │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│                              └─────────────┐                   │           │
│                                            ▼                   │           │
│  ┌─────────────┐    ┌─────────────┐  ┌─────────────┐          │           │
│  │   Judge     │◀───│ Progress    │◀─│   VLM/      │          │           │
│  │  Agent      │    │  Emitter    │  │   CV        │          │           │
│  │ (Dual-tier) │    │  (real-time)│  │  (NIM, OpenCV)          │           │
│  └─────────────┘    └─────────────┘  └─────────────┘          │           │
│        ▼                                                           ▼       │
│  ┌─────────────────────────────────────┐    ┌─────────────────────────────┐ │
│  │         Knowledge Graph             │    │       Security Modules       │ │
│  │  (NetworkX + OSINT entities)        │    │      (25+ detectors)         │ │
│  └─────────────────────────────────────┘    └─────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │              Progress / Showcasing Middleware                          │ │
│  │  (WebSocket events → Agent Theater, Screenshot Carousel, Running Log) │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| ScoutAgent (existing) | Web scraping, DOM extraction, screenshot capture | SecurityAgent, VisionAgent |
| SecurityAgent (existing + enhanced) | Security scanning, header analysis, vulnerability detection | JudgeAgent, Security Enterprise |
| VisionAgent (enhanced) | 5-pass VLM analysis, CV temporal comparison | ProgressEmitter, JudgeAgent |
| GraphInvestigator (enhanced) | Knowledge graph construction, entity verification, OSINT integration | OSIntelligenceEngine, JudgeAgent |
| JudgeAgent (enhanced) | Dual-tier verdict generation, site-type-specific scoring | All agents, Progress Emitter |
| OSIntelligenceEngine (new) | 15+ intelligence sources, darknet monitoring, threat feed aggregation | GraphInvestigator, Threat Analyzer |
| ComprehensiveSecurityAudit (new) | 25+ security modules, OWASP compliance, CVSS scoring | SecurityAgent, JudgeAgent |
| ProgressEmitter (new) | Real-time progress events, WebSocket broadcasting | All agents, Frontend Showcase |
| TemporalComputerVision (new) | SSIM, optical flow, screenshot diff, timer fraud detection | VisionAgent |

## Pattern 1: Agent Extension Pattern

**What:** Extend existing agent base classes to add capabilities without refactoring.

**When:** Adding new analysis capabilities to existing agents (Vision 5-pass, OSINT for Graph, Judge dual-tier).

**Example:**
```python
from veritas.agents.vision import VisionAgent

class EnhancedVisionAgent(VisionAgent):
  def __init__(self, nim_client: NimClient):
    super().__init__(nim_client)
    self.passes = ["full_page_scan", "element_interaction", ...]
    self.cv_analyzer = TemporalComputerVision(nim_client)

  async def analyze(self, screenshots: List[str]) -> VisionReport:
    base_report = await super().analyze(screenshots)
    temporal_result = await self.cv_analyzer.compare(screenshots)
    base_report.temporal_analysis = temporal_result
    return base_report
```

## Pattern 2: Tiered Async Execution

**What:** Group async operations by timeout priority to maximize parallelism.

**When:** OSINT checks with varying response times, security module execution.

**Example:**
```python
import asyncio

async def run_osint_checks(domain: str) -> OSINTReport:
  fast_tasks = [self._check_whois(domain), self._check_ssl(domain)]
  fast_results = await asyncio.gather(*[
    asyncio.wait_for(t, 5) for t in fast_tasks
  ], return_exceptions=True)
```

## Anti-Pattern: Synchronous Remote API Calls

**What:** Calling external APIs without async/await.

**Why bad:** Blocks entire audit, violates FastAPI async best practices.

**Instead:** Use aiohttp for all HTTP calls, run in parallel with asyncio.gather.

**Anti-pattern example:**
```python
# BAD - blocks entire request
def check_virus_total(domain):
  response = requests.get(f"https://vt.api/{domain}")
  return response.json()
```

**Correct approach:**
```python
# GOOD - async, non-blocking
async def check_virus_total(domain):
  async with aiohttp.ClientSession() as session:
    async with session.get(f"https://vt.api/{domain}") as resp:
      return await resp.json()
```

## Sources

- VERITAS PROJECT.md (existing agent architecture)
- VERITAS IMPLEMENTATION_PLAN.md (enhancement plans)
- LangGraph documentation (state machine patterns)
- FastAPI best practices (async/await patterns)
