"use client";

import { useEffect, useRef, useState } from "react";

interface StatCounterProps {
  value: number;
  label: string;
  suffix?: string;
  duration?: number;
  className?: string;
}

export function StatCounter({ value, label, suffix = "", duration = 1.2, className = "" }: StatCounterProps) {
  const [display, setDisplay] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const prevValue = useRef(0);

  useEffect(() => {
    const start = prevValue.current;
    const diff = value - start;
    if (diff === 0) return;

    const startTime = performance.now();
    const ms = duration * 1000;

    const tick = (now: number) => {
      const elapsed = now - startTime;
      const t = Math.min(elapsed / ms, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - t, 3);
      const current = Math.round(start + diff * eased);
      setDisplay(current);
      if (t < 1) requestAnimationFrame(tick);
      else prevValue.current = value;
    };

    requestAnimationFrame(tick);
  }, [value, duration]);

  return (
    <div ref={ref} className={`text-center ${className}`}>
      <div className="text-2xl font-bold font-mono text-[var(--v-text)] tabular-nums">
        {display}
        {suffix && <span className="text-sm text-[var(--v-text-tertiary)] ml-0.5">{suffix}</span>}
      </div>
      <div className="text-[10px] uppercase tracking-wider text-[var(--v-text-tertiary)] mt-0.5">
        {label}
      </div>
    </div>
  );
}
