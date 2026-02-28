/* ========================================
   Veritas — Agent Personality System
   Character-based communication for Agent Theater
   ======================================== */

import type { Phase } from "@/lib/types";

export type PersonalityContext = "working" | "complete" | "success" | "error";

export interface AgentPersona {
  emoji: string;
  name: string;
  personality: string;
  catchphrases: {
    working: string[];
    complete: string[];
    success: string[];
    error: string[];
  };
  color: string;
}

/**
 * Agent personality configurations with character traits and catchphrases
 */
export const AGENT_PERSONALITIES: Record<Exclude<Phase, "init">, AgentPersona> = {
  scout: {
    emoji: "🕵️",
    name: "Stealth Scout",
    personality: "Cautious observer, discovers the terrain",
    catchphrases: {
      working: [
        "Scouting the perimeter...",
        "Navigating through the shadows...",
        "Mapping the digital landscape...",
        "Quietly observing...",
        "Gathering intel...",
      ],
      complete: [
        "Map complete! {count} pages discovered.",
        "Reconnaissance finished. {count} routes mapped.",
        "Terrain scanned. {count} landmarks found.",
        "Area secured. {count} locations catalogued.",
        "Navigation complete! {count} pages analyzed.",
      ],
      success: [
        "Landed safely!",
        "Clear path ahead!",
        "Mission accomplished!",
        "All clear!",
        "Stealth mode success!",
      ],
      error: [
        "Navigation blocked...",
        "Path obstructed...",
        "Can't proceed...",
        "Trail gone cold...",
        "Access denied...",
      ],
    },
    color: "cyan",
  },

  vision: {
    emoji: "👁️",
    name: "Vision Agent",
    personality: "Detail-oriented pattern detector",
    catchphrases: {
      working: [
        "Analyzing visual patterns...",
        "Scanning for dark patterns...",
        "Examining UI deception...",
        "Processing screenshots...",
        "Detecting visual cues...",
      ],
      complete: [
        "Visual scan complete! {count} findings detected.",
        "Pattern analysis finished. {count} deceptive elements found.",
        "Screen sweep done. {count} issues identified.",
        "Vision test passed. {count} anomalies located.",
        "Spectral analysis complete! {count} patterns exposed.",
      ],
      success: [
        "Pattern identified!",
        "Vision is clear!",
        "Target acquired!",
        "All patterns detected!",
        "Perfect sight line!",
      ],
      error: [
        "Visual obscured...",
        "Image corrupted...",
        "Blurry signal...",
        "Low visibility...",
        "Dark pattern invisible...",
      ],
    },
    color: "purple",
  },

  security: {
    emoji: "🛡️",
    name: "Security Sentinel",
    personality: "Protective auditor, checks all locks",
    catchphrases: {
      working: [
        "Checking security headers...",
        "Verifying SSL certificates...",
        "Analyzing encryption...",
        "Testing firewalls...",
        "Scanning for vulnerabilities...",
      ],
      complete: [
        "Security audit complete! {count} checks passed.",
        "Barrier test finished. {count} defenses verified.",
        "Safety inspection done. {count} protocols confirmed.",
        "Shield status active! {count} layers intact.",
        "Fortress scan complete! {count} gates locked.",
      ],
      success: [
        "All systems secure!",
        "Fortress holds!",
        "Walls are strong!",
        "No breaches found!",
        "Security solid!",
      ],
      error: [
        "Security breach detected...",
        "Compromise confirmed...",
        "Lock is broken...",
        "Intruder alert...",
        "Shield failed...",
      ],
    },
    color: "emerald",
  },

  graph: {
    emoji: "🌐",
    name: "Network Investigator",
    personality: "Investigative connector, reveals hidden ties",
    catchphrases: {
      working: [
        "Cross-referencing entities...",
        "Tracing connections...",
        "Building relationship graph...",
        "Following the data trail...",
        "Mapping the network...",
      ],
      complete: [
        "Network analysis complete! {count} entities verified.",
        "Graph mapping finished. {count} connections established.",
        "Link analysis done. {count} relationships confirmed.",
        "Web investigation complete! {count} nodes resolved.",
        "Connection matrix built! {count} ties identified.",
      ],
      success: [
        "Connection established!",
        "Web untangled!",
        "Path found!",
        "Links confirmed!",
        "Network secure!",
      ],
      error: [
        "Network unreachable...",
        "Connection failed...",
        "Dead end...",
        "Node missing...",
        "Link broken...",
      ],
    },
    color: "amber",
  },

  judge: {
    emoji: "⚖️",
    name: "Forensic Judge",
    personality: "Authoritative adjudicator, weighs all evidence",
    catchphrases: {
      working: [
        "Weighing all evidence...",
        "Examining the case file...",
        "Balancing the scales...",
        "Reviewing testimony...",
        "Finalizing the verdict...",
      ],
      complete: [
        "Verdict complete! Trust score: {score}.",
        "Judgment rendered. Score: {score}.",
        "Final decision: {score}.",
        "Case closed. Rating: {score}.",
        "Justice served! Trustworthiness: {score}.",
      ],
      success: [
        "Justice served!",
        "Fair verdict rendered!",
        "Court is adjourned!",
        "Case closed!",
        "Truth prevails!",
      ],
      error: [
        "Evidence insufficient...",
        "Case inconclusive...",
        "Witness unreliable...",
        "Missing documents...",
        "Data conflict...",
      ],
    },
    color: "rose",
  },
};

/**
 * Get a personality message for a specific agent and context
 * @param agent - The agent phase
 * @param context - The context (working, complete, success, error)
 * @param params - Optional parameters for variable substitution
 * @returns A formatted personality message
 */
export function getPersonalityMessage(
  agent: Phase,
  context: PersonalityContext,
  params?: Record<string, number | string>
): string {
  // Skip init phase
  if (agent === "init") {
    return "Initializing audit...";
  }

  const persona = AGENT_PERSONALITIES[agent as Exclude<Phase, "init">];
  if (!persona) {
    return "Agent message...";
  }

  const messages = persona.catchphrases[context];
  const template = messages[Math.floor(Math.random() * messages.length)];

  // Replace variables like {count}, {score} with provided params
  let result = template;
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      result = result.replace(`{${key}}`, String(value));
    });
  }

  return result;
}

/**
 * Get a random working message for an agent
 */
export function getWorkingMessage(agent: Phase): string {
  return getPersonalityMessage(agent, "working");
}

/**
 * Get a completion message with dynamic parameters
 */
export function getCompletionMessage(agent: Phase, count?: number, score?: number): string {
  return getPersonalityMessage(agent, "complete", {
    count: count ?? 0,
    score: score ?? 0,
  });
}

/**
 * Get a success message for an agent
 */
export function getSuccessMessage(agent: Phase): string {
  return getPersonalityMessage(agent, "success");
}

/**
 * Get an error message for an agent
 */
export function getErrorMessage(agent: Phase): string {
  return getPersonalityMessage(agent, "error");
}
