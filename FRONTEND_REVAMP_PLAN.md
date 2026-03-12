# VERITAS FRONTEND REVAMP — MASTER PLAN v2.1

## Direction: Bloomberg War Room — Institutional Intelligence Terminal

**Philosophy**: Veritas is a **real-time forensic intelligence terminal** — not a dashboard, not a marketing site, not a toy. It's the workstation that appears when 5 AI agents are performing a live, adversarial audit of a website. Think Bloomberg Terminal meets a Tier-1 SOC (Security Operations Center). Every panel is live. Every number ticks. Data density is a feature, not a bug. Empty space means broken UI.

**Design DNA:**
- **Bloomberg Terminal** — dense multi-pane layouts, monospace ticking figures, data walls with no wasted pixels, panel chrome with title bars + close/minimize/expand controls, keyboard shortcuts shown inline
- **CrowdStrike Falcon** — threat severity heatmaps, investigation timelines, IOC (Indicator of Compromise) cards, adversary tracking panels
- **Splunk / Elastic SIEM** — structured log streams with timestamp columns, faceted search, live query bars, saved searches, field extraction visualization
- **Linear App** — premium internal-tool feel, functional dark UI, command palette, no marketing fluff, the tool IS the product
- **Figma** — workspace density that never feels cluttered because typographic hierarchy and spacing rhythm are mathematically precise
- **Datadog / Grafana** — metric ticker strips at top, live sparklines embedded in table cells, auto-refresh indicators

**The Three Rules:**
1. If a panel has empty space, it needs more data or it shouldn't exist.
2. If a number isn't ticking during a live audit, something is wrong.
3. If you can't identify the active agent within 200ms of glancing at the screen, the hierarchy failed.

---

## TABLE OF CONTENTS

