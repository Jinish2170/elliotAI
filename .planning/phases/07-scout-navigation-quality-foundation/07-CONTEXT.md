# Phase 7: Scout Navigation & Quality Foundation - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver complete page coverage via scrolling (lazy-loaded content detection) and multi-page exploration (About, Contact, Privacy, footer links), with quality management foundation preventing false positives through multi-factor validation (2+ source consensus) and confidence scoring (0-100%).

</domain>

<decisions>
## Implementation Decisions

### Scrolling behavior

- **Scroll methodology:** Intelligent incremental scroll (page height/2 per scroll), not continuous scroll
- **Scroll duration:** 300-500ms wait after each scroll chunk to allow lazy loading
- **Scroll termination:** Stop when no new content appears for 2 consecutive scroll checkpoints OR maximum 15 scroll cycles
- **Scroll detection:** Use scroll position vs page height + DOM mutation observer for lazy-loaded content
- **Screenshot triggers:** Capture screenshot after each scroll segment and upon scroll termination

### Multi-page exploration

- **Pages to visit:** Automatically discover and visit: About, Contact, Privacy, FAQ, footer links (max 8 pages)
- **Link discovery:** Prioritize nav bar + footer + in-page "Learn More" sections
- **Exploration order:** 1) Landing page (already visited), 2) Legal pages (Privacy, Terms), 3) About pages (About, Team), 4) functional pages (Contact, FAQ), 5) outbound footer links
- **Navigation method:** Follow discovered links, extract all hrefs, deduplicate, prioritize by relevance keywords
- **Exploration limit:** Timeout per page = baseline 15s + lazy loading wait, max 8 pages total

### Quality validation rules

- **Source types for consensus:** Vision Agent, OSINT Agent, Security Agent — multiple findings from these agents count toward consensus
- **Consensus threshold:** 2+ distinct agents must corroborate a finding for "confirmed" status (prevents solo-source false positives)
- **Partial findings:** Single-source findings shown as "unconfirmed" with lower confidence (<50%), displayed separately from confirmed findings
- **Finding confidence tiers:** Confirmed (2+ sources, >=50%), Unconfirmed (1 source, <50%), Pending (insufficient data)
- **Conflict detection:** If one agent flags safe while another flags threat → downgrade to "conflicted" status, show both findings with conflict note

### Confidence scoring

- **Scoring factors:** Source agreement weight (60%), finding severity (25%), contextual confidence (15%)
- **Score calculation:**
  - 2+ sources agree on high-severity → 75-100%
  - 2+ sources agree on medium-severity → 50-75%
  - 1 source high-severity → 40-60% (unconfirmed)
  - 1 source medium-severity → 20-40% (unconfirmed)
- **Visual breakdown:** Show score with contributing factors breakdown (e.g., "87%: 3 sources agree, high severity")
- **Dynamic recalculation:** Scores update in real-time as additional sources contribute findings

### Claude's Discretion

- Exact scroll chunk size (page height/2 vs /3 vs /4)
- Mutation observer debounce timing
- Maximum lazy-load wait before giving up
- Exact confidence score algorithms
- Link discovery heuristics and keyword lists

</decisions>

<specifics>
## Specific Ideas

- Intelligence should be fast but thorough — aggressive lazy loading detection without excessive delays
- 2+ source consensus is critical to prevent false positives from noisy agents
- Confidence scoring should be transparent — users should understand why a finding is/isn't confirmed

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-scout-navigation-quality-foundation*
*Context gathered: 2026-02-26*
