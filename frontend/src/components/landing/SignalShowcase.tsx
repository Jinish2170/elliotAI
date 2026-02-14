"use client";

import { TRUST_SIGNALS } from "@/lib/education";
import { motion } from "framer-motion";
import { useState } from "react";

export function SignalShowcase() {
  const [hovered, setHovered] = useState<string | null>(null);

  return (
    <section className="relative py-24 px-4">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-14"
        >
          <p className="text-xs uppercase tracking-[0.25em] text-cyan-400 mb-3 font-medium">
            Six Independent Signals
          </p>
          <h2 className="text-3xl font-bold text-[var(--v-text)]">
            What We Analyze
          </h2>
        </motion.div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {TRUST_SIGNALS.map((signal, i) => (
            <motion.div
              key={signal.id}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08, duration: 0.5 }}
              onMouseEnter={() => setHovered(signal.id)}
              onMouseLeave={() => setHovered(null)}
              className={`
                relative group cursor-default rounded-xl border p-5 text-center transition-all duration-300
                ${
                  hovered === signal.id
                    ? "border-cyan-500/40 bg-cyan-500/5 -translate-y-1 shadow-lg shadow-cyan-500/10"
                    : "border-white/5 bg-[var(--v-surface)]"
                }
              `}
            >
              <div className="text-3xl mb-3">{signal.icon}</div>
              <h3 className="text-xs font-semibold text-[var(--v-text)] mb-1">
                {signal.label}
              </h3>
              <p className="text-[10px] text-[var(--v-text-tertiary)]">
                {Math.round(signal.weight * 100)}% weight
              </p>

              {/* Expanded tooltip */}
              <motion.div
                initial={false}
                animate={{
                  opacity: hovered === signal.id ? 1 : 0,
                  y: hovered === signal.id ? 0 : 8,
                  height: hovered === signal.id ? "auto" : 0,
                }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <p className="text-[11px] text-[var(--v-text-secondary)] mt-3 leading-relaxed">
                  {signal.description}
                </p>
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
