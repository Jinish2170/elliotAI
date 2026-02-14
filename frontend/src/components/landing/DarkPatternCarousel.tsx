"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { DARK_PATTERN_CATEGORIES } from "@/lib/education";

export function DarkPatternCarousel() {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const total = DARK_PATTERN_CATEGORIES.length;

  const next = useCallback(() => setActive((p) => (p + 1) % total), [total]);
  const prev = () => setActive((p) => (p - 1 + total) % total);

  useEffect(() => {
    if (paused) return;
    const timer = setInterval(next, 6000);
    return () => clearInterval(timer);
  }, [paused, next]);

  const cat = DARK_PATTERN_CATEGORIES[active];

  return (
    <section id="dark-patterns" className="relative py-24 px-4">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-14"
        >
          <p className="text-xs uppercase tracking-[0.25em] text-purple-400 mb-3 font-medium">
            5 Categories · 21 Sub-Types
          </p>
          <h2 className="text-3xl font-bold text-[var(--v-text)]">
            Dark Patterns We Detect
          </h2>
        </motion.div>

        {/* Carousel */}
        <div
          className="relative"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => setPaused(false)}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={cat.id}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -40 }}
              transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
              className="glass-card rounded-2xl p-8 sm:p-10"
            >
              <div className="flex items-center gap-4 mb-6">
                <span className="text-4xl">{cat.icon}</span>
                <div>
                  <h3 className="text-xl font-bold text-[var(--v-text)]">{cat.name}</h3>
                  <p className="text-xs text-[var(--v-text-tertiary)]">
                    {cat.subTypes} detection patterns · Severity: {cat.severity}
                  </p>
                </div>
              </div>

              <p className="text-sm text-[var(--v-text-secondary)] mb-6 leading-relaxed">
                {cat.description}
              </p>

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-[var(--v-text-tertiary)] mb-2">
                  Real-World Examples
                </p>
                {cat.examples.map((ex, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 text-sm text-[var(--v-text-secondary)]"
                  >
                    <span className="text-red-400 mt-0.5">•</span>
                    <span>{ex}</span>
                  </div>
                ))}
              </div>

              {/* Severity bar */}
              <div className="mt-6">
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-[var(--v-text-tertiary)]">Detection Severity</span>
                  <span className={cat.severity === "Critical" ? "text-red-400" : "text-amber-400"}>
                    {cat.severity}
                  </span>
                </div>
                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: cat.severity === "Critical" ? "90%" : "70%" }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={`h-full rounded-full ${
                      cat.severity === "Critical"
                        ? "bg-gradient-to-r from-red-500 to-orange-500"
                        : "bg-gradient-to-r from-amber-500 to-yellow-500"
                    }`}
                  />
                </div>
              </div>
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex items-center justify-center gap-4 mt-6">
            <button
              onClick={prev}
              className="p-2 rounded-lg border border-white/10 hover:border-white/20 text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <div className="flex gap-2">
              {DARK_PATTERN_CATEGORIES.map((_, i) => (
                <button
                  key={i}
                  onClick={() => setActive(i)}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${
                    i === active
                      ? "bg-purple-500 w-6"
                      : "bg-white/20 hover:bg-white/30"
                  }`}
                />
              ))}
            </div>

            <button
              onClick={next}
              className="p-2 rounded-lg border border-white/10 hover:border-white/20 text-[var(--v-text-secondary)] hover:text-[var(--v-text)] transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
