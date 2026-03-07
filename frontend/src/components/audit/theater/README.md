# VERITAS Theater Components

>The "Out Theater" experience for VERITAS autonomous auditing.

## Overview

These components create a cinematic, theater-themed presentation of the autonomous audit process, designed for maximum visual impact and immersive storytelling.

## Components

### AnimatedAgentTheater

**Purpose**: Stage-like presentation where each agent performs their role on a "stage"

**Features**:
- 5 agents positioned strategically on a virtual stage
- Dynamic spotlight effect that follows the active agent
- Dramatic entrance/exit animations
- Personality messaging display with emoji, color coding, and status
- Stage floor visual element
- Background particle effects that react to current phase
- Responsive scaling for different screen sizes

**Usage**:
```tsx
<AnimatedAgentTheater
  phases={store.phases}
  currentPhase={store.currentPhase}
  trustScore={store.result?.trust_score}
/>
```

**Event Requirements**:
- Store must have `phases` object with AgentState per phase
- Each phase includes: `status` (waiting/active/complete/error), `message`, `pct`
- `activePass` and `completedPasses` for Vision phase

---

### TrustScoreReveal

**Purpose**: Dramatic cinematic reveal of the final trust score with celebration effects

**Features**:
- Multi-stage countdown reveal animation
- Score tier based coloring:
  - 90+: Exceptional (emerald) with 💎 emoji
  - 80-89: Excellent (green) with 🎉 emoji
  - 70-79: Good (cyan) with ✅ emoji
  - 50-69: Moderate (amber) with ⚠️ emoji
  - 30-49: Low (orange-red) with 🚨 emoji
  - <30: Very Low (red) with ⛔ emoji
- Confetti celebration for scores >= 80
- Green flag celebration display with categorized indicators
- Shimmer/glow effects on high trust scores
- Verdict text display for narrative

**Usage**:
```tsx
<TrustScoreReveal
  trustScore={trustScore}
  riskLevel={riskLevel}
  greenFlags={greenFlags}
  verdict={verdict}
/>
```

**Event Requirements**:
- `green_flags`: array of GreenFlag objects with id, category, label, icon
- Each GreenFlag structure must match frontend type definition

---

## Data Models

### PhaseState
```typescript
interface PhaseState {
  status: PhaseStatus; // "waiting" | "active" | "complete" | "error"
  message: string;
  pct: number;
  summary?: Record<string, unknown>;
  error?: string;
}
```

### GreenFlag
```typescript
interface GreenFlag {
  id: string;
  category: "security" | "privacy" | "compliance" | "trust";
  label: string;
  icon: string; // emoji
}
```

### AgentPersona
```typescript
interface AgentPersona {
  emoji: string;
  name: string;
  personality: string;
  catchphrases: {
    working: string[];
    complete: string[];
    success: string[];
    error: string[];
  };
  color: string; // Tailwind color class prefix sans "text-" (e.g., "cyan", "emerald")
}
```

## Animation Classes

All animation classes are defined in `frontend/src/app/globals.css`:

- `animate-gradient` - Background gradient animation
- `animate-spotlight` - Pulsing spotlight effect
- `animate-float` - Gentle floating animation
- `animate-reveal` - Reveal animation with blur effect
- `animate-countdown` - Countdown pulse effect
- Tier-specific glows: `tier-excellent`, `tier-good`, `tier-moderate`, `tier-low`, `tier-very-low`

## Performance Considerations

- **Particle Count**: Reduced to 50 for Theater components vs 30 for Dashboard
- **Animation Durations**: Fast-paced (0.5-2s) with reduced motion support
- **Resource Usage**: Components use Framer Motion with will-change animations
- **Browser Compatibility**: All effects work with reduced motion preferences

## Browser Support

- Modern browsers with ES2017+ support
- WebP format for images (handled by Vision Agent)
- Reduced motion via CSS media queries
- Hardware acceleration for smooth 60fps animations

---

*Last Updated: 2026-03-07*
