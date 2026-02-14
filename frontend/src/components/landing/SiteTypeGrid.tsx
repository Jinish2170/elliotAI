"use client";

import { motion } from "framer-motion";
import { SITE_TYPES } from "@/lib/education";

export function SiteTypeGrid() {
  return (
    <section id="site-types" className="relative py-24 px-4">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-14"
        >
          <p className="text-xs uppercase tracking-[0.25em] text-cyan-400 mb-3 font-medium">
            Adaptive Analysis
          </p>
          <h2 className="text-3xl font-bold text-[var(--v-text)] mb-3">
            Trust Across Domains
          </h2>
          <p className="text-sm text-[var(--v-text-secondary)] max-w-lg mx-auto">
            Veritas adapts its analysis to each website type, using specialized detection
            strategies for different industries.
          </p>
        </motion.div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
          {SITE_TYPES.map((st, i) => (
            <motion.div
              key={st.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{
                duration: 0.4,
                delay: i * 0.08,
                ease: [0.25, 0.46, 0.45, 0.94],
              }}
              className="group relative glass-card rounded-xl p-5 text-center hover:border-cyan-500/30 hover:shadow-[0_0_20px_rgba(6,182,212,0.1)] transition-all duration-300 cursor-default"
            >
              <div className="text-3xl mb-3 group-hover:scale-110 transition-transform duration-300">
                {st.icon}
              </div>
              <h3 className="text-sm font-semibold text-[var(--v-text)] mb-1">
                {st.label}
              </h3>
              <p className="text-xs text-[var(--v-text-tertiary)] leading-relaxed opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                {st.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