1. [Psychological Framework](#1-psychological-framework)
2. [Design System Overhaul](#2-design-system-overhaul)
3. [Icon System — Premium Agent Identity](#3-icon-system)
4. [Scene Plan — Page-by-Page Storyboard](#4-scene-plan)
5. [Component Architecture](#5-component-architecture)
6. [Micro-interaction & Motion Catalogue](#6-micro-interaction-catalogue)
7. [Data Density & Interactive Data Strategy](#7-data-density-strategy)
8. [Animation System & Performance Budget](#8-animation-system)
9. [Report Presentation Plan](#9-report-presentation-plan)
10. [Mitigation & Risk Plan](#10-mitigation--risk-plan)
11. [Implementation Phases](#11-implementation-phases)
12. [Current vs. Revamped Comparison](#12-comparison)

---

## 1. PSYCHOLOGICAL FRAMEWORK

### 1.1 Core Cognitive Principles

Every UI decision maps to a known cognitive mechanism — not aesthetic opinion.

| Principle | Source | Application in Veritas |
|---|---|---|
| **Aesthetic-Usability Effect** | Don Norman, 2004 | Premium institutional visuals = perceived trust in the tool's accuracy. Bloomberg feels trustworthy because it looks expensive |
| **Progressive Disclosure** | Nielsen Norman Group | Don't dump 50 findings at once. Reveal in layers: summary panel → detail expansion → raw JSON/evidence drill-down |
| **Hick's Law** | W.E. Hick, 1952 | Reduce decisions per screen. One primary CTA per view. In the War Room, the ONLY focus is the active agent's panel |
| **Miller's Law** | George Miller, 1956 | 7±2 chunks. Each panel shows max 7 visible data rows before requiring scroll or expansion |
| **Von Restorff Effect** | Hedwig von Restorff, 1933 | Critical findings visually BREAK the pattern — not just red text on the same row, but a structural outlier (different background, left-stripe, icon swap) |
| **Zeigarnik Effect** | Bluma Zeigarnik, 1927 | Incomplete tasks are remembered better. The phase progress bar always shows what's pending |
| **Peak-End Rule** | Kahneman & Tversky | People judge by peak and end. Verdict reveal = peak. Report ready notification = end. Both must be polished |
| **Attentional Tunneling** | Wickens, 2005 | In high-data environments, users fixate on one area. Prevent with deliberate chromatic shifts + panel focus changes per agent |
| **Information Foraging Theory** | Pirolli & Card, 1999 | Users follow "information scent." Every data element must telegraph what deeper data lies beneath it (chevron, ellipsis, hover preview) |
| **Arousal Theory (Yerkes-Dodson)** | Yerkes & Dodson, 1908 | Moderate arousal = peak performance. Bloomberg is energizing but not anxious — dense but organized. Same principle here |

### 1.2 Emotional Arc Mapping

The user goes through a predictable emotional journey. The UI matches each phase — but tension comes from **data accumulating**, not from animations. Like watching a Bloomberg terminal during a market crash: the numbers tell the story.

```
COMMAND     → BOOT       → RECON       → INTEL FLOOD     → DELIBERATION → CLASSIFIED
(Landing)    (Connect)    (Scout)       (Sec+Vis+Graph)    (Judge)        (Report)
```

| Emotional Phase | Duration | UI Behavior | Data Density | Color Temperature |
|---|---|---|---|---|
| **COMMAND** | 0–5s | URL input is the only bright element. Terminal cursor blinks. Metric ticker strip shows "IDLE". System feels primed, waiting for orders | Minimal — input + system status | Cold. Near-black (`#080A0F`) with single cyan accent on input border |
| **BOOT** | 5–15s | Initialization sequence streams in the log panel: `[SYS] Connecting... [SYS] Spawning scout_v3... [SYS] Allocating GPU...` Line by line, monospace, timestamped | Rising — log lines streaming, progress bar filling | Cold blue, panels lighting up one at a time |
| **RECON** | 15–60s | Scout is active. Screenshots stream in. First data points populate panels. Metric ticker starts ticking: `PAGES: 3 → 4 → 5`, `LINKS: 12 → 18 → 23` | Medium — all panels have data, numbers ticking | **Scout cyan bleeds across viewport** — background tint shifts, panel borders glow cyan |
| **INTEL FLOOD** | 60–180s | Peak Bloomberg moment. Findings stack in real-time. Security headers table fills row by row. OSINT sidebar populates. Every panel is alive simultaneously | **MAXIMUM** — every panel has live data, nothing is empty | Shifts per agent: **Emerald → Purple → Amber**. The entire screen's color temperature changes with each agent handoff |
| **DELIBERATION** | 180–240s | Judge active. Data flow pauses. Existing findings flash as they're "reviewed". A deliberation indicator pulses. The silence after the storm | High but frozen — data stops arriving, existing data is spotlighted | Deep crimson tint → slow transition toward verdict color |
| **CLASSIFIED** | 240s+ | Verdict stamps into center. Report link appears. All data persists in archival state — accessible, scrollable, no more blinking | Archival — everything persists, nothing ticks | Score-dependent: green debrief / red alert / amber caution |

### 1.3 User Personas & Information Needs

| Persona | What They Want | How We Serve Them |
|---|---|---|
| **Security Engineer** | Raw headers, CVE data, CVSS scores, OWASP mappings, WHOIS dumps, DNS records, certificate chains | Collapsible JSON trees with syntax highlighting (like browser DevTools), filterable log streams, clickable CVE→NVD links, WHOIS as terminal-style output |
| **Product Manager** | "Is this safe? What's wrong? How bad?" | Trust score as dominant visual element, severity summary counts as inline badges, plain English finding summaries at top of every panel |
| **Compliance Officer** | Evidence trail, timestamps, which checks ran, reproducibility | Full structured event timeline with `[HH:MM:SS.ms]` timestamps, per-agent metrics, model version tags, exportable audit trail |
| **Curious User** | "Show me what you found" | Live data feed with educational tooltips, screenshot evidence with bounding-box overlays, interactive exploration |

The UI serves ALL FOUR simultaneously through **layered panel architecture** — dense by default. Every panel is its own depth-drill. Not a mode toggle. The data is always there; premium users see deeper.

---

## 2. DESIGN SYSTEM OVERHAUL

### 2.1 Elevation System (Replaces Flat Glass-Card)

Current problem: everything is `glass-card` = same `rgba(10, 15, 30, 0.7)` + `blur(12px)`. Zero depth. Bloomberg has 5+ visual layers — panels within panels, popovers, drawers, header bars.

**New 5-tier elevation system:**

| Tier | Usage | Background | Border | Shadow | Blur | z-index |
|---|---|---|---|---|---|---|
| **T1 — SUBSTRATE** | Page background, section separators | `#080A0F` solid | None | None | None | 0 |
| **T2 — SURFACE** | Panel bodies, sidebar regions, data tables | `rgba(10, 15, 30, 0.85)` | `0.5px rgba(255,255,255,0.06)` | None | `blur(4px)` | 10 |
| **T3 — CARD** | Finding cards, agent tiles, metric blocks, data rows on hover | `rgba(15, 20, 40, 0.9)` | `1px rgba(255,255,255,0.10)` | `0 2px 8px rgba(0,0,0,0.3)` | `blur(8px)` | 20 |
| **T4 — POPUP** | Tooltips, expanded finding detail, JSON tree popovers, right-click menus | `rgba(20, 25, 50, 0.95)` | `1px rgba(255,255,255,0.15)` | `0 4px 16px rgba(0,0,0,0.5)` | `blur(16px)` | 40 |
| **T5 — OVERLAY** | Verdict reveal, fullscreen screenshot, critical alerts | `rgba(8, 10, 20, 0.98)` | `2px agent-color` | `0 8px 32px rgba(0,0,0,0.7)` | `blur(24px)` | 50 |

**Panel Chrome (Bloomberg-style):**
Every panel at T2+ gets a **title bar** — a 28px-tall header strip:
```
┌─ SECURITY FINDINGS ──────────────── [3] ── ⊡ ⊟ ──┐
│                                                     │
│  Panel content here...                              │
│                                                     │
└─────────────────────────────────────────────────────┘
```
- Title: ALL CAPS, `font-size: 10px`, `letter-spacing: 0.1em`, `font-family: JetBrains Mono`, `color: rgba(255,255,255,0.5)`
- Count badge: `[3]` in the title bar showing item count
- Controls: Minimize `⊟` / Maximize `⊡` (optional per panel, functional on audit page)
- Left accent: 2px vertical line in the panel's contextual color
- Background: Slightly darker than panel body (`rgba(5, 8, 18, 0.9)`)

### 2.2 Color System — Aggressive Chromatic Shift

**HARD chromatic shift.** Not subtle tinting — the entire viewport's atmosphere changes when agents switch. Like a Bloomberg terminal switching between asset classes where the whole screen feels different.

**Agent Color Palette:**

| Agent | Primary | Glow (`box-shadow`) | Background Tint (`radial-gradient` overlay) | Border Accent | Panel Title Accent | Text Highlight |
|---|---|---|---|---|---|---|
| **Scout** | `#06D6A0` (Cyan-teal) | `0 0 40px rgba(6,214,160,0.3)` | `radial-gradient(ellipse at 30% 50%, rgba(6,214,160,0.08), transparent 60%)` | `rgba(6,214,160,0.4)` | `#06D6A0` | `rgba(6,214,160,0.9)` |
| **Security** | `#10B981` (Emerald) | `0 0 40px rgba(16,185,129,0.3)` | `radial-gradient(ellipse at 70% 30%, rgba(16,185,129,0.08), transparent 60%)` | `rgba(16,185,129,0.4)` | `#10B981` | `rgba(16,185,129,0.9)` |
| **Vision** | `#8B5CF6` (Purple) | `0 0 40px rgba(139,92,246,0.3)` | `radial-gradient(ellipse at 50% 70%, rgba(139,92,246,0.08), transparent 60%)` | `rgba(139,92,246,0.4)` | `#8B5CF6` | `rgba(139,92,246,0.9)` |
| **Graph** | `#F59E0B` (Amber) | `0 0 40px rgba(245,158,11,0.3)` | `radial-gradient(ellipse at 60% 40%, rgba(245,158,11,0.08), transparent 60%)` | `rgba(245,158,11,0.4)` | `#F59E0B` | `rgba(245,158,11,0.9)` |
| **Judge** | `#EF4444` → verdict color | `0 0 40px rgba(239,68,68,0.3)` | `radial-gradient(ellipse at 50% 50%, rgba(239,68,68,0.08), transparent 60%)` | `rgba(239,68,68,0.4)` | `#EF4444` | `rgba(239,68,68,0.9)` |

**Chromatic Shift Mechanics:**
- A `<ChromaticProvider>` wraps the audit page
- CSS custom properties `--agent-primary`, `--agent-glow`, `--agent-tint`, `--agent-border` are set on `<body>` during audit
- Transition: `400ms cubic-bezier(0.4, 0, 0.2, 1)` — fast enough to feel responsive, slow enough to feel atmospheric
- **What changes during shift:**
  1. Full-page radial gradient overlay (the "atmosphere") — AGGRESSIVE, clearly visible
  2. Active agent's panel border brightens to 100% opacity (from 40%)
  3. All other panels' borders dim to 6% opacity
  4. The metric ticker strip at the top gets an underline glow in agent color
  5. The log terminal's prompt character changes to agent color: `scout>`, `security>`, `vision>`, etc.
  6. Particle field (if enabled) shifts to agent color
  7. The panel title bar accent strips shift to agent color on the active panel
- **prefers-reduced-motion**: Disables transitions (instant swap), reduces glow intensity by 70%

### 2.3 Typography Hierarchy

**Two fonts. No exceptions.**

| Element | Font | Weight | Size | Tracking | Use Case |
|---|---|---|---|---|---|
| **Page Title** | Inter | 700 (Bold) | 28px | `-0.02em` | "AUDIT: example.com", "REPORT: example.com" |
| **Panel Title** | JetBrains Mono | 600 (SemiBold) | 10px | `0.12em` | ALL CAPS panel headers: "SECURITY FINDINGS", "EVENT LOG" |
| **Section Header** | Inter | 600 (SemiBold) | 16px | `-0.01em` | Report section titles: "Signal Analysis", "Dark Patterns" |
| **Body Text** | Inter | 400 (Regular) | 13px | `0` | Finding descriptions, narrative content |
| **Data Label** | JetBrains Mono | 400 (Regular) | 11px | `0.04em` | "TRUST SCORE", "SEVERITY", "RESPONSE TIME" |
| **Data Value** | JetBrains Mono | 700 (Bold) | 14–24px | `0` | `73/100`, `4.2s`, `12 findings`, ticking numbers |
| **Ticker Number** | JetBrains Mono | 700 (Bold) | 12px | `0.02em` | Numbers in the metric ticker strip that count up during audit |
| **Log Entry** | JetBrains Mono | 400 (Regular) | 11px | `0` | `[14:23:07.332] [SCOUT] Navigating to /about...` |
| **Badge / Tag** | JetBrains Mono | 500 (Medium) | 9px | `0.08em` | `CRITICAL`, `HIGH`, `CVE-2024-1234`, `PASS`, `FAIL` |
| **Tooltip** | Inter | 400 (Regular) | 12px | `0` | Hover explanations, contextual help |

**Key rule**: If it's a number, a timestamp, a score, a code snippet, a status badge, or a log entry — it's **JetBrains Mono**. Everything else is **Inter**. No ambiguity.

### 2.4 Severity Visual Language

**Not just color.** Bloomberg uses color + icon + position + cell formatting. We use:

| Severity | Color | Icon | Background Strip | Badge Style | Row Treatment |
|---|---|---|---|---|---|
| **CRITICAL** | `#EF4444` (Red) | `ShieldAlert` (filled) | 3px left-stripe, red | Solid red bg, white text, `CRITICAL` | Slightly brighter row bg, left-stripe visible at rest |
| **HIGH** | `#F59E0B` (Amber) | `AlertTriangle` | 3px left-stripe, amber | Solid amber bg, black text, `HIGH` | Subtle amber tint on row bg |
| **MEDIUM** | `#3B82F6` (Blue) | `Info` (circle) | 2px left-stripe, blue | Outlined blue border, blue text, `MEDIUM` | Default row bg |
| **LOW** | `#6B7280` (Gray) | `Minus` (circle) | 1px left-stripe, gray | Muted gray bg, gray text, `LOW` | Default row bg |
| **PASS** | `#10B981` (Green) | `CheckCircle2` | 2px left-stripe, green | Outlined green, `PASS` | Default row bg |

**Structural outlier for CRITICAL (Von Restorff):** Critical findings get a visually different container — not just a red stripe but a slightly raised card treatment (T3 instead of inline row), making them physically stand out from the data stream.

---

## 3. ICON SYSTEM — PREMIUM AGENT IDENTITY

**The current problem**: Agents use emojis (`🔍`, `🛡️`, `👁️`). This screams toy. Premium tools have a consistent, mature icon system.

### 3.1 Icon Treatment

**Every icon in the system follows these rules:**

| Property | Value | Rationale |
|---|---|---|
| **Stroke width** | 1.5px | Consistent with Linear, Figma, Vercel — modern SaaS standard |
| **Line cap** | Round | Softer, more premium than butt caps |
| **Line join** | Round | Consistent with caps |
| **Size — inline** | 14px | In text, badges, table cells |
| **Size — panel title** | 16px | In panel title bars |
| **Size — agent tile** | 20px | In agent identity cards |
| **Size — hero** | 28px | Landing page feature icons, report section icons |
| **Container** | 32px rounded-square (`border-radius: 8px`) | Every agent icon sits inside a subtle container with the agent's color as bg at 10% opacity and border at 20% opacity |
| **Icon library** | Lucide React (exclusively) | One library. No mixing. No custom SVGs except the Veritas logo |

### 3.2 Agent Icon Assignments

| Agent | Icon | Container BG | Container Border | Rationale |
|---|---|---|---|---|
| **Scout** | `Radar` | `rgba(6,214,160,0.10)` | `rgba(6,214,160,0.20)` | Radar = systematic scanning, discovery |
| **Security** | `ShieldCheck` | `rgba(16,185,129,0.10)` | `rgba(16,185,129,0.20)` | Shield = defensive analysis, protection check |
| **Vision** | `ScanEye` | `rgba(139,92,246,0.10)` | `rgba(139,92,246,0.20)` | Eye with scan lines = visual + screenshot analysis |
| **Graph** | `Network` | `rgba(245,158,11,0.10)` | `rgba(245,158,11,0.20)` | Network nodes = OSINT, entity graph, connections |
| **Judge** | `Scale` | `rgba(239,68,68,0.10)` | `rgba(239,68,68,0.20)` | Justice scale = deliberation, final verdict |

### 3.3 Icon States

| State | Treatment |
|---|---|
| **Idle** | Container bg at 10%, icon color at 40% opacity |
| **Active** | Container bg at 20%, icon color at 100%, subtle glow (`0 0 12px agent-color at 0.2`) |
| **Complete** | Container bg at 10%, icon color at 60%, small `CheckCircle2` badge (8px) overlaid at bottom-right |
| **Error** | Container bg shifts to `rgba(239,68,68,0.10)`, icon swaps to `AlertCircle` in red |
| **Hover** | Container bg brightens to 15%, border brightens to 30%, scale(1.05) with 150ms ease-out |

### 3.4 System Icons (Non-Agent)

| Context | Icons Used | Treatment |
|---|---|---|
| **Severity** | `ShieldAlert`, `AlertTriangle`, `Info`, `Minus`, `CheckCircle2` | Inline 14px, colored per severity, no container |
| **Navigation** | `ChevronRight`, `ChevronDown`, `ExternalLink`, `Copy`, `Download`, `Search`, `Filter`, `X` | Inline 14px, `rgba(255,255,255,0.4)`, brightens on hover |
| **Panel controls** | `Minimize2`, `Maximize2`, `GripVertical` | Inline 12px, `rgba(255,255,255,0.3)` — Bloomberg chrome style |
| **Status indicators** | `Loader2` (spinning), `Check`, `Clock`, `Wifi`, `WifiOff` | Inline 12px, contextual color |
| **Data types** | `Globe` (URL), `Lock` (SSL), `Server` (hosting), `FileJson` (data), `Terminal` (logs) | Inline 14px, muted white |

---

## 4. SCENE PLAN — PAGE-BY-PAGE STORYBOARD

### Scene 1: COMMAND CENTER (Landing Page)

**Kill the marketing site feel.** This isn't a product page — it's the entry screen of a professional tool. Think: Linear's login, Figma's file browser, Vercel's dashboard. Clean. Dense. Functional. The URL input IS the hero.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│  ◉ VERITAS   ·   v3.2.1   ·   [5 agents online]   ·   [GPU: NVIDIA ████ OK]  │  ← Status bar
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                                                                                  │
│                           VERITAS INTELLIGENCE ENGINE                             │
│                        Real-time website forensic analysis                        │
│                                                                                  │
│               ┌──────────────────────────────────────────────┐                   │
│               │  https://                                    │  [ANALYZE →]      │  ← URL Input (hero)
│               └──────────────────────────────────────────────┘                   │
│                                                                                  │
│               ANALYSIS TIER ·  ◉ Quick  ○ Standard  ○ Deep  ○ Paranoid          │  ← Tier selector (radio)
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─ SYSTEM CAPABILITIES ──────┐  ┌─ AGENT STATUS ────────────┐  ┌─ STATS ───┐  │
│  │  ☐ SSL/TLS Analysis        │  │  ◉ Scout    ── READY ──   │  │ Audits    │  │
│  │  ☐ OSINT Investigation     │  │  ◉ Security ── READY ──   │  │  12,847   │  │
│  │  ☐ Dark Pattern Detection  │  │  ◉ Vision   ── READY ──   │  │ Threats   │  │
│  │  ☐ Screenshot Analysis     │  │  ◉ Graph    ── READY ──   │  │   3,291   │  │
│  │  ☐ JavaScript Audit        │  │  ◉ Judge    ── READY ──   │  │ Avg Time  │  │
│  │  ☐ Redirect Chain Trace    │  │                            │  │   47.3s   │  │
│  │  ☐ Form Validation         │  │  GPU: NVIDIA RTX ████     │  │ Uptime    │  │
│  │  ☐ Entity Graph Building   │  │  NIM: Connected (40 RPM)  │  │  99.7%    │  │
│  └────────────────────────────┘  └────────────────────────────┘  └───────────┘  │
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  ┌─ RECENT AUDITS ──────────────────────────────────────────────────── [↗] ──┐  │
│  │  TIME        TARGET               SCORE  TIER    FINDINGS  STATUS         │  │
│  │  14:23:07    example.com          73     Deep    12        ■ Complete     │  │
│  │  14:18:42    suspicious-shop.io   23     Para    47        ■ Complete     │  │
│  │  14:12:01    my-bank.com          91     Quick   3         ■ Complete     │  │
│  │  13:58:33    phishing-test.net    8      Deep    89        ■ Complete     │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│  ┌─ HOW IT WORKS ────────────────────────────────────────────────────────────┐  │
│  │  1. SUBMIT → 2. SCOUT → 3. ANALYZE → 4. INVESTIGATE → 5. JUDGE → REPORT │  │
│  │  Dense single-line timeline with agent icons at each step                 │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  © 2025 Veritas Intelligence · v3.2.1 · MIT License                             │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Scene 1 — Key Design Decisions:**

| Element | Old (v1) | New Bloomberg Treatment |
|---|---|---|
| **Hero area** | Giant "INVESTIGATE ANYTHING" text + animated ParticleField + cyan gradient swoosh | Clean tool header. System name + tagline. URL input is visually dominant (thicker border, glow on focus). No particle field on landing |
| **Tier selector** | 4 flashy cards with gradients and descriptions expanding on hover | Inline radio group below the input. One line. Bloomberg Terminal doesn't have flashy cards for options — it has compact selectors |
| **Capabilities** | "SignalShowcase" — animated carousel of cards sliding in with motion | Static checklist grid. Capabilities are facts, not a slideshow. Monospace labels, checkmark icons, 3-column compact grid |
| **Agent status** | Not shown on landing | Bloomberg-style status panel showing each agent's readiness, GPU status, NIM connection. Makes it feel like a live system, not a brochure |
| **Stats** | Not shown on landing | Compact metrics block: total audits, threats detected, avg time, uptime. Monospace ticking numbers. Institutional credibility |
| **Recent audits** | Not shown on landing | Table (not cards) of recent audits with timestamp, target, score, tier, finding count, status. Bloomberg = tables, not cards |
| **How it works** | 6 floating cards with step numbers, icons, descriptions | Single-line dense timeline. `1. SUBMIT → 2. SCOUT → ... → REPORT`. Pipeline visualization, not a card layout |
| **Footer** | Not present / scattered links | Minimal single-line footer with version, license. Internal tool feel |
| **Particle field** | Full-page canvas particle animation on landing | **REMOVED from landing**. Landing is clean and functional. Particle field reserved for audit page only (as ambient texture) |

**Landing page must feel like**: Opening Datadog for the first time. You see a professional tool. The input is obvious. The system status tells you it's live. Recent audits show this tool is actively used. No marketing. No "Learn More" buttons. No feature carousels.

### Scene 2: WAR ROOM (Audit Page — Live)

**The heart of Veritas.** This is where the Bloomberg Terminal density peaks. Four distinct panels + a metric ticker + a log stream. All live during the audit. Each panel has chrome (title bar, controls, item count).

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ◉ VERITAS  ·  AUDITING: suspicious-shop.io  ·  TIER: Deep  ·  ELAPSED: 01:23  ·  ████▒▒ 67%    │ ← Header bar
├───────────────────────────────────────────────────────────────────────────────────────────────────┤
│ PAGES: 7  ·  LINKS: 34  ·  FINDINGS: 12  ·  SCREENSHOTS: 4  ·  HEADERS: ✓  ·  SSL: ✓  ·  DNS: ✓│ ← Metric ticker
├────────────────────┬───────────────────────────────────────────────────┬───────────────────────────┤
│ ─ AGENTS ────── ⊡  │ ─ ACTIVE INTEL ─────────────────────────── ⊡ ⊟  │ ─ EVIDENCE ──────── ⊡ ⊟  │
│                    │                                                   │                           │
│  ◉ Scout    ████   │  ┌─ SECURITY AGENT ACTIVE ───────────────────┐  │  ┌─ SCREENSHOTS [4] ───┐  │
│     12 pages       │  │                                            │  │  │  [img] /home         │  │
│     34 links       │  │  Currently analyzing: HTTP headers         │  │  │  [img] /about        │  │
│     COMPLETE       │  │                                            │  │  │  [img] /checkout     │  │
│                    │  │  ┌─ FINDINGS STREAM ─────────── [12] ──┐  │  │  │  [img] /login        │  │
│  ◉ Security ███▒   │  │  │ ▌CRI Missing CSP header             │  │  │  └──────────────────────┘  │
│     8 headers      │  │  │ ▌HIG X-Frame-Options absent         │  │  │                           │
│     3 findings     │  │  │ ▌MED No HSTS preload                │  │  │  ┌─ METRICS ──────────┐  │
│     RUNNING...     │  │  │ ▌LOW Referrer-Policy permissive     │  │  │  │ Trust Score  --     │  │
│                    │  │  │ ▌MED Insecure cookie flags           │  │  │  │ Risk Level   --     │  │
│  ○ Vision   ▒▒▒▒   │  │  └────────────────────────────────────┘  │  │  │ Pages        7      │  │
│     Waiting...     │  │                                            │  │  │ Links        34     │  │
│                    │  │  ┌─ RAW DATA ─────────────────────────┐  │  │  │ Findings     12     │  │
│  ○ Graph    ▒▒▒▒   │  │  │ > GET / HTTP/1.1                   │  │  │  │ Duration     01:23  │  │
│     Waiting...     │  │  │ < 200 OK                            │  │  │  └──────────────────────┘  │
│                    │  │  │ < content-security-policy: (none)   │  │  │                           │
│  ○ Judge    ▒▒▒▒   │  │  │ < x-frame-options: (none)          │  │  │  ┌─ OSINT ────────────┐  │
│     Waiting...     │  │  │ < strict-transport: (none)          │  │  │  │ WHOIS: Private      │  │
│                    │  │  └────────────────────────────────────┘  │  │  │ Registrar: GoDaddy  │  │
│                    │  └────────────────────────────────────────────┘  │  │ Created: 2024-01-15 │  │
│                    │                                                   │  │ Hosting: CloudFlare │  │
│                    │                                                   │  └──────────────────────┘  │
├────────────────────┴───────────────────────────────────────────────────┴───────────────────────────┤
│ ─ EVENT LOG ──────────────────────────────── [Filter: ▼ All] [Search: ___________] ── ⊡ ⊟ ── [↗]  │
│ [14:23:07.332] [SCOUT]    Navigating to /checkout...                                               │
│ [14:23:08.119] [SCOUT]    Screenshot captured: /checkout (1920x1080)                               │
│ [14:23:08.445] [SECURITY] Analyzing HTTP headers for /checkout...                                  │
│ [14:23:09.012] [SECURITY] ▌CRI Missing Content-Security-Policy header                             │
│ [14:23:09.334] [SECURITY] ▌HIG X-Frame-Options header absent — clickjacking risk                  │
│ security>_                                                                                         │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Scene 2 — Layout Specification:**

| Zone | Width | Content | Panel Chrome |
|---|---|---|---|
| **Header Bar** | 100% × 36px | Logo, target URL, tier badge, elapsed timer (ticking), progress bar | Fixed top, T2 surface, border-bottom 1px |
| **Metric Ticker** | 100% × 28px | Horizontal strip of key metrics, monospace, separated by `·`. Numbers tick up in real-time during audit | Fixed below header, T1 substrate with subtle top-border. JetBrains Mono 11px |
| **Agent Stack** | 200px left column | Vertical list of 5 agent tiles. Each tile: icon in container + name + mini progress bar + key stat + status badge | T2 surface, resizable (drag handle) |
| **Active Intel** | Flex center (fills remaining) | The MAIN content area. Content changes based on active agent. Shows: agent banner, findings stream, raw data preview | T2 surface with T3 cards inside |
| **Evidence Sidebar** | 280px right column | Stacked panels (not tabbed): Screenshots, Metrics, OSINT. Each with own title bar | T2 surface, resizable, scroll independent |
| **Event Log** | 100% × 180px bottom | Full-width structured log. Timestamps + agent tags + messages. Filter dropdown, search input, copy button, expand button | T1 substrate (terminal black `#0D0D0D`), JetBrains Mono 11px throughout |

**Scene 2 — Active Intel Zone (Per-Agent Content):**

The center panel is the **Bloomberg main stage** — its content rotates based on which agent is active:

| Agent Active | Main Stage Shows |
|---|---|
| **Scout** | Page-by-page navigation log with thumbnail previews. Link count ticking. URL tree building in real-time (collapsible). Redirect chain visualization |
| **Security** | HTTP header analysis table (header name → value → verdict). SSL certificate detail panel. Cookie analysis grid. Each finding as a structured row with severity-stripe |
| **Vision** | Screenshot grid (2×2 during audit, expandable). Dark pattern detection overlays drawn on screenshots in real-time. Form analysis results as structured cards |
| **Graph** | Entity relationship mini-graph (WHOIS → Registrar → IP → Hosting). OSINT timeline. DNS record table. Certificate transparency log entries |
| **Judge** | Deliberation view: summary of all agent findings in a structured table. Each row is a finding being "weighed". Verdict building animation. Score counter |

**Scene 2 — Finding Stream Format:**

Findings appear in the Active Intel zone as structured rows, NOT as chat messages:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ▌CRI  ShieldAlert  Missing Content-Security-Policy header    [EXPAND ▾] │
│        Allows inline script execution. XSS attack surface.              │
│        Source: security_agent · Check: http_headers · GET /             │
├──────────────────────────────────────────────────────────────────────────┤
│ ▌HIG  AlertTriang  X-Frame-Options header absent             [EXPAND ▾] │
│        Clickjacking risk on all pages.                                  │
│        Source: security_agent · Check: http_headers · GET /             │
└──────────────────────────────────────────────────────────────────────────┘
```

Each finding row:
- 3px left-stripe in severity color
- Severity badge in panel title style (`CRI`, `HIG`, `MED`, `LOW`)
- Icon (from severity icon set) in severity color
- One-line title
- One-line plain-English description (collapsed by default in dense mode)
- Source metadata line: agent, check type, request
- `[EXPAND ▾]` reveals: full detail, evidence links, raw data, remediation advice

**Scene 2 — Evidence Sidebar (Stacked, Not Tabbed):**

The current evidence panel uses TABS. Tabs hide data. Bloomberg shows all data simultaneously in stacked panels.

```
┌─ SCREENSHOTS ──────────────────── [4] ──┐
│  ┌───────┐ ┌───────┐ ┌───────┐          │  ← 80px thumbnails, click to expand
│  │ /home │ │/about │ │/check │ ···      │
│  └───────┘ └───────┘ └───────┘          │
├─ METRICS ──────────────────────── [⟳] ──┤
│  Trust Score      ██████████▒   73/100   │  ← Inline progress bars
│  Risk Level       ████████████  HIGH     │
│  Pages Analyzed   7                      │
│  Links Discovered 34                     │
│  Unique Findings  12                     │
│  Time Elapsed     01:23.4               │
├─ OSINT ────────────────────────── [↗] ──┤
│  Domain:     suspicious-shop.io          │
│  Registrar:  GoDaddy LLC                 │
│  Created:    2024-01-15                  │
│  WHOIS:      Privacy Protected           │
│  Hosting:    Cloudflare, Inc             │
│  SSL Issuer: Let's Encrypt               │
│  IP:         104.21.45.67                │
│  ASN:        AS13335 (Cloudflare)        │
└──────────────────────────────────────────┘
```

**Scene 2 — Event Log (Bloomberg Terminal Bar):**

The bottom log is the "Bloomberg terminal" — monospace, dense, structured.

| Feature | Specification |
|---|---|
| **Font** | JetBrains Mono 11px, `line-height: 1.6` |
| **Background** | `#0D0D0D` (terminal black, darker than page bg) |
| **Timestamp** | `[HH:MM:SS.mmm]` in `rgba(255,255,255,0.3)` — always visible, left-aligned |
| **Agent tag** | `[SCOUT]`, `[SECURITY]`, etc. — in agent color, fixed width 12ch |
| **Severity inline** | Finding entries show `▌CRI`, `▌HIG`, etc. in severity color before the message |
| **Agent prompt** | Bottom line shows `agent_name>_` with blinking cursor in agent color |
| **Filter** | Dropdown: All / Scout / Security / Vision / Graph / Judge / Errors only |
| **Search** | Inline text search with highlight-on-match. Case-insensitive string match |
| **Controls** | Copy all (clipboard), Expand (full-screen overlay), Clear |
| **Scroll** | Auto-scrolls to bottom. Scrolling up pauses auto-scroll. "↓ New entries" badge appears when paused |
| **Max visible** | 200 entries visible (virtualized). Older entries accessible via scroll. No truncation |

### Scene 2b: VERDICT REVEAL (Post-Audit Overlay — 3 seconds)

The verdict reveal is a 3-second overlay sequence. Fast but impactful.

```
T=0.0s  ────  Dim: All panels dim to 30% opacity. Log pauses
T=0.5s  ────  Center stage: "ANALYSIS COMPLETE" in JetBrains Mono, 16px, fade-in
T=1.0s  ────  Score counter: "0" → final score. JetBrains Mono Bold, 72px. Rapid count-up
T=2.0s  ────  Classification stamp: "SUSPICIOUS" / "SAFE" / "DANGEROUS". Color-coded badge, scale-in
T=2.5s  ────  CTA: "VIEW FULL REPORT →" button fades in below
T=3.0s  ────  Panels restore to full opacity. Overlay becomes dismissible (click/ESC)
```

- **Click anywhere** or **ESC** dismisses the overlay at any point
- Once dismissed, the audit page remains in "archival" state — all data visible, nothing ticking
- Verdict classification colors: SAFE = `#10B981`, CAUTION = `#F59E0B`, SUSPICIOUS = `#EF4444`, DANGEROUS = `#DC2626` with pulsing glow
- No confetti. No particles. Clean, institutional reveal.

### Scene 3: INTELLIGENCE REPORT (Report Page)

The report is a **scrollable, section-navigated intelligence dossier**. Not a stack of cards — a structured document with left-rail navigation, like reading a Bloomberg research report or a CrowdStrike threat analysis.

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ◉ VERITAS  ·  REPORT: suspicious-shop.io  ·  Score: 23/100 SUSPICIOUS  ·  [PDF ↓] [JSON ↓]      │
├───────────────┬───────────────────────────────────────────────────────────────────────────────────┤
│               │                                                                                   │
│  SECTIONS     │  ┌─ EXECUTIVE SUMMARY ───────────────────────────────────────────────────────┐  │
│               │  │                                                                            │  │
│  ● Overview   │  │  Target: suspicious-shop.io                                                │  │
│  ○ Signals    │  │  Trust Score: ████████▒▒ 23/100 — SUSPICIOUS                              │  │
│  ○ Dark Pat.  │  │  Classification: High-risk e-commerce site with multiple deceptive          │  │
│  ○ Security   │  │  practices and missing security controls.                                  │  │
│  ○ Entity     │  │                                                                            │  │
│  ○ Evidence   │  │  ┌───────────┬───────────┬───────────┬───────────┐                        │  │
│  ○ Recommend  │  │  │ CRITICAL  │ HIGH      │ MEDIUM    │ LOW       │                        │  │
│  ○ Metadata   │  │  │     4     │     8     │    12     │     3     │                        │  │
│  ○ Raw Data   │  │  └───────────┴───────────┴───────────┴───────────┘                        │  │
│               │  │                                                                            │  │
│               │  │  Key Findings:                                                             │  │
│               │  │  • 4 critical security misconfigurations                                   │  │
│               │  │  • 12 dark patterns detected across checkout flow                          │  │
│               │  │  • WHOIS privacy shield on 30-day-old domain                              │  │
│               │  │  • Urgency manipulation on 100% of product pages                          │  │
│               │  └────────────────────────────────────────────────────────────────────────────┘  │
│               │                                                                                   │
│               │  ┌─ SIGNAL ANALYSIS ──────────────────────────────── 4 of 6 below threshold ─┐  │
│               │  │                                                                            │  │
│               │  │  Signal          Score    Threshold    Status    Detail                    │  │
│               │  │  ─────────────────────────────────────────────────────────                 │  │
│               │  │  SSL/TLS         42       70           ▌FAIL     Weak cipher suite          │  │
│               │  │  HTTP Security   18       60           ▌FAIL     Missing 4 critical headers│  │
│               │  │  Content Trust   31       50           ▌FAIL     12 dark patterns detected │  │
│               │  │  Domain Intel    25       50           ▌FAIL     30-day-old, privacy WHOIS │  │
│               │  │  Redirect Chain  89       70           ▌PASS     Clean, no suspicious hops │  │
│               │  │  Form Safety     55       50           ▌PASS     Standard forms detected   │  │
│               │  └────────────────────────────────────────────────────────────────────────────┘  │
│               │                                                                                   │
│               │  ... (more sections scroll below) ...                                            │
│               │                                                                                   │
├───────────────┴───────────────────────────────────────────────────────────────────────────────────┤
│  Audit ID: abc123 · Duration: 3m 47s · Agents: 5/5 · Model: NIM v3.2 · Generated: 2025-01-15    │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Scene 3 — Section Navigation (Left Rail):**

| Feature | Spec |
|---|---|
| **Width** | 160px fixed, sticky on scroll |
| **Items** | Section names, 13px Inter Regular, `rgba(255,255,255,0.4)` |
| **Active indicator** | Filled circle `●` + white text. Scrollspy tracks current section |
| **Click behavior** | Smooth scroll to section. URL hash updates |
| **Mobile** | Collapses to horizontal pill strip at top (same as current behavior) |

**Scene 3 — Report Sections (Narrative Structure):**

The report follows a **6-act intelligence narrative**:

1. **EXECUTIVE SUMMARY** — Verdict, score bar, severity breakdown grid, key findings bullets. "What happened in 30 seconds."
2. **SIGNAL ANALYSIS** — Table of all signals with score vs. threshold, pass/fail status, one-line detail. "Where the numbers came from."
3. **DARK PATTERNS & DECEPTION** — Grid of detected patterns with screenshot evidence links, category tags, frequency counts. "What manipulations we found."
4. **SECURITY POSTURE** — Matrix of security checks (headers, SSL, cookies, CORS, etc.) as a pass/fail grid with expandable details. "How secure the infrastructure is."
5. **ENTITY INTELLIGENCE** — WHOIS data, DNS records, hosting info, certificate chain, domain age timeline, IP geolocation. "Who runs this and where." Data displayed as structured terminal-style blocks.
6. **EVIDENCE GALLERY** — All screenshots with bounding-box overlays for findings. Click any finding anywhere in the report → scrolls here and highlights the relevant screenshot.
7. **RECOMMENDATIONS** — Prioritized action items grouped by severity. Each recommendation links back to the finding that generated it.
8. **AUDIT METADATA** — Technical details: agent versions, model used, timing per agent, event count, tier settings. For compliance officers.
9. **RAW DATA** *(expandable)* — Full JSON audit payload in a syntax-highlighted, collapsible tree viewer. Copy button. Download as `.json`. "For engineers who want everything."

Every section heading includes a one-line summary visible without scrolling into the section:
- *"Signal Analysis — 4 of 6 signals below threshold"*
- *"Dark Patterns — 12 patterns detected across 3 categories"*
- *"Security Posture — Missing 4 critical HTTP security headers"*

### Scene 4: AUDIT HISTORY (History Page)

Dense table view — Bloomberg-style. Not a card grid.

```
┌─ AUDIT HISTORY ──────────────────────────────────────────────────── [Filter ▾] [Search] ─┐
│                                                                                           │
│  TIME              TARGET                    SCORE    TIER      FINDINGS    DURATION       │
│  ────────────────────────────────────────────────────────────────────────────────────      │
│  2025-01-15 14:23  suspicious-shop.io         23     Deep         47       3m 47s         │
│  2025-01-15 14:18  example.com                73     Standard     12       1m 23s         │
│  2025-01-15 14:12  my-bank.com                91     Quick         3       0m 34s         │
│  2025-01-15 13:58  phishing-test.net           8     Deep         89       4m 12s ■       │
│  ...                                                                                      │
│                                                                                           │
│  Showing 1–25 of 142 audits                                            [← 1 2 3 ... →]   │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

- Score column: inline color-coded bar + number
- Row hover: subtle bg change (T3 elevation), click to navigate to report
- Sortable columns (click header)
- Filter: by tier, by score range, by date range
- Search: target URL text search

### Scene 5: COMPARISON VIEW (Compare Page — Future Scope)

Side-by-side two-audit comparison. Out of scope for V1 revamp but wireframed for awareness:
- Two report columns side by side
- Delta highlights: green (improved), red (worsened), gray (unchanged)
- Score trend line if same target audited multiple times

---

## 5. COMPONENT ARCHITECTURE

### 5.1 New & Redesigned Components

| # | Component | Status | File | Purpose |
|---|---|---|---|---|
| 1 | `MetricTicker` | **NEW** | `components/audit/MetricTicker.tsx` | Horizontal strip of live-updating monospace metrics. Ticks during audit |
| 2 | `PanelChrome` | **NEW** | `components/layout/PanelChrome.tsx` | Reusable panel wrapper: title bar + controls + left accent. Used by every panel |
| 3 | `AgentTile` | **REDESIGN** | `components/audit/AgentTile.tsx` | Replaces `AgentCard`. Compact: icon-in-container + name + progress bar + stat + status |
| 4 | `ActiveIntel` | **NEW** | `components/audit/ActiveIntel.tsx` | Center content panel that swaps based on active agent. Renders agent-specific data views |
| 5 | `FindingRow` | **NEW** | `components/audit/FindingRow.tsx` | Structured finding display: severity stripe + icon + title + detail + expand |
| 6 | `DataFeed` | **REDESIGN** | `components/audit/DataFeed.tsx` | Replaces `NarrativeFeed`. Structured typed entries, not chat bubbles |
| 7 | `EventLog` | **REDESIGN** | `components/audit/EventLog.tsx` | Replaces `ForensicLog`. Full terminal: timestamps, agent tags, filter, search, copy |
| 8 | `EvidenceStack` | **REDESIGN** | `components/audit/EvidenceStack.tsx` | Replaces tabbed `EvidencePanel`. Stacked panels: Screenshots + Metrics + OSINT |
| 9 | `VerdictReveal` | **REDESIGN** | `components/audit/VerdictReveal.tsx` | 3-second overlay: dim → count-up → classification → CTA. No confetti |
| 10 | `SectionNav` | **NEW** | `components/report/SectionNav.tsx` | Left-rail sticky section navigation with scrollspy |
| 11 | `SignalTable` | **REDESIGN** | `components/report/SignalTable.tsx` | Table-based signal analysis (not cards). Score vs. threshold columns |
| 12 | `SecurityMatrix` | **REDESIGN** | `components/report/SecurityMatrix.tsx` | Pass/fail grid of security checks. Expandable rows |
| 13 | `JsonTreeViewer` | **NEW** | `components/data-display/JsonTreeViewer.tsx` | Syntax-highlighted collapsible JSON tree. Like browser DevTools |
| 14 | `TerminalBlock` | **NEW** | `components/data-display/TerminalBlock.tsx` | Terminal-style output block for WHOIS, DNS, cert chain. Monospace, copyable |
| 15 | `DataTable` | **NEW** | `components/data-display/DataTable.tsx` | Sortable, filterable table for structured data (DNS records, headers, etc.) |
| 16 | `ChromaticProvider` | **NEW** | `components/providers/ChromaticProvider.tsx` | Context provider + CSS custom property manager for agent color shift |
| 17 | `AgentIcon` | **NEW** | `components/ui/AgentIcon.tsx` | Standardized agent icon renderer: Lucide icon + container + state (idle/active/complete/error) |
| 18 | `SeverityBadge` | **NEW** | `components/ui/SeverityBadge.tsx` | Consistent severity badge: color + icon + label. Used everywhere severity appears |
| 19 | `InlineSparkline` | **NEW** | `components/data-display/InlineSparkline.tsx` | Tiny 60×16px sparkline for embedding in table cells and metric displays |
| 20 | `LandingSystem` | **REDESIGN** | `components/landing/LandingSystem.tsx` | Replaces all landing components. One component: input hero + capabilities grid + agent status + recent audits + timeline |

### 5.2 Deprecated Components

| Component | Reason | Replacement |
|---|---|---|
| `AnimatedAgentTheater.tsx` | Theatrical mode killed. Bloomberg has no theater | `ActiveIntel` is always visible in the main stage |
| `page-theater.tsx` | Variant route removed | Standard audit page handles all views |
| `ParticleField.tsx` on landing | Landing is clean, no ambient particle noise | Retained on audit page ONLY as subtle ambient texture (reduced density: 20 particles) |
| `SignalShowcase.tsx` | Marketing carousel killed | Static capabilities grid in `LandingSystem` |
| `DarkPatternCarousel.tsx` | Card carousel → table grid | `DarkPatternGrid` redesigned as structured grid with screenshot links |
| `SiteTypeGrid.tsx` | Landing simplification | Not needed in internal-tool feel |
| `GreenFlagCelebration.tsx` | No confetti in Bloomberg | `VerdictReveal` handles safe sites with green classification stamp |
| `CompletionOverlay.tsx` | Replaced by `VerdictReveal` | — |
| `HowItWorks.tsx` (card layout) | Replaced by dense single-line timeline | Inline in `LandingSystem` |

### 5.3 File Structure

```
frontend/src/components/
├── audit/
│   ├── MetricTicker.tsx
│   ├── AgentTile.tsx
│   ├── ActiveIntel.tsx
│   ├── FindingRow.tsx
│   ├── DataFeed.tsx
│   ├── EventLog.tsx
│   ├── EvidenceStack.tsx
│   └── VerdictReveal.tsx
├── report/
│   ├── SectionNav.tsx
│   ├── SignalTable.tsx
│   ├── SecurityMatrix.tsx
│   ├── DarkPatternGrid.tsx (redesigned)
│   ├── EntityIntel.tsx (new)
│   └── EvidenceGallery.tsx (new)
├── data-display/
│   ├── JsonTreeViewer.tsx
│   ├── TerminalBlock.tsx
│   ├── DataTable.tsx
│   ├── InlineSparkline.tsx
│   └── TrustGauge.tsx (kept, minor style update)
├── landing/
│   └── LandingSystem.tsx (replaces all landing components)
├── layout/
│   ├── PanelChrome.tsx
│   └── Navbar.tsx (updated)
├── providers/
│   └── ChromaticProvider.tsx
└── ui/
    ├── AgentIcon.tsx
    └── SeverityBadge.tsx
```

---

## 6. MICRO-INTERACTION & MOTION CATALOGUE

### 6.1 Interaction Patterns

| Element | Trigger | Animation | Duration | Easing |
|---|---|---|---|---|
| **Finding row** | Appear (new finding arrives) | Slide-in from left + opacity 0→1. Left-stripe appears first, content follows 50ms later | 250ms | `cubic-bezier(0.2, 0, 0, 1)` |
| **Finding row** | Hover | Background brightens by 8%. Left-stripe widens 3px→5px. Slight elevation increase | 150ms | `ease-out` |
| **Finding row** | Click (expand) | Height transition + content fade-in. Chevron rotates 90° | 200ms | `ease-out` |
| **Agent tile** | Activation | Border transitions to agent color at 100%. Icon container brightens. Progress bar begins filling | 400ms | `cubic-bezier(0.4, 0, 0.2, 1)` |
| **Agent tile** | Completion | `CheckCircle2` badge scales in at corner. Status text swaps to "COMPLETE" | 300ms | `ease-out` |
| **Metric ticker** | Number update | Digit counter (increment by 1, not jump). Each digit rolls independently. Slight flash on update | 100ms per digit | `linear` |
| **Panel chrome** | Minimize click | Height collapses to title bar only (28px). Content hidden. Arrow icon rotates | 200ms | `ease-out` |
| **Panel chrome** | Expand click | Height expands to full. Content fades in | 200ms | `ease-out` |
| **Chromatic shift** | Agent changes | CSS custom properties transition. Radial gradient overlay shifts. Border accents transition | 400ms | `cubic-bezier(0.4, 0, 0.2, 1)` |
| **Verdict overlay** | Sequence start | Panels dim 100%→30% opacity. Overlay fades in from center | 500ms | `ease-out` |
| **Score count-up** | Within verdict | 0 → final score. Each number step takes 8ms. Total ≤ 800ms for score 100 | ~800ms | `linear` |
| **Classification stamp** | After count-up | Scale 0.8→1.0 + opacity 0→1. Color-coded badge materializes | 300ms | `cubic-bezier(0, 0, 0.2, 1)` |
| **Log entry** | Appear | No animation by default (instant append). Only newest entry has a brief highlight flash | 100ms flash | `ease-out` |
| **Screenshot thumbnail** | Hover | Scale 1.0→1.03. Border brightens to 20%. Shows "Click to expand" tooltip | 150ms | `ease-out` |
| **Screenshot thumbnail** | Click | Expands to T5 overlay. Zoom/pan enabled. Bounding boxes visible | 300ms | `cubic-bezier(0, 0, 0.2, 1)` |
| **Section nav item** | Scrollspy crosses threshold | Opacity 0.4→1.0. Circle fill transitions. Text color brightens | 200ms | `ease-out` |
| **JSON tree node** | Click (toggle) | Chevron rotates. Children slide down/up with height transition | 150ms | `ease-out` |
| **Table sort** | Click column header | Rows reorder with a stagger animation (each row moves 20ms after the previous) | 300ms total | `ease-out` |

### 6.2 Motion Budget

| Context | Max Simultaneous Animations | Rationale |
|---|---|---|
| **During live audit** | 3 | Ticker ticking + finding rows appearing + log entries streaming. Nothing else should animate |
| **Agent handoff** | 1 | Only the chromatic shift. All other animations pause during the 400ms transition |
| **Verdict reveal** | 2 | Dim transition + score counter. Then stamp. Sequential, not parallel |
| **Report scroll** | 1 | Section nav highlight only. Content is static |
| **Reduced motion** | 0 | All transitions set to 0ms. Instant state changes. No transforms |

### 6.3 Performance Guards

| Guard | Implementation |
|---|---|
| **GPU detection** | `navigator.hardwareConcurrency < 4` → disable particle field entirely, reduce glow effects by 80% |
| **Frame rate monitor** | If FPS drops below 30 for 500ms → auto-reduce animation budget to 1 simultaneous |
| **Reduced motion** | `prefers-reduced-motion: reduce` → all `transition-duration: 0ms`, no transforms, instant state swaps |
| **Virtualized lists** | Event log and finding lists use `react-window` for 200+ items. Only visible rows rendered |

---

## 7. DATA DENSITY & INTERACTIVE DATA STRATEGY

### 7.1 Shneiderman's Mantra: Overview First, Zoom & Filter, Details on Demand

Every data surface follows this information architecture:

| Level | What the User Sees | Interaction |
|---|---|---|
| **Overview** | Summary counts, severity badges, inline sparklines, pass/fail status. Visible at panel level without any interaction | Default state. Always visible |
| **Zoom** | Expanding a finding row, clicking a section nav item, hovering a metric for a tooltip with detail | Single click or hover |
| **Filter** | Event log filter dropdown, finding severity filter, data table column sort, search | Dropdowns, sort headers, search input |
| **Detail** | Full finding detail with evidence links, raw JSON tree, full screenshot with overlays, WHOIS terminal block | Click "EXPAND" or drill-down action |
| **Raw** | Complete JSON audit payload, downloadable, syntax-highlighted, copyable | "RAW DATA" section in report, or `[JSON ↓]` button |

### 7.2 Data Display Types & When to Use Each

| Data Type | Display Format | Component | Example |
|---|---|---|---|
| **Key-value pairs** | Two-column `label: value` in monospace | `TerminalBlock` | WHOIS results, domain info, hosting details |
| **Structured records** | Sortable table with columns | `DataTable` | DNS records, HTTP headers, cookie list |
| **Nested objects** | Collapsible JSON tree with syntax highlighting | `JsonTreeViewer` | Raw audit JSON, API response bodies |
| **Temporal events** | Timestamped log stream | `EventLog` | Audit event timeline |
| **Findings** | Severity-striped expandable rows | `FindingRow` | Security findings, dark patterns |
| **Metrics** | Monospace numbers with inline sparklines | `MetricTicker` / `InlineSparkline` | Page count, link count, score, timing |
| **Binary status** | Pass/fail grid with colored cells | `SecurityMatrix` | Header checks, SSL checks |
| **Screenshots** | Thumbnail grid with overlay annotations | `EvidenceGallery` | Screenshots with dark pattern bounding boxes |
| **Certificates** | Terminal-style certificate dump | `TerminalBlock` | SSL cert chain details |
| **Entity graph data** | Structured terminal-style blocks + mini graph | `TerminalBlock` + future viz | WHOIS → Registrar → IP chain |

### 7.3 JSON Data Presentation — Interactive Log/Tree Format

**Feedback #6: "all data from json but in more interesting way like a log or other type"**

Every piece of data ultimately comes from the JSON audit response. Instead of hiding the JSON behind "View Raw" and showing processed cards, we present data in formats that feel native to security tooling:

**A. JsonTreeViewer (DevTools-inspired)**
```
▾ audit_result
  ▾ findings [12]
    ▾ 0
        severity: "CRITICAL"
        title: "Missing Content-Security-Policy"
        agent: "security_agent"
      ▾ evidence
          header_name: "content-security-policy"
          expected: "present"
          actual: null
          url: "https://suspicious-shop.io/"
    ▸ 1
    ▸ 2
    ...
  ▾ screenshots [4]
    ▸ 0
    ...
  ▸ osint
  ▸ metadata
```
- Syntax highlighted: strings in green, numbers in cyan, booleans in amber, null in red
- Collapsible at every level
- Array items show `[count]`
- Object keys are bold
- Copy button per node (copies that subtree as JSON)
- Search within the tree (highlight matches)

**B. TerminalBlock (WHOIS/DNS/Cert — Terminal-style)**
```
┌─ WHOIS LOOKUP ──────────────── suspicious-shop.io ─┐
│  $ whois suspicious-shop.io                         │
│                                                     │
│  Domain Name: SUSPICIOUS-SHOP.IO                    │
│  Registry Domain ID: abc123-IO                      │
│  Registrar: GoDaddy.com, LLC                        │
│  Created: 2024-01-15T00:00:00Z                      │
│  Updated: 2024-12-01T12:00:00Z                      │
│  Expires: 2025-01-15T00:00:00Z                      │
│  Status: clientTransferProhibited                   │
│  Registrant: REDACTED FOR PRIVACY                   │
│  Name Servers:                                      │
│    ns1.cloudflare.com                               │
│    ns2.cloudflare.com                               │
│                                                     │
│  [COPY] [EXPAND]                                    │
└─────────────────────────────────────────────────────┘
```
- Monospace throughout (JetBrains Mono 11px)
- Terminal black background (`#0D0D0D`)
- Command prompt at top (like it was just run)
- Key fields highlighted in agent color
- Copyable as raw text
- Expandable for full output

**C. DataTable (DNS Records, Headers, Cookies — Sortable Table)**
```
┌─ DNS RECORDS ────────────────────────────── [6] ───┐
│  TYPE    NAME                  VALUE         TTL    │
│  ──────────────────────────────────────────────────  │
│  A       suspicious-shop.io   104.21.45.67  300    │
│  AAAA    suspicious-shop.io   2606:4700::   300    │
│  MX      suspicious-shop.io   mail.google   3600   │
│  TXT     suspicious-shop.io   v=spf1 ...    3600   │
│  NS      suspicious-shop.io   ns1.cf.com    86400  │
│  NS      suspicious-shop.io   ns2.cf.com    86400  │
│                                                     │
│  Click column header to sort · [COPY] [JSON ↓]     │
└─────────────────────────────────────────────────────┘
```
- Column headers clickable for sort (ascending/descending)
- JetBrains Mono for all data cells
- Row hover highlight
- Filter by record type
- Copy as table or export as JSON

### 7.4 Expert vs. Standard Mode

**Not a toggle.** Expert content is always available but collapsed by default. Standard users see the summary; experts expand for depth.

| Data Surface | Standard View (default) | Expert Expansion (click to reveal) |
|---|---|---|
| **Security finding** | Severity + title + one-line description | Full detail: affected URL, expected vs. actual, remediation steps, CWE/OWASP mapping, raw request/response |
| **OSINT data** | Domain age, registrar, hosting, SSL issuer | Full WHOIS dump in `TerminalBlock`, DNS records in `DataTable`, cert chain in `TerminalBlock` |
| **Dark pattern** | Pattern name + category + affected page | Screenshot with bounding box overlay, pattern confidence score, behavioral manipulation technique explanation (psychology reference) |
| **Signal score** | Score bar + pass/fail | Breakdown of sub-checks that contributed to the score, with individual pass/fail per sub-check in a nested table |
| **Full audit data** | Not shown by default | `JsonTreeViewer` in the "RAW DATA" report section, or `[JSON ↓]` download button |

---

## 8. ANIMATION SYSTEM & PERFORMANCE BUDGET

### 8.1 Timing Standards

| Speed Class | Duration | Use Case |
|---|---|---|
| **Instant** | 0–50ms | Hover state changes, button depress, active state swaps |
| **Quick** | 100–200ms | Expand/collapse, finding row appear, tooltip show, panel minimize |
| **Standard** | 250–400ms | Chromatic shift, agent activation, verdict overlay entrance, page transitions |
| **Slow** | 500–800ms | Score count-up (within verdict), full-page transitions, first-load stagger |

### 8.2 Easing Functions

| Easing | CSS Value | Use |
|---|---|---|
| **Snap** | `cubic-bezier(0.2, 0, 0, 1)` | Finding row slide-in, data entry appear — fast start, smooth stop |
| **Smooth** | `cubic-bezier(0.4, 0, 0.2, 1)` | Chromatic shift, agent state transitions — gentle and atmospheric |
| **Bounce** | NOT USED | Bloomberg doesn't bounce. Nothing bounces. Ever |
| **Spring** | NOT USED | No spring physics. All transitions are CSS easing-based, not spring-based |
| **Linear** | `linear` | Score counter (each digit), metric ticker number updates |

### 8.3 Animation Budget (Hard Limits)

| Metric | Budget | Enforcement |
|---|---|---|
| **Max simultaneous CSS transitions** | 3 during audit, 1 during report scroll | `AnimationBudget` utility class tracks active transitions |
| **Max DOM reflows per frame** | 2 | Batch reads then writes. Use `transform` and `opacity` only for animations |
| **Target frame time** | 16ms (60fps) | If frame time exceeds 20ms for 500ms, reduce particle count → disable particles → disable glow |
| **Initial bundle size delta** | < +25kb gzipped vs. current | Tree-shake unused Framer Motion features. Use `LazyMotion` + `domAnimation` |
| **Time to Interactive** | < 3s on 4G connection | Landing page has zero heavy animations. Audit page lazy-loads particle field component |

---

## 9. REPORT PRESENTATION PLAN

### 9.1 Narrative Structure

The report tells a story. It follows a **6-act intelligence briefing** structure borrowed from how actual threat intelligence reports are written (CrowdStrike, Mandiant, Recorded Future):

1. **THE VERDICT** (Executive Summary): "We investigated X. The verdict is Y. Here's the 30-second version."
2. **THE SIGNALS** (Signal Analysis): "Here's where the numbers come from — 6 trust signals, scored and compared against thresholds."
3. **THE DECEPTION** (Dark Patterns + Content): "Here's how this site manipulates its users. With evidence."
4. **THE INFRASTRUCTURE** (Security + Entity): "Here's the technical security posture and who actually runs this site."
5. **THE EVIDENCE** (Screenshots + Gallery): "Here's the visual proof. Every finding links back here."
6. **THE ADVISORY** (Recommendations + Metadata): "Here's what you should do. And here's how we did the analysis."

Each section heading includes an inline summary:
- *"Signal Analysis — 4 of 6 signals below threshold"*
- *"Dark Patterns — 12 detected across 3 categories"*
- *"Security Posture — Missing 4 critical HTTP headers"*

### 9.2 Visual Evidence Integration

**Every finding card links to its evidence.** The current report disconnects findings from screenshots. Fix:

1. Each finding has a small `[Evidence →]` link
2. Clicking it smooth-scrolls to the Evidence Gallery section
3. The relevant screenshot is highlighted with a border glow
4. Bounding box overlays show exactly where on the page the finding was detected
5. This creates a **finding → evidence → screenshot** chain = rigorous, not hand-wavy

### 9.3 Export Options (Future — Not in V1 Revamp)

- **PDF Export**: Server-side render via Puppeteer
- **JSON Export**: Raw audit data dump (available as `[JSON ↓]` button)
- **Share Link**: Public read-only link

Listed for awareness. NOT in scope for immediate revamp.

---

## 10. MITIGATION & RISK PLAN

### 10.1 Performance Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **Too many re-renders during live audit** | Jank, dropped frames | `React.memo` on static components. Zustand selectors (already using). Virtualize lists at 100+ entries |
| **Particle field eats GPU** | Throttled FPS on low-end | Detect `hardwareConcurrency < 4` → disable particles. `prefers-reduced-motion` → always disabled. On audit page only (removed from landing) |
| **Framer Motion bundle** | Slower initial load | Use `LazyMotion` + `domAnimation` feature bundle (saves ~20kb). Already imported — minimal change |
| **Large screenshots** | Memory pressure | Backend serves resized thumbnails. Frontend: `loading="lazy"`. Full-size only on click-to-expand |
| **WebSocket message storms** | Event handler bottleneck | Existing `EventSequencer` in store. Add `requestAnimationFrame` batching if >5 events/frame |
| **CSS custom property transitions** | Browser compatibility | Register with `@property` for animatable custom props. Fallback: class-based instant swaps |
| **Bloomberg data density** | UI feels slow with all panels | All panels default to collapsed minimums. Data streams in lazily. Virtualization on log + finding list |

### 10.2 UX Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **"War Room" feels overwhelming** | New users don't know where to look | Strict hierarchy: ONLY the active agent's panel has bright state. Everything else is dim. Start with just the Agent Stack visible, other panels populate as data arrives |
| **Chromatic shift is too intense** | Motion sickness | 400ms transition is smooth. Only affects background tint + borders, not text. `prefers-reduced-motion` disables entirely (instant color swap, reduced glow) |
| **Verdict reveal blocks interaction** | User wants to see data, not a 3s wait | Click anywhere or ESC to dismiss instantly. Verdict takes MAX 3s. After dismiss, all data remains |
| **Expert expansions are too dense** | Information overload | Expert content is ALWAYS collapsed. User explicitly clicks to expand. Default view is clean summary |
| **Log search limitations** | Users expect regex | Ship with case-insensitive string match. Regex is a v2 feature |
| **No light mode** | Accessibility concern | Not in V1. The Bloomberg/SOC aesthetic is fundamentally dark. Light mode would be a separate design system |

### 10.3 Technical Risks

| Risk | Impact | Mitigation |
|---|---|---|
| **Breaking Zustand store** | Data flow breaks | ZERO store changes. New components consume existing selectors. Only add new selectors if needed |
| **Breaking WebSocket protocol** | Audit page stops working | ZERO backend changes. Same events, same payloads. All changes frontend-only |
| **Component deletion breaks imports** | Build fails | Deprecate last (Phase 6). New components work alongside old ones first. Remove only when all new routes working |
| **CSS variable conflicts** | Styling breaks | New elevation uses new variable names (`--elev-*`). Old `glass-card` class remains during transition |
| **Next.js 16 compatibility** | Hydration issues | All new components are `"use client"` (same pattern as current). Test SSR compat per component |

### 10.4 Accessibility

| Concern | Implementation |
|---|---|
| **Color-blind users** | Severity uses color + icon shape + position + text label. Never color alone |
| **Screen readers** | All dynamic updates in `aria-live="polite"` regions. Verdict has `role="alert"`. Agent state changes announced |
| **Keyboard navigation** | All interactive elements focusable. Tab order follows visual order (left→center→right→bottom). `Escape` closes overlays |
| **Reduced motion** | Globally respected. All transitions 0ms. Score count-up instant. Chromatic shift instant (no transition). Particle field disabled |
| **Contrast ratios** | All text meets WCAG AA (4.5:1 minimum). JetBrains Mono on dark bg is naturally high-contrast. Severity colors tested against dark backgrounds |

---

## 11. IMPLEMENTATION PHASES

### Phase 1: Foundation — Design System + Providers (3-4 days)
- New CSS: elevation tier classes (`elev-1` through `elev-5`), panel chrome styles, typography class overhaul
- `ChromaticProvider` context + CSS custom property wiring on `<body>`
- `PanelChrome` component (reusable panel wrapper with title bar + controls)
- `AgentIcon` component (Lucide icon + container + states)
- `SeverityBadge` component (consistent severity rendering)
- Typography audit: ensure JetBrains Mono on ALL data elements globally
- New severity visual language CSS (left-stripe, badge, row treatments)

### Phase 2: War Room Core (4-5 days)
- `MetricTicker` (header ticker strip with live-updating monospace numbers)
- `AgentTile` (redesigned compact agent cards)
- `ActiveIntel` (center stage with per-agent content switching)
- `FindingRow` (structured finding display with severity stripe + expand)
- `DataFeed` (structured typed entries replacing chat-like NarrativeFeed)
- Wire everything to existing Zustand store (no store changes)
- Chromatic shift integration on audit page layout

### Phase 3: War Room Periphery + Data Display (3-4 days)
- `EvidenceStack` (stacked panels replacing tabbed EvidencePanel)
- `EventLog` (full terminal: timestamps, agent tags, filter, search, copy)
- `VerdictReveal` (3-second overlay sequence)
- `JsonTreeViewer` (collapsible syntax-highlighted JSON tree)
- `TerminalBlock` (terminal-style output for WHOIS/DNS/cert data)
- `DataTable` (sortable/filterable table for structured records)
- `InlineSparkline` (tiny metric sparklines)

### Phase 4: Report Revamp (3-4 days)
- `SectionNav` (left-rail sticky with scrollspy)
- `SignalTable` (table-based signal analysis with score vs. threshold)
- `SecurityMatrix` (pass/fail grid with expandable detail rows)
- `DarkPatternGrid` redesign (structured grid with screenshot evidence links)
- `EntityIntel` (OSINT data in TerminalBlock + DataTable format)
- `EvidenceGallery` (screenshots with finding-linked bounding box overlays)
- RAW DATA section with `JsonTreeViewer`
- Report narrative flow (6-act structure)

### Phase 5: Landing + History + Polish (2-3 days)
- `LandingSystem` — complete landing page redesign (internal-tool feel)
- Remove ParticleField from landing (keep on audit page only, 20 particles)
- Landing: capabilities grid, agent status panel, recent audits table, dense timeline
- History page: table layout with sort/filter, inline score bars
- Navbar update: version badge, system status indicators
- Global polish: all icons swapped from emoji to Lucide, all data in JetBrains Mono

### Phase 6: Cleanup + QA (2-3 days)
- Delete deprecated components: AnimatedAgentTheater, page-theater, GreenFlagCelebration, CompletionOverlay, SignalShowcase, SiteTypeGrid, HowItWorks (card version)
- Performance audit: Lighthouse, Core Web Vitals
- Reduced motion testing (full walkthrough with `prefers-reduced-motion`)
- Mobile responsiveness pass (War Room stacks to single-column)
- Cross-browser: Chrome, Firefox, Safari, Edge
- Accessibility audit (axe-core automated + manual keyboard/screen reader test)

---

## 12. CURRENT VS. REVAMPED COMPARISON

| Aspect | Current | After Revamp |
|---|---|---|
| **Landing page** | Marketing site: ParticleField + animated cards + feature carousel + "INVESTIGATE ANYTHING" hero | Internal tool: clean input hero + capabilities grid + agent status + recent audits table + dense timeline |
| **Depth system** | 1 level (`glass-card`) | 5-tier elevation with distinct visual treatment per tier |
| **Panel structure** | No panel chrome, floating glass cards | Bloomberg chrome: every panel has title bar (28px) with ALL CAPS label, count badge, minimize/expand controls, left accent |
| **Agent identity** | Emoji icons (`🔍🛡️👁️`) on uniform cards | Lucide icons (Radar, ShieldCheck, ScanEye, Network, Scale) in rounded-square containers with agent-color bg |
| **Audit page layout** | 3-column grid: AgentPipeline \| NarrativeFeed \| EvidencePanel | 4-zone War Room: Agent Stack (left) + Active Intel (center) + Evidence Stack (right) + Event Log (bottom) + Metric Ticker (top) |
| **Active agent treatment** | Slightly brighter card, pulse animation | Full chromatic shift: viewport bg tint, border accents, log prompt color, ticker underline glow, particle field color |
| **Chromatic shift** | None | AGGRESSIVE: background radial gradient, border colors, log prompt, ticker accent all shift per agent. 400ms transition |
| **Data feed** | Chat-like scrolling list (NarrativeFeed) | Structured typed entries with severity stripes, expand/collapse, source metadata |
| **Evidence visibility** | Tabbed (can only see one type at a time) | Stacked (Screenshots + Metrics + OSINT all visible simultaneously) |
| **Verdict reveal** | Simple centered modal with number | 3-second institutional sequence: dim → "ANALYSIS COMPLETE" → count-up → classification stamp → CTA. No confetti. Click/ESC dismisses |
| **Report structure** | Stacked cards, all same visual weight | 6-act intelligence dossier with left-rail section nav, scrollspy, inline section summaries |
| **Expert data** | Minimal — some raw cards | Collapsible JSON trees (DevTools-style), terminal-style WHOIS/DNS blocks, sortable data tables, full raw JSON viewer |
| **Typography** | Inter everywhere | Inter (body/headings) + JetBrains Mono (ALL data: numbers, timestamps, scores, badges, logs, code, metrics) |
| **Icon system** | Emoji icons, inconsistent sizing | Lucide 1.5px stroke, round caps, consistent sizing (14/16/20/28px), contained in colored rounded-square housings |
| **Severity encoding** | Color only | Color + Lucide icon + left-stripe (1-3px) + badge + row treatment. CRITICAL gets structural outlier (raised card) |
| **Forensic log** | Collapsed glass card, 3 visible entries | Full terminal: black bg, timestamps, agent tags in color, filter dropdown, search, copy, expandable, 200 entry virtualized |
| **Party colors** | Cyan everywhere | Agent-driven: Scout=teal, Security=emerald, Vision=purple, Graph=amber, Judge=red→verdict |
| **Landing particle field** | Full-page canvas animation on landing | REMOVED from landing. Retained on audit page only at 20 particles as ambient texture |
| **Hover interactions** | Opacity/color changes on glass cards | Bg brighten, stripe widen, scale(1.03-1.05), elevation shifts, contextual tooltip preview |
| **Mobile** | Horizontal pills → stacked columns | War Room stacks to single-column. Panels collapse to title-bar-only. Tap to expand |
| **Performance** | ~60 particles, full framer-motion, no animation budget | 20 particles (audit only), LazyMotion, max 3 simultaneous animations, GPU detection, auto-degrade |

---

## APPROVAL REQUESTED

This plan integrates all 7 feedback points. No implementation begins until you approve or request changes.

**Your 7 points addressed:**

| # | Your Feedback | Where It's Addressed |
|---|---|---|
| 1 | "Bloomberg terminal feel" | Entire document. Panel chrome (§2.1), metric ticker (§4 Scene 2), dense data tables everywhere, monospace data walls, ticking numbers |
| 2 | "Go harder on chromatic shift" | §2.2 — Aggressive shift: viewport radial gradient, border accents at 40%, log prompt color, ticker glow, particle field color. All shift per agent |
| 3 | "OK on verdict timing" | §4 Scene 2b — 3-second sequence confirmed. No confetti. Institutional reveal |
| 4 | "Better views with clear sections" | §4 Scene 2 — 4-zone layout with panel chrome (title bars, counts, controls). §4 Scene 3 — Report with left-rail section nav + scrollspy |
| 5 | "Premium mature icons" | §3 — Complete icon system: Lucide 1.5px stroke, round caps, contained in colored rounded-square housings. Per-agent assignments. 4 visual states |
| 6 | "JSON data as interactive log" | §7.3 — JsonTreeViewer (DevTools-style), TerminalBlock (WHOIS/DNS), DataTable (sortable records). Expert expansions on every data surface |
| 7 | "Premium internal-tool landing" | §4 Scene 1 — Kill marketing feel. Input hero, capabilities grid, agent status panel, recent audits table, dense timeline. No ParticleField, no carousels |

**Ready to execute on your signal.**
