# VERITAS — Frontend Implementation Blueprint

> **"Think like a creator, not just a coder."**
> This document is the single source of truth for the Next.js frontend.
> Every design choice, animation, interaction, and educational element is defined here.
> If context is lost, read this file first.

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Tech Stack](#2-tech-stack)
3. [Color System & Typography](#3-color-system--typography)
4. [Page Architecture](#4-page-architecture)
5. [Page 1: Landing — "The Observatory"](#5-page-1-landing--the-observatory)
6. [Page 2: Live Audit — "The War Room"](#6-page-2-live-audit--the-war-room)
7. [Page 3: Report — "The Dossier"](#7-page-3-report--the-dossier)
8. [Micro-Interactions & Animation System](#8-micro-interactions--animation-system)
9. [Educational Content System — "Did You Know?"](#9-educational-content-system--did-you-know)
10. [WebSocket Protocol & Backend API](#10-websocket-protocol--backend-api)
11. [Component Inventory](#11-component-inventory)
12. [Responsive & Accessibility](#12-responsive--accessibility)
13. [Implementation Order](#13-implementation-order)

---

## 1. Design Philosophy

### Core Principles

| # | Principle | Meaning |
|---|-----------|---------|
| 1 | **Cinematic, Not Dashboard** | This is not a boring analytics dashboard. It's a forensic investigation unfolding in real-time — every phase tells a story. |
| 2 | **Always Alive** | Even when the backend is processing and nothing new has arrived, the UI must be visually alive — ambient animations, educational cards cycling, particle fields responding to scroll/mouse. Zero dead moments. |
| 3 | **Teach While You Wait** | Non-technical users should LEARN something about web safety, dark patterns, and digital trust while watching the audit. The idle time becomes value time. |
| 4 | **No Internal Jargon** | Terms like "NIM", "VLM", "Playwright", "LangGraph" never appear. Instead: "AI Vision Analysis", "Browser Agent", "Intelligence Network". The user sees capability, not implementation. |
| 5 | **International Standard** | Every pixel must feel like a product used by enterprise security teams. Think: CrowdStrike Falcon UI, Stripe Radar, Cloudflare dashboard — that level of polish. |
| 6 | **Progressive Disclosure** | Show the essential first. Let curious users drill deeper. Expert details behind expandable panels, not walls of text. |

### Emotional Journey

```
LANDING PAGE          →    LIVE AUDIT           →    REPORT
"I feel safe here"    →    "This is thrilling"  →    "I understand everything"

Calm confidence       →    Controlled intensity →    Clear resolution
Dark + minimal        →    Dynamic + narrative  →    Structured + actionable
```

### Design References (Mood Board)

- **CrowdStrike Falcon** — Dark theme, threat visualization, real-time indicators
- **Linear.app** — Silky smooth transitions, clean typography, subtle gradients
- **Stripe Radar** — Data-dense but readable, risk scoring UI
- **Vercel Dashboard** — Deployment timeline feel, status indicators
- **Apple.com product pages** — Scroll-triggered animations, cinematic reveals

---

## 2. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Framework | **Next.js 15** (App Router) | Server components, streaming, file-based routing |
| UI Library | **React 19** | Latest concurrent features |
| Styling | **Tailwind CSS 4** | Utility-first, fast iteration |
| Components | **shadcn/ui** | Accessible, unstyled base components |
| Animation | **Framer Motion 11** | Layout animations, exit animations, choreographed sequences |
| 3D/Particles | **tsparticles** (lightweight) | Ambient particle background — no heavy Three.js dependency |
| Charts | **Recharts** | Radar chart, gauge, bar charts for trust signals |
| Graph Viz | **react-force-graph-2d** | Interactive entity relationship graph |
| Icons | **Lucide React** | Consistent, professional icon set |
| Fonts | **Inter** (body) + **JetBrains Mono** (data/code) | via `next/font` |
| Real-time | **Native WebSocket** | Direct WS connection to FastAPI backend |
| State | **Zustand** | Lightweight global state for audit data |
| Type Safety | **TypeScript 5** | End-to-end type safety |

---

## 3. Color System & Typography

### Color Palette

```
Background Layers:
  --bg-deep:       #050810    (deepest background — almost black with blue tint)
  --bg-surface:    #0A0F1E    (card surfaces)
  --bg-elevated:   #111827    (elevated panels, modals)
  --bg-hover:      #1F2937    (hover states)

Accent Spectrum (The "Trust Gradient"):
  --accent-cyan:   #06B6D4    (primary accent — trust, scanning, active)
  --accent-blue:   #3B82F6    (secondary — links, info)
  --accent-purple: #8B5CF6    (tertiary — intelligence, AI)
  --accent-indigo: #6366F1    (graph/network visualization)

Risk Colors (Semantic):
  --risk-safe:     #10B981    (emerald green — trusted)
  --risk-caution:  #F59E0B    (amber — suspicious, needs attention)
  --risk-warning:  #F97316    (orange — high risk)
  --risk-danger:   #EF4444    (red — likely fraudulent / critical)

Text:
  --text-primary:  #F9FAFB    (near-white — headings, primary text)
  --text-secondary:#9CA3AF    (muted gray — secondary text)
  --text-tertiary: #6B7280    (subtle gray — labels, timestamps)

Glow Effects:
  --glow-cyan:     rgba(6, 182, 212, 0.15)
  --glow-danger:   rgba(239, 68, 68, 0.15)
  --glow-safe:     rgba(16, 185, 129, 0.15)
```

### Typography Scale

```
Display (hero):    text-5xl  / 3rem    / font-bold / tracking-tight / Inter
Heading 1:         text-3xl  / 1.875rem / font-bold / tracking-tight / Inter
Heading 2:         text-2xl  / 1.5rem  / font-semibold / Inter
Heading 3:         text-lg   / 1.125rem / font-semibold / Inter
Body:              text-base / 1rem    / font-normal / Inter
Small:             text-sm   / 0.875rem / font-normal / Inter
Caption:           text-xs   / 0.75rem / font-medium / Inter uppercase tracking-wide
Data/Code:         text-sm   / 0.875rem / font-mono / JetBrains Mono
```

---

## 4. Page Architecture

```
/                    → Landing Page ("The Observatory")
/audit/[id]          → Live Audit Page ("The War Room")
/report/[id]         → Report Page ("The Dossier")
```

### Layout Structure

```
app/
  layout.tsx              ← Root layout: dark theme, fonts, global nav
  page.tsx                ← Landing page
  audit/
    [id]/
      page.tsx            ← Live audit page
  report/
    [id]/
      page.tsx            ← Report page
  globals.css             ← Tailwind + custom CSS variables
```

---

## 5. Page 1: Landing — "The Observatory"

### Purpose
First impression. Must communicate: **"This tool is powerful, trustworthy, and easy to use."**
The user should feel like they're stepping into a world-class security operations center.

### Visual Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ ✦ VERITAS                              [About] [How It Works]      │ ← Minimal nav
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│              ◐  ← Animated shield/eye logo (SVG, subtle pulse)     │
│                                                                     │
│                    V E R I T A S                                    │ ← Display text
│          Autonomous Forensic Web Auditor                            │ ← Subtitle fade-in
│                                                                     │
│     "See what websites don't want you to see."                      │ ← Tagline
│                                                                     │
│   ┌───────────────────────────────────────────────────────────┐     │
│   │ 🔗  Enter website URL...                       [Analyze] │     │ ← URL input bar
│   └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│      ○ Quick Scan        ◉ Standard Audit       ○ Deep Forensic   │ ← Tier selector
│        ~60 seconds          ~3 minutes              ~5 minutes      │
│        Basic checks         Full analysis           Everything      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── WHAT WE ANALYZE ──────────────────────────────────────────────  │
│                                                                     │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐      │
│  │  👁️  │  │  🔍  │  │  ⏱️  │  │  🌐  │  │  🔒  │  │  🛡️  │      │
│  │Visual│  │Struct│  │Tempo-│  │Graph │  │Meta  │  │Secu- │      │
│  │Intel │  │ural  │  │ral   │  │Intel │  │Data  │  │rity  │      │
│  │      │  │Scan  │  │Analy-│  │      │  │      │  │Audit │      │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘      │
│                                                                     │
│  Each card has hover-expand micro-animation explaining              │
│  what it does in plain English                                      │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── DARK PATTERNS WE DETECT ─────────────────────────────────────  │
│                                                                     │
│  Animated rotating carousel (auto-play + manual navigation):        │
│                                                                     │
│  ┌─────────────────────────────────────────┐                        │
│  │  🎭 Visual Interference                 │                        │
│  │                                         │                        │
│  │  "Hidden cancel buttons, disguised ads, │                        │
│  │   trick questions designed to mislead   │                        │
│  │   your clicks."                         │                        │
│  │                                         │                        │
│  │  Examples:                              │                        │
│  │  • 'Accept All' is huge, green          │                        │
│  │  • 'Decline' is tiny, gray, hidden      │                        │
│  │                                         │                        │
│  │  Severity: ████████░░ High              │                        │
│  │                                         │                        │
│  │              ● ○ ○ ○ ○                  │                        │
│  └─────────────────────────────────────────┘                        │
│                                                                     │
│  Five cards total — one per dark pattern category:                  │
│    1. Visual Interference                                           │
│    2. False Urgency (fake timers, fake scarcity)                   │
│    3. Forced Continuity (roach motel, guilt-tripping)              │
│    4. Sneaking (hidden costs, pre-selected add-ons)                │
│    5. Social Engineering (fake reviews, fake badges)               │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── HOW VERITAS WORKS ──────────────────────────────────────────── │
│                                                                     │
│  Scroll-triggered step-by-step reveal:                              │
│                                                                     │
│    Step 1  ─────────●  Browser Agent visits the site stealthily    │
│    Step 2  ────●       AI Vision analyzes every screenshot          │
│    Step 3  ────●       Intelligence Network verifies the entity    │
│    Step 4  ────●       Security Audit scans headers & forms        │
│    Step 5  ────●       Forensic Judge weighs all evidence          │
│    Step 6  ────●       Comprehensive trust report generated        │
│                                                                     │
│  Each step reveals on scroll with slide-up + fade animation        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── TRUST ACROSS DOMAINS ──────────────────────────────────────── │
│                                                                     │
│  Animated icon grid showing site type adaptability:                 │
│                                                                     │
│  🛒 E-commerce   🏢 Corporate   🏦 Financial   ☁️ SaaS   🕶️ Dark Web │
│                                                                     │
│  "Veritas adapts its analysis to each website type."               │
│  Hover each icon to see what Veritas checks specifically.          │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                    Veritas — Trust, Verified.                       │ ← Footer
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Ambient Background
- **tsparticles** field with low-opacity cyan dots connected by faint lines
- Moves gently with mouse parallax (not distracting, purely atmospheric)
- Particle density increases slightly near the URL input (visual focus)

### Key Interactions
1. **URL Input** — Glowing border on focus, real-time URL validation, submit on Enter
2. **Tier Selector** — Radio cards with smooth border animation on selection; brief tooltip on hover explaining each tier
3. **Signal Cards** — Hover → card lifts with shadow + reveals 2-line explanation
4. **Dark Pattern Carousel** — Auto-rotates every 6s, swipe/click to navigate, pause on hover
5. **How It Works** — Steps reveal on scroll with staggered cascade (200ms delay each)
6. **CTA Button** — Gradient border animation (cyan→purple shimmer) on the Analyze button

---

## 6. Page 2: Live Audit — "The War Room"

### Purpose
This is the **heart of the product**. The user watches a real-time forensic investigation unfold.
Even during quiet moments (backend processing), the UI must be visually engaging and educational.

**This page is the #1 priority for creative investment.**

### Visual Layout — Three-Column Responsive

```
┌─────────────────────────────────────────────────────────────────────┐
│ ← Back   VERITAS AUDIT: www.example.com            ⏱ 2m 34s      │
├──────────────┬──────────────────────────────┬───────────────────────┤
│              │                              │                       │
│  AGENT       │    NARRATIVE FEED            │  EVIDENCE PANEL       │
│  PIPELINE    │    (center stage)            │  (right sidebar)      │
│              │                              │                       │
│ ┌──────────┐ │ ┌──────────────────────────┐ │ ┌─────────────────┐   │
│ │ 🔎 Scout │ │ │                          │ │ │ 📸 Screenshots  │   │
│ │ ████████ │ │ │  ┌──────────────────┐    │ │ │                 │   │
│ │ Complete │ │ │  │ SCOUT REPORT     │    │ │ │ [thumb][thumb]  │   │
│ └──────────┘ │ │  │                  │    │ │ │ [thumb][thumb]  │   │
│       │      │ │  │ ✅ SSL valid     │    │ │ │                 │   │
│       ↓      │ │  │ ✅ Page loaded   │    │ │ │ Click to expand │   │
│ ┌──────────┐ │ │  │ ⚠️ 3 forms found │    │ │ ├─────────────────┤   │
│ │ 🛡 Secur │ │ │  │ ✅ No CAPTCHA   │    │ │ │ 🔍 Findings     │   │
│ │ ████████ │ │ │  └──────────────────┘    │ │ │                 │   │
│ │ Complete │ │ │                          │ │ │ ⚠️ Hidden cost  │   │
│ └──────────┘ │ │  ┌──────────────────┐    │ │ │  drip pricing   │   │
│       │      │ │  │   ✨ DID YOU     │    │ │ │  Severity: High │   │
│       ↓      │ │  │   KNOW?          │    │ │ │                 │   │
│ ┌──────────┐ │ │  │                  │    │ │ │ 🎭 Fake badge   │   │
│ │ 👁 Vision│ │ │  │ "Dark patterns   │    │ │ │  Norton image   │   │
│ │ ████░░░░ │ │ │  │  cost consumers  │    │ │ │  not clickable  │   │
│ │ Analyz.. │ │ │  │  $12.8B/year"    │    │ │ │  Severity: Crit │   │
│ └──────────┘ │ │  │                  │    │ │ ├─────────────────┤   │
│       │      │ │  └──────────────────┘    │ │ │ 📊 Live Stats   │   │
│       ↓      │ │                          │ │ │                 │   │
│ ┌──────────┐ │ │  ┌──────────────────┐    │ │ │ Pages: 3        │   │
│ │ 🌐 Graph │ │ │  │ VISION ANALYSIS  │    │ │ │ Findings: 5     │   │
│ │ ░░░░░░░░ │ │ │  │                  │    │ │ │ Screenshots: 8  │   │
│ │ Waiting  │ │ │  │ Analyzing page   │    │ │ │ AI Calls: 12    │   │
│ └──────────┘ │ │  │ visuals for      │    │ │ │ Elapsed: 2m34s  │   │
│       │      │ │  │ deceptive        │    │ │ │                 │   │
│       ↓      │ │  │ patterns...      │    │ │ └─────────────────┘   │
│ ┌──────────┐ │ │  │                  │    │ │                       │
│ │ ⚖️ Judge │ │ │  │ [animation of    │    │ │                       │
│ │ ░░░░░░░░ │ │ │  │  AI eye scanning │    │ │                       │
│ │ Waiting  │ │ │  │  a screenshot]   │    │ │                       │
│ └──────────┘ │ │  └──────────────────┘    │ │                       │
│              │ │                          │ │                       │
│              │ └──────────────────────────┘ │                       │
│              │                              │                       │
├──────────────┴──────────────────────────────┴───────────────────────┤
│                                                                     │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  FORENSIC LOG — Live Technical Feed (collapsible)            │  │
│   │  [10:32:15] Scout → Navigated to https://example.com        │  │
│   │  [10:32:16] Scout → SSL certificate valid (Let's Encrypt)   │  │
│   │  [10:32:17] Scout → Detected site type: E-commerce (94%)    │  │
│   │  [10:32:18] Security → Checking HTTP security headers...    │  │
│   │  [10:32:19] Security → Missing: CSP, X-Frame-Options        │  │
│   │  [10:32:22] Vision → Analyzing screenshot_001.jpg...        │  │
│   │  [10:32:25] Vision → FINDING: Hidden unsubscribe (0.87)     │  │
│   └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Left Column: Agent Pipeline (Fixed, Always Visible)

Five vertical cards representing the audit phases:

```
States per card:
  WAITING    → Muted, dashed border, pulsing dot
  ACTIVE     → Glowing cyan border, animated progress bar, phase-specific animation inside
  COMPLETE   → Solid green check, summary text visible, slight glow
  ERROR      → Red border, error icon, retry option
```

**Card Content When Active:**

| Agent | Active Animation | Active Description |
|-------|-----------------|-------------------|
| **Scout** | Miniature browser window graphic with scanning line moving down | "Browser agent visiting the website stealthily..." |
| **Security** | Shield icon with rotating scan ring | "Analyzing security headers, checking phishing databases..." |
| **Vision** | Eye icon with iris that pulses/scans | "AI vision analyzing screenshots for deceptive patterns..." |
| **Graph** | Network nodes connecting with animated edges | "Cross-referencing domain records, business registries..." |
| **Judge** | Scales of justice gently tipping | "Weighing all evidence to compute final trust score..." |

**Card Content When Complete:**

Show a 1-2 line summary result:
- Scout: "3 pages scanned, 8 screenshots captured"
- Security: "2 missing headers, 0 phishing flags"
- Vision: "5 dark patterns detected (2 critical)"
- Graph: "Domain age: 1,247 days, entity verified"
- Judge: "Trust Score: 72/100 — Probably Safe"

### Center Column: Narrative Feed (The Star)

This is a **vertical scrolling feed** that tells the story of the audit. Each entry is a card that animates in (slide up + fade in). Cards appear in real-time as the audit progresses.

**Card Types in the Feed:**

#### 1. Agent Report Card
```
┌─────────────────────────────────────────┐
│  🔎 BROWSER RECONNAISSANCE             │
│  ──────────────────────────────────     │
│                                         │
│  ✅ Page loaded in 1.2s                 │
│  ✅ SSL certificate valid (Let's Encrypt)│
│  ✅ No CAPTCHA challenges               │
│  ⚠️  3 forms detected (analyzing...)    │
│  📋 Site classified as: E-commerce      │
│                                         │
│  "The browser agent successfully        │
│   infiltrated the website and began     │
│   collecting evidence."                 │ ← Narrative text
│                                         │
└─────────────────────────────────────────┘
```

#### 2. Finding Alert Card (appears with attention-grabbing animation)
```
┌─────────────────────────────────────────┐
│  ⚠️  DARK PATTERN DETECTED             │  ← Amber/red glow pulse
│  ──────────────────────────────────     │
│                                         │
│  Category: Sneaking                     │
│  Pattern: Hidden Costs / Drip Pricing   │
│  Severity: ████████░░ HIGH              │
│  Confidence: 87%                        │
│                                         │
│  "Additional fees appear only at        │
│   checkout — not shown on the product   │
│   listing page."                        │
│                                         │
│  What this means: The website adds      │
│  hidden charges that you wouldn't       │  ← Plain English
│  expect, making the real price higher   │
│  than advertised.                       │
│                                         │
└─────────────────────────────────────────┘
```

#### 3. Educational "Did You Know?" Card (appears BETWEEN agent phases)
```
┌─────────────────────────────────────────┐
│  ✨ DID YOU KNOW?                       │  ← Subtle purple glow
│  ──────────────────────────────────     │
│                                         │
│  "According to a Princeton study,      │
│   11,000 shopping websites use at       │
│   least one dark pattern. The most      │
│   common? Hidden costs at checkout."    │
│                                         │
│  Source: Princeton Dark Patterns        │
│  Research, 2019                         │
│                                         │
└─────────────────────────────────────────┘
```

#### 4. Phase Transition Card
```
┌─────────────────────────────────────────┐
│  ──── PHASE 3 OF 5 ────                │
│                                         │
│  🌐 Intelligence Network               │
│                                         │
│  "Now cross-referencing the website's   │
│   identity with global registries,      │
│   DNS records, and business databases." │
│                                         │
│  ▸ This phase typically takes 30-60s    │
│                                         │
└─────────────────────────────────────────┘
```

#### 5. Screenshot Reveal Card (when Vision processes a screenshot)
```
┌─────────────────────────────────────────┐
│  📸 SCREENSHOT ANALYSIS                 │
│  ──────────────────────────────────     │
│                                         │
│  ┌───────────────────────────────┐      │
│  │                               │      │
│  │   [Screenshot image with      │      │
│  │    semi-transparent red        │      │
│  │    overlay on detected         │      │
│  │    dark pattern areas]         │      │
│  │                               │      │
│  └───────────────────────────────┘      │
│                                         │
│  AI Vision identified 2 concerns:       │
│  • Accept button 3x larger than Decline │
│  • Unsubscribe link at 8px, gray-on-gray│
│                                         │
└─────────────────────────────────────────┘
```

### Right Column: Evidence Panel (Fixed Sidebar)

Three collapsible sections:

**📸 Screenshots** — Thumbnail grid. Click to open lightbox with full image. Thumbnails appear with a satisfying "polaroid drop" animation as they're captured.

**🔍 Findings** — Scrollable list of detected issues. Each entry has:
- Severity badge (color-coded)
- Category icon
- One-line summary
- Expand to see full detail

**📊 Live Stats** — Real-time counters with CountUp animation:
- Pages Scanned: 3
- Screenshots: 8
- Findings: 5
- AI Analysis Calls: 12
- Security Checks: 4
- Elapsed: 2m 34s

### Bottom Bar: Forensic Log (Collapsible)

A terminal-style scrolling log with monospace font, timestamps, and color-coded entries:
- `[timestamp] Agent → Action` format
- Green for success, amber for warnings, red for errors, cyan for info
- Auto-scrolls to bottom, user can scroll up to pause
- Collapsed by default (small "peek" showing last 2 lines), click to expand

### The "Nothing Happening" Problem — Solved

When the backend is processing and no new events arrive for >3 seconds:

1. **Educational Cards** appear in the narrative feed (see Section 9 for full content)
2. **Phase-Specific Ambient Animations** play in the active agent card
3. **Progress Bar** shows smooth interpolated progress (not jumpy)
4. **Forensic Log** continues to show "processing..." entries with timestamps
5. **Stats Counters** have subtle pulse animation
6. **Particle Background** shifts color subtly based on current phase

### Completion Animation

When the audit finishes:
1. All agent cards flash green simultaneously (0.5s)
2. The narrative feed shows a "AUDIT COMPLETE" card with the trust score
3. Trust score number counts up from 0 to final value (1.5s, easing)
4. Color of the score gauge reflects risk level
5. A "View Full Report →" button appears with gradient shimmer
6. Confetti/particle burst if score > 85 (trusted site celebration)

---

## 7. Page 3: Report — "The Dossier"

### Purpose
The permanent, shareable, printable forensic report. Must feel authoritative and clear.
Two modes: **Simple** (for non-technical users) and **Expert** (for security professionals).

### Visual Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ ← Back to Audit   VERITAS FORENSIC REPORT                         │
│                    www.example.com · February 14, 2026              │
│                                                                     │
│     ┌───────┐      ┌──────────────┐                                │
│     │ [PDF] │      │ Simple │Expert│  ← Mode toggle                │
│     └───────┘      └──────────────┘                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── TRUST SCORE ──────────────────────────────────────────────────  │
│                                                                     │
│           ┌──────────────────────┐                                  │
│           │                      │                                  │
│           │    ┌────────┐        │   Risk Level: PROBABLY SAFE     │
│           │    │   72   │        │                                  │
│           │    │  /100  │        │   "This website appears mostly  │
│           │    └────────┘        │    legitimate but has some       │
│           │   ██████████░░░░    │    questionable practices."      │
│           │                      │                                  │
│           └──────────────────────┘                                  │
│                                                                     │
│   Animated trust gauge (circular arc) that fills on page load       │
│   Color: green(90+) → teal(70-89) → amber(40-69)                  │
│          → orange(20-39) → red(0-19)                                │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── SIGNAL BREAKDOWN ────────────────────────────────────────────  │
│                                                                     │
│   ┌───────────────────────┐   ┌──────────────────────────────────┐ │
│   │                       │   │                                  │ │
│   │    RADAR CHART        │   │  Visual Intelligence    82/100   │ │
│   │    (6-axis)           │   │  ████████████████░░░░           │ │
│   │                       │   │  Structural Analysis    65/100   │ │
│   │   Visual ─── Meta     │   │  █████████████░░░░░░░          │ │
│   │    /          \       │   │  Temporal Analysis     90/100   │ │
│   │  Secur ──── Struct    │   │  ██████████████████░░          │ │
│   │    \          /       │   │  Graph Intelligence    58/100   │ │
│   │   Graph ── Temporal   │   │  ████████████░░░░░░░░          │ │
│   │                       │   │  Meta Verification     75/100   │ │
│   └───────────────────────┘   │  ███████████████░░░░░          │ │
│                               │  Security Audit        70/100   │ │
│   Animated radar that draws   │  ██████████████░░░░░░          │ │
│   its shape on page load      │                                  │ │
│                               └──────────────────────────────────┘ │
│                                                                     │
│   Each signal row is expandable → reveals sub-signal details        │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── DARK PATTERNS FOUND ─────────────────────────────────────────  │
│                                                                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │
│  │ Visual │ │ Urgency│ │ Forced │ │Sneaking│ │ Social │           │
│  │ Inter. │ │        │ │ Contin.│ │        │ │ Engin. │           │
│  │  2 ⚠️  │ │  1 🔴  │ │  0 ✅  │ │  2 🔴  │ │  1 ⚠️  │           │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘           │
│                                                                     │
│  Category tabs — click to see findings in that category             │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Finding #1: Hidden Costs / Drip Pricing                      │  │
│  │  Severity: CRITICAL  │  Confidence: 87%  │  Category: Sneaking│  │
│  │                                                               │  │
│  │  Evidence: Additional $4.99 "service fee" appears only at     │  │
│  │  checkout. Product page shows $19.99 but final total is       │  │
│  │  $24.98.                                                      │  │
│  │                                                               │  │
│  │  🖼️ [Annotated screenshot showing the hidden fee]              │  │
│  │                                                               │  │
│  │  What this means for you: (Simple mode)                       │  │
│  │  "The price you see isn't the price you pay. The website      │  │
│  │   hides extra charges until the very last step."              │  │
│  │                                                               │  │
│  │  Technical Detail: (Expert mode)                              │  │
│  │  "DOM analysis reveals a .checkout-fee element injected via   │  │
│  │   JavaScript on the /checkout route, absent from /product     │  │
│  │   pages. Price delta: 24.9% above listed price."              │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── ENTITY VERIFICATION ─────────────────────────────────────────  │
│                                                                     │
│  ┌─────────────────────────┐  ┌───────────────────────────────┐   │
│  │                         │  │                               │   │
│  │   ENTITY GRAPH          │  │  Domain: example.com          │   │
│  │   (force-directed)      │  │  Registrar: GoDaddy          │   │
│  │                         │  │  Age: 1,247 days (3.4 years) │   │
│  │   [example.com]         │  │  SSL: Let's Encrypt (valid)  │   │
│  │      /    |    \        │  │  IP: 104.21.x.x (Cloudflare) │   │
│  │   [IP] [WHOIS] [SSL]   │  │  Country: United States       │   │
│  │      \    |    /        │  │                               │   │
│  │   [Registrar]           │  │  Inconsistencies: 1           │   │
│  │                         │  │  ⚠️ Footer says "Since 2010"   │   │
│  │   Interactive: drag,    │  │     but domain registered     │   │
│  │   zoom, hover nodes     │  │     in 2022                   │   │
│  │                         │  │                               │   │
│  └─────────────────────────┘  └───────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── SECURITY AUDIT ──────────────────────────────────────────────  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  HTTP Security Headers                                       │  │
│  │                                                              │  │
│  │  ✅ Strict-Transport-Security     present                   │  │
│  │  ✅ X-Content-Type-Options        nosniff                   │  │
│  │  ❌ Content-Security-Policy       MISSING                   │  │
│  │  ❌ X-Frame-Options               MISSING                   │  │
│  │  ✅ Referrer-Policy               strict-origin             │  │
│  │  ⚠️  Permissions-Policy           partial                   │  │
│  │                                                              │  │
│  │  Score: 4/6 headers present                                 │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  Phishing Database Check                                     │  │
│  │  ✅ Not found in Google Safe Browsing                       │  │
│  │  ✅ Not found in PhishTank                                  │  │
│  │  ✅ Not found in OpenPhish                                  │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  Form Security                                               │  │
│  │  ⚠️  Credit card form without autocomplete="off"            │  │
│  │  ✅ All forms submit over HTTPS                             │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── RECOMMENDATIONS ─────────────────────────────────────────────  │
│                                                                     │
│  ┌─────────┐  ┌─────────────────────────────────────────────────┐  │
│  │ 🔴 HIGH │  │ Review all charges before finalizing payment.  │  │
│  │         │  │ Hidden fees may inflate the actual cost.        │  │
│  └─────────┘  └─────────────────────────────────────────────────┘  │
│  ┌─────────┐  ┌─────────────────────────────────────────────────┐  │
│  │ 🟡 MED  │  │ Verify trust badges by clicking them.          │  │
│  │         │  │ Some security seals on this site are just images│  │
│  └─────────┘  └─────────────────────────────────────────────────┘  │
│  ┌─────────┐  ┌─────────────────────────────────────────────────┐  │
│  │ 🟢 LOW  │  │ Check terms before starting any free trial.    │  │
│  │         │  │ Auto-renewal terms may apply.                   │  │
│  └─────────┘  └─────────────────────────────────────────────────┘  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ── AUDIT METADATA ──────────────────────────────────────────────  │
│                                                                     │
│  Audit ID: vrts_a1b2c3d4                                            │
│  Tier: Deep Forensic                                                │
│  Date: February 14, 2026 at 10:32 AM                               │
│  Duration: 4m 12s                                                   │
│  Pages Analyzed: 5                                                  │
│  Screenshots: 12                                                    │
│  AI Analysis Calls: 23                                              │
│  Security Modules: 4                                                │
│  Site Type Detected: E-commerce (94% confidence)                   │
│  Verdict Mode: Expert                                               │
│                                                                     │
│              [Download PDF]  [Share Link]  [New Audit]              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Report Page Animations
1. **Trust Score Gauge** — Circular arc fills from 0 to final score on mount (1.5s ease-out)
2. **Radar Chart** — Each axis extends from center to its value with staggered delay (0.2s per axis)
3. **Signal Bars** — Each bar slides right from 0% to value with count-up number
4. **Dark Pattern Category Tabs** — Slide-in from bottom on scroll
5. **Entity Graph** — Nodes appear one by one, edges draw between them (force simulation)
6. **Security Checklist** — Items checked off one by one (0.3s delay each)

---

## 8. Micro-Interactions & Animation System

### Global Animation Tokens

```typescript
const ANIMATION = {
  // Timing
  fast:      { duration: 0.15 },
  normal:    { duration: 0.3 },
  slow:      { duration: 0.6 },
  dramatic:  { duration: 1.2 },

  // Easings
  snappy:    { ease: [0.25, 0.46, 0.45, 0.94] },
  smooth:    { ease: [0.4, 0, 0.2, 1] },
  bounce:    { ease: [0.68, -0.55, 0.265, 1.55] },
  dramatic:  { ease: [0.16, 1, 0.3, 1] },

  // Common patterns
  fadeUp:    { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 } },
  fadeIn:    { initial: { opacity: 0 }, animate: { opacity: 1 } },
  slideIn:   { initial: { opacity: 0, x: -20 }, animate: { opacity: 1, x: 0 } },
  scaleIn:   { initial: { scale: 0.95, opacity: 0 }, animate: { scale: 1, opacity: 1 } },
  countUp:   { from: 0, duration: 1.5 },
}
```

### Specific Micro-Interactions

| Element | Trigger | Animation |
|---------|---------|-----------|
| URL Input | Focus | Border glows cyan, slight scale up (1.02) |
| Analyze Button | Hover | Gradient border shimmer (linear-gradient animation) |
| Analyze Button | Click | Scale down (0.95), then navigate |
| Agent Card | Becomes active | Border transitions from dashed-gray to solid-cyan with glow |
| Agent Card | Complete | Green checkmark pops in, progress bar fills to 100% |
| Narrative Card | New entry | Slides up from below with staggered children animation |
| Finding Alert | Appears | Brief red/amber pulse glow on the entire card, then settles |
| Screenshot Thumbnail | New capture | "Polaroid drop" — falls and rotates slightly, then settles |
| Screenshot Thumbnail | Click | Expands to lightbox with backdrop blur |
| Did You Know Card | Appears | Fade in with slight scale, purple glow |
| Stats Counter | Value change | Number rolls up/down to new value |
| Trust Score Gauge | Page load | Arc draws from 0° to score angle over 1.5s |
| Radar Chart | Page load | Each axis extends from center with stagger |
| Forensic Log | New entry | New line types out (typewriter effect, 50ms per char) |
| Signal Bar | Page load | Width transitions from 0% to value over 0.6s |
| Page Transition | Navigate | Shared layout animation via Framer Motion |

### Phase-Dependent Ambient Effects

The particle background and UI color accent shift subtly based on audit phase:

| Phase | Particle Color | Accent Shift | Mood |
|-------|---------------|-------------|------|
| Scout | Cyan (#06B6D4) | Default | Calm reconnaissance |
| Security | Teal (#14B8A6) | Slightly green | Protective scanning |
| Vision | Purple (#8B5CF6) | Purple tint | AI intelligence |
| Graph | Indigo (#6366F1) | Blue-purple | Deep investigation |
| Judge | Amber (#F59E0B) | Warm gold | Deliberation |
| Complete | Green (#10B981) | Green if safe, Red if danger | Resolution |

---

## 9. Educational Content System — "Did You Know?"

### Purpose
Fill quiet moments with fascinating, relevant content. Non-technical users should LEARN something.
Each card is shown between agent phases, during long processing, or during idle moments.

### Content Categories

#### A. Dark Pattern Facts (rotate randomly)

```json
[
  {
    "title": "The $12.8 Billion Problem",
    "text": "Dark patterns cost consumers an estimated $12.8 billion per year through deceptive design choices that trick people into unintended purchases.",
    "source": "FTC Consumer Reports, 2023"
  },
  {
    "title": "11,000 Websites, 1,818 Dark Patterns",
    "text": "A Princeton University study crawled 11,000 shopping websites and found 1,818 instances of dark patterns. Nearly 1 in 6 websites used at least one.",
    "source": "Princeton Web Transparency & Accountability Project"
  },
  {
    "title": "The EU Strikes Back",
    "text": "The European Union's Digital Services Act (2024) explicitly bans dark patterns, making deceptive UX design illegal with fines up to 6% of global revenue.",
    "source": "EU Digital Services Act, Article 25"
  },
  {
    "title": "Roach Motel: Easy In, Hard Out",
    "text": "One of the most common dark patterns is the 'Roach Motel' — signing up takes one click, but canceling requires calling a phone number during business hours.",
    "source": "darkpatterns.org"
  },
  {
    "title": "The Fake Timer Trick",
    "text": "Fake countdown timers on e-commerce sites create artificial urgency. Studies show they increase conversion by 332%, but the timer simply resets when it reaches zero.",
    "source": "Journal of Marketing Research"
  },
  {
    "title": "Amazon's Dark Secret",
    "text": "Internal Amazon documents revealed the company deliberately made it difficult to cancel Prime subscriptions. The project was internally named 'Iliad' after Homer's epic about a war that dragged on forever.",
    "source": "FTC v. Amazon.com, Inc., 2023"
  },
  {
    "title": "Confirmshaming",
    "text": "Many websites use guilt-tripping language on decline buttons: 'No thanks, I don't want to save money' or 'I prefer to pay full price.' This psychological manipulation is called confirmshaming.",
    "source": "UX Research Institute"
  },
  {
    "title": "The Pre-Selected Checkbox",
    "text": "Studies show that pre-checked boxes have a 70-90% opt-in rate, compared to 10-30% when unchecked. That's why hidden subscriptions and add-ons are pre-selected by default.",
    "source": "Behavioral Economics Research"
  }
]
```

#### B. Audit Terminology Explained (shown contextually based on current phase)

```json
{
  "scout_phase": [
    {
      "term": "Browser Fingerprinting",
      "definition": "Websites can identify your browser by its unique combination of settings, fonts, and plugins — even without cookies. Our Browser Agent uses stealth techniques to avoid detection."
    },
    {
      "term": "SSL/TLS Certificate",
      "definition": "The padlock icon in your browser. It encrypts data between you and the website. But a valid SSL doesn't mean the site is trustworthy — even phishing sites can have SSL certificates."
    },
    {
      "term": "CAPTCHA Detection",
      "definition": "Some websites use CAPTCHA challenges to block automated analysis. Our agent detects these barriers and adapts its investigation strategy accordingly."
    },
    {
      "term": "DOM Analysis",
      "definition": "The DOM is the website's internal structure — like an X-ray of the page. We analyze it to find hidden elements, invisible buttons, and deceptive form fields."
    }
  ],
  "security_phase": [
    {
      "term": "Content Security Policy (CSP)",
      "definition": "A security header that tells the browser which scripts are allowed to run. Without CSP, attackers can inject malicious code into the page."
    },
    {
      "term": "Phishing Database",
      "definition": "Databases like Google Safe Browsing maintain lists of known phishing websites. We cross-reference every audited URL against these global databases."
    },
    {
      "term": "HTTP Security Headers",
      "definition": "When your browser visits a website, the server sends invisible 'headers' with security instructions. Missing headers = potential vulnerabilities."
    }
  ],
  "vision_phase": [
    {
      "term": "AI Vision Analysis",
      "definition": "Our AI 'sees' the website exactly like a human would — analyzing colors, button sizes, text contrast, and layout to detect visual manipulation."
    },
    {
      "term": "Visual Hierarchy Manipulation",
      "definition": "Making the 'Accept' button large and colorful while the 'Decline' button is tiny and gray. This design trick guides your clicks toward the business-preferred action."
    },
    {
      "term": "Drip Pricing",
      "definition": "Showing a low price initially, then adding fees, taxes, and surcharges at checkout. The final price can be 30-50% higher than what was advertised."
    }
  ],
  "graph_phase": [
    {
      "term": "WHOIS Lookup",
      "definition": "A public database that shows who registered a domain name, when, and where. Fraudulent sites often use privacy services to hide their identity."
    },
    {
      "term": "Domain Age",
      "definition": "How long a website has existed. Scam sites are often brand new (registered days ago), while legitimate businesses typically have older domains."
    },
    {
      "term": "Entity Verification",
      "definition": "Cross-checking the company name, address, and claims on the website against business registries, DNS records, and public databases."
    }
  ],
  "judge_phase": [
    {
      "term": "Trust Score",
      "definition": "A 0-100 score computed from 6 independent signals. Like a credit score for websites — higher means more trustworthy."
    },
    {
      "term": "Signal Weighting",
      "definition": "Not all evidence is equal. Our Intelligence Network verification (hard to fake) is weighted more heavily than visual analysis (can be subjective)."
    },
    {
      "term": "Override Rules",
      "definition": "Some findings are so severe they override the calculated score. For example: a website found in phishing databases is automatically marked as high risk, regardless of other signals."
    }
  ]
}
```

#### C. Web Safety Tips (shown on report page)

```json
[
  "Always check the URL bar for the correct domain name before entering credentials.",
  "A padlock (SSL) icon doesn't guarantee the site is safe — it only means the connection is encrypted.",
  "Read cancellation and refund policies before subscribing to any service.",
  "If a deal seems too good to be true, it probably is. Verify the seller independently.",
  "Check website reviews on independent platforms, not just testimonials on the site itself.",
  "Be suspicious of countdown timers and 'limited stock' warnings — they're often fake.",
  "Never enter credit card details on a website that doesn't use HTTPS.",
  "If a website makes it hard to find the cancel button, that's a deliberate design choice."
]
```

### Display Logic

```
ON LANDING PAGE:
  → Show dark pattern carousel with category details

DURING LIVE AUDIT:
  → Between each agent phase transition, show 1 random "Did You Know?" card
  → During any >5s processing gap, show 1 contextual terminology card (matched to current phase)
  → After a finding is detected, show the relevant category educational context
  → Rotate cards every 8 seconds if multiple are queued
  → Never repeat a card within the same audit session (track shown IDs)

ON REPORT PAGE:
  → Show 2-3 Web Safety Tips at the bottom, relevant to findings
  → Each dark pattern finding includes its category's plain-English explanation
```

---

## 10. WebSocket Protocol & Backend API

### Backend Architecture (FastAPI)

```
backend/
  main.py              ← FastAPI app, CORS, lifespan
  requirements.txt     ← fastapi, uvicorn, websockets
  routes/
    audit.py           ← POST /api/audit/start, WS /api/audit/stream/{id}
    health.py          ← GET /api/health
  services/
    audit_runner.py    ← Wraps VeritasOrchestrator, emits WS events
```

### API Endpoints

#### `POST /api/audit/start`
```json
// Request
{
  "url": "https://www.example.com",
  "tier": "standard_audit",
  "verdict_mode": "expert"
}

// Response
{
  "audit_id": "vrts_a1b2c3d4",
  "status": "queued",
  "ws_url": "/api/audit/stream/vrts_a1b2c3d4"
}
```

#### `WS /api/audit/stream/{audit_id}`

WebSocket connection streams typed JSON events:

```typescript
// Event Types
type AuditEvent =
  | { type: "phase_start";    phase: Phase; message: string; pct: number }
  | { type: "phase_complete"; phase: Phase; message: string; pct: number; summary: PhaseSummary }
  | { type: "phase_error";    phase: Phase; message: string; pct: number; error: string }
  | { type: "finding";        finding: Finding }
  | { type: "screenshot";     url: string; label: string; index: number }
  | { type: "stats_update";   stats: AuditStats }
  | { type: "log_entry";      timestamp: string; agent: string; message: string; level: "info"|"warn"|"error" }
  | { type: "site_type";      site_type: string; confidence: number }
  | { type: "security_result"; module: string; result: SecurityResult }
  | { type: "audit_complete"; result: AuditResult }
  | { type: "audit_error";    error: string }

type Phase = "scout" | "security" | "vision" | "graph" | "judge"

type PhaseSummary = {
  scout:    { pages: number; screenshots: number; forms: number; captcha: boolean }
  security: { headers_present: number; headers_total: number; phishing_flagged: boolean; modules: string[] }
  vision:   { findings_count: number; critical_count: number; ai_calls: number }
  graph:    { domain_age_days: number; entity_verified: boolean; inconsistencies: number; nodes: number }
  judge:    { trust_score: number; risk_level: string; signal_scores: Record<string, number> }
}

type Finding = {
  id: string
  category: string             // "visual_interference" | "false_urgency" | etc.
  pattern_type: string         // "hidden_costs" | "fake_countdown" | etc.
  severity: "low" | "medium" | "high" | "critical"
  confidence: number           // 0.0 - 1.0
  description: string          // AI-generated description
  plain_english: string        // Non-technical explanation
  screenshot_index?: number    // Which screenshot it was found in
}

type AuditStats = {
  pages_scanned: number
  screenshots: number
  findings: number
  ai_calls: number
  security_checks: number
  elapsed_seconds: number
}
```

### Frontend WebSocket Hook

```typescript
// hooks/useAuditStream.ts
function useAuditStream(auditId: string) {
  // Returns:
  return {
    // State
    phase: Phase | null,          // Current active phase
    pct: number,                  // 0-100 overall progress
    phases: Record<Phase, PhaseState>, // State of each phase
    findings: Finding[],          // All findings so far
    screenshots: Screenshot[],    // All screenshots captured
    stats: AuditStats,            // Live stats
    logs: LogEntry[],             // Forensic log entries
    siteType: SiteType | null,    // Detected site type
    securityResults: SecurityResult[], // Security module results
    result: AuditResult | null,   // Final result (when complete)
    error: string | null,         // Error message (if any)
    status: "connecting" | "running" | "complete" | "error",
  }
}
```

---

## 11. Component Inventory

### Shared Components

```
components/
  ui/                          ← shadcn/ui base (auto-generated)
    button.tsx
    card.tsx
    badge.tsx
    tooltip.tsx
    dialog.tsx
    tabs.tsx
    progress.tsx
    separator.tsx

  layout/
    Navbar.tsx                 ← Minimal top nav: logo + links
    Footer.tsx                 ← Simple footer
    PageTransition.tsx         ← Framer Motion page wrapper

  ambient/
    ParticleField.tsx          ← tsparticles background (configurable colors)
    GlowOrb.tsx                ← Floating ambient glow orb

  data-display/
    TrustGauge.tsx             ← Animated circular arc gauge (0-100)
    RadarChart.tsx             ← 6-axis radar chart (Recharts)
    SignalBar.tsx              ← Horizontal progress bar with label + score
    StatCounter.tsx            ← Animated counting number
    SeverityBadge.tsx          ← Color-coded severity pill (low/med/high/critical)
    RiskBadge.tsx              ← Risk level badge (trusted → fraudulent)
```

### Landing Page Components

```
  landing/
    HeroSection.tsx            ← Logo animation + tagline + URL input
    URLInput.tsx               ← Glowing input bar with validation
    TierSelector.tsx           ← Three-option radio card group
    SignalShowcase.tsx         ← 6 signal cards with hover expansion
    DarkPatternCarousel.tsx    ← Auto-rotating category cards
    HowItWorks.tsx             ← Scroll-triggered 6-step timeline
    SiteTypeGrid.tsx           ← 5 site type icons with hover detail
```

### Live Audit Components

```
  audit/
    AgentPipeline.tsx          ← Left column: 5 stacked agent cards
    AgentCard.tsx              ← Individual agent card with states
    AgentAnimation.tsx         ← Phase-specific inline animation (scanner, eye, graph, scales)
    NarrativeFeed.tsx          ← Center column: scrolling card feed
    NarrativeCard.tsx          ← Base card for feed entries
    AgentReportCard.tsx        ← Report summary from an agent
    FindingAlertCard.tsx       ← Dark pattern detection alert
    DidYouKnowCard.tsx         ← Educational content card
    PhaseTransitionCard.tsx    ← "Phase X of 5" divider card
    ScreenshotRevealCard.tsx   ← Screenshot with AI analysis overlay
    EvidencePanel.tsx          ← Right sidebar container
    ScreenshotGallery.tsx      ← Thumbnail grid with lightbox
    FindingsList.tsx           ← Scrollable findings list
    LiveStats.tsx              ← Animated stat counters
    ForensicLog.tsx            ← Terminal-style expandable log
    AuditHeader.tsx            ← Top bar with URL + timer
    CompletionOverlay.tsx      ← Celebration/result reveal on audit end
```

### Report Page Components

```
  report/
    ReportHeader.tsx           ← Title + URL + date + mode toggle + PDF button
    TrustScoreHero.tsx         ← Large animated gauge + risk level + narrative
    SignalBreakdown.tsx        ← Radar chart + signal bar list
    DarkPatternGrid.tsx        ← Category tabs + finding detail cards
    FindingDetailCard.tsx      ← Full finding with evidence + explanation
    EntityGraph.tsx            ← Interactive force-directed graph
    EntityDetails.tsx          ← Domain info table
    SecurityPanel.tsx          ← Headers checklist + phishing + forms
    Recommendations.tsx        ← Prioritized action items
    AuditMetadata.tsx          ← Audit info footer
    ReportActions.tsx          ← PDF download + share + new audit
```

### Educational Components

```
  education/
    DidYouKnow.tsx             ← Fact card with source citation
    TermExplainer.tsx          ← Term + definition with icon
    SafetyTip.tsx              ← Actionable safety advice card
    EducationProvider.tsx      ← Context provider managing shown/unshown cards
```

---

## 12. Responsive & Accessibility

### Breakpoints

```
Mobile:   < 768px   → Single column, stacked layout
Tablet:   768-1024px → Two columns (pipeline + narrative, panel below)
Desktop:  > 1024px  → Full three-column layout
Wide:     > 1440px  → Max-width container, centered
```

### Mobile Adaptations

**Live Audit (Mobile):**
- Agent Pipeline → Horizontal scrollable pills at top
- Narrative Feed → Full width, main view
- Evidence Panel → Swipe-up bottom sheet (60vh height)
- Forensic Log → Hidden, accessible via button

**Report (Mobile):**
- Radar Chart + Signal Bars → Stacked vertically
- Entity Graph → Full width, simplified
- All sections → Full width, expandable accordion

### Accessibility

- WCAG 2.1 AA compliance
- All animations respect `prefers-reduced-motion`
- Focus-visible outlines on all interactive elements
- SemanticHTML (`<main>`, `<nav>`, `<article>`, `<section>`)
- Alt text on all screenshots and icons
- ARIA labels on gauge, chart, and graph components
- Keyboard navigable: Tab order follows visual order
- Color is never the only indicator — icons/text accompany all color-coded elements

---

## 13. Implementation Order

### Phase 1: Foundation (Backend API + Frontend Scaffold)

```
Step 1.1: FastAPI Backend
  - Create backend/main.py with CORS
  - Create backend/routes/audit.py (POST + WS endpoints)
  - Create backend/services/audit_runner.py (wraps orchestrator, converts ##PROGRESS → WS events)
  - Create backend/routes/health.py
  - Test: curl POST + wscat connection

Step 1.2: Next.js Scaffold
  - npx create-next-app@latest with App Router + TypeScript + Tailwind
  - Install: framer-motion, recharts, react-force-graph-2d, tsparticles, zustand, lucide-react
  - Configure: shadcn/ui, fonts (Inter + JetBrains Mono), color variables
  - Create: root layout with dark theme + Navbar
```

### Phase 2: Landing Page

```
Step 2.1: Hero + URL Input + Tier Selector
Step 2.2: Signal Showcase (6 cards)
Step 2.3: Dark Pattern Carousel (5 categories)
Step 2.4: How It Works timeline
Step 2.5: Site Type Grid
Step 2.6: Particle background + animations polish
```

### Phase 3: Live Audit Page (The Star)

```
Step 3.1: WebSocket hook (useAuditStream) + Zustand store
Step 3.2: Agent Pipeline (left column) with state management
Step 3.3: Narrative Feed (center) with card components
Step 3.4: Evidence Panel (right) with screenshots + findings + stats
Step 3.5: Forensic Log (bottom)
Step 3.6: Educational content system (DidYouKnow provider + cards)
Step 3.7: Phase-dependent ambient effects
Step 3.8: Completion animation + transition to report
```

### Phase 4: Report Page

```
Step 4.1: Trust Score Gauge + Risk Level
Step 4.2: Radar Chart + Signal Bars
Step 4.3: Dark Pattern Grid + Finding Cards
Step 4.4: Entity Graph + Details
Step 4.5: Security Panel
Step 4.6: Recommendations
Step 4.7: Audit Metadata + Actions (PDF, Share)
Step 4.8: Simple vs Expert mode toggle
```

### Phase 5: Polish & Integration

```
Step 5.1: Page transitions (Framer Motion layout)
Step 5.2: Mobile responsive adaptations
Step 5.3: Loading states + error boundaries
Step 5.4: End-to-end test: start audit → live stream → view report
Step 5.5: Performance optimization (lazy loading, code splitting)
```

---

## Quick Reference: User-Facing Language Map

**NEVER show these internal terms to users:**

| Internal Term | User-Facing Term |
|--------------|-----------------|
| NIM / NVIDIA NIM | AI Engine |
| VLM | AI Vision |
| LLM | AI Analysis |
| Playwright | Browser Agent |
| LangGraph | Audit Pipeline |
| ScoutAgent | Browser Reconnaissance |
| VisionAgent | Visual Intelligence |
| GraphInvestigator | Intelligence Network |
| JudgeAgent | Forensic Judge |
| SecurityNode | Security Audit |
| nim_calls | AI Analysis Calls |
| DOM Analysis | Page Structure Analysis |
| WHOIS | Domain Registry |
| CSP | Content Security Policy *(only in Expert mode)* |

---

## Quick Reference: The 6 Trust Signals

| Signal | Weight | Icon | User Label | What It Checks |
|--------|--------|------|-----------|---------------|
| Visual | 0.20 | 👁️ | Visual Intelligence | Screenshot analysis for dark patterns |
| Structural | 0.15 | 🔍 | Page Structure | DOM, forms, hidden elements |
| Temporal | 0.10 | ⏱️ | Time Analysis | Fake timers, countdown reset detection |
| Graph | 0.25 | 🌐 | Identity Verification | WHOIS, DNS, business registry |
| Meta | 0.10 | 🔒 | Basic Verification | SSL, domain age, metadata |
| Security | 0.20 | 🛡️ | Security Audit | HTTP headers, phishing DB, form security |

---

## Quick Reference: The 5 Dark Pattern Categories

| Category | Icon | Count of Sub-types | Detection Method |
|----------|------|-------------------|-----------------|
| Visual Interference | 🎭 | 5 | Visual (AI Vision) |
| False Urgency | ⏰ | 4 | Temporal (timer comparison) |
| Forced Continuity | 🚪 | 4 | Visual + Structural |
| Sneaking | 🐍 | 4 | Visual + Structural |
| Social Engineering | 🎯 | 4 | Combined (all signals) |

---

## Quick Reference: Risk Levels

| Score Range | Risk Level | Color | Badge |
|------------|------------|-------|-------|
| 90-100 | Trusted | `--risk-safe` (#10B981) | Green shield |
| 70-89 | Probably Safe | Teal | Blue-green shield |
| 40-69 | Suspicious | `--risk-caution` (#F59E0B) | Amber warning |
| 20-39 | High Risk | `--risk-warning` (#F97316) | Orange alert |
| 0-19 | Likely Fraudulent | `--risk-danger` (#EF4444) | Red skull |

---

*This document is the frontend implementation bible. Every design decision, animation, component, and interaction is specified here. When in doubt, read this file.*
