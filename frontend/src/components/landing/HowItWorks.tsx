"use client";

import { motion } from "framer-motion";

const STEPS = [
  {
    num: 1,
    icon: "🔎",
    title: "Browser Reconnaissance",
    description: "A stealth browser agent visits the website, captures screenshots, analyzes page structure, and collects evidence — all without triggering anti-bot systems.",
    time: "~30s",
  },
  {
    num: 2,
    icon: "🛡️",
    title: "Security Audit",
    description: "HTTP security headers are checked, the URL is cross-referenced with phishing databases, and form security is analyzed for vulnerabilities.",
    time: "~15s",
  },
  {
    num: 3,
    icon: "👁️",
    title: "Visual Intelligence",
    description: "AI vision examines every screenshot for dark patterns — hidden buttons, misleading layouts, deceptive color hierarchies, and visual manipulation.",
    time: "~45s",
  },
  {
    num: 4,
    icon: "🌐",
    title: "Intelligence Network",
    description: "Domain records, WHOIS data, DNS entries, and business registries are cross-referenced to verify the website's claimed identity.",
    time: "~30s",
  },
  {
    num: 5,
    icon: "⚖️",
    title: "Forensic Judge",
    description: "An AI judge weighs all evidence from every agent, computes the trust score, and determines risk level with override rules for critical findings.",
    time: "~10s",
  },
  {
    num: 6,
    icon: "📋",
    title: "Report Generation",
    description: "A comprehensive forensic report is generated with trust scores, signal breakdowns, dark pattern evidence, and actionable recommendations.",
    time: "Instant",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="relative py-24 px-4">
      <div className="max-w-3xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <p className="text-xs uppercase tracking-[0.25em] text-cyan-400 mb-3 font-medium">
            6-Phase Forensic Pipeline
          </p>
          <h2 className="text-3xl font-bold text-[var(--v-text)]">
            How Veritas Works
          </h2>
        </motion.div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-cyan-500/40 via-purple-500/40 to-emerald-500/40" />

          <div className="space-y-8">
            {STEPS.map((step, i) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-50px" }}
                transition={{
                  duration: 0.5,
                  delay: i * 0.12,
                  ease: [0.25, 0.46, 0.45, 0.94],
                }}
                className="relative flex items-start gap-6 group"
              >
                {/* Node */}
                <div className="relative z-10 flex-shrink-0 w-12 h-12 rounded-xl bg-[var(--v-surface)] border border-white/10 flex items-center justify-center text-xl group-hover:border-cyan-500/40 group-hover:shadow-[0_0_20px_rgba(6,182,212,0.15)] transition-all duration-300">
                  {step.icon}
                </div>

                {/* Content */}
                <div className="flex-1 pb-2">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="text-xs font-mono text-[var(--v-text-tertiary)]">
                      STEP {step.num}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full border border-white/10 text-[var(--v-text-tertiary)]">
                      {step.time}
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-[var(--v-text)] mb-1">
                    {step.title}
                  </h3>
                  <p className="text-sm text-[var(--v-text-secondary)] leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
