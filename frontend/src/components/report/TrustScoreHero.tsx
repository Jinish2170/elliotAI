"use client";

import { motion } from "framer-motion";
import { TrustGauge } from "@/components/data-display/TrustGauge";
import { RiskBadge } from "@/components/data-display/RiskBadge";

interface TrustScoreHeroProps {
  score: number;
  riskLevel: string;
  narrative: string;
}

export function TrustScoreHero({ score, riskLevel, narrative }: TrustScoreHeroProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="glass-card rounded-2xl p-8 mb-6"
    >
      <h2 className="text-[10px] uppercase tracking-[0.2em] text-[var(--v-text-tertiary)] font-semibold mb-6">
        Trust Score
      </h2>

      <div className="flex flex-col md:flex-row items-center gap-8">
        {/* Gauge */}
        <div className="flex-shrink-0">
          <TrustGauge score={score} size={200} animate={true} />
        </div>

        {/* Details */}
        <div className="flex-1 text-center md:text-left">
          <div className="mb-3">
            <RiskBadge riskLevel={riskLevel} />
          </div>
          <p className="text-sm text-[var(--v-text-secondary)] leading-relaxed max-w-md">
            {narrative}
          </p>
        </div>
      </div>
    </motion.section>
  );
}
