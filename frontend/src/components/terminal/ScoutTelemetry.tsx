"use client";
import React from "react";
import { GhostPanel } from "./TerminalPanel";
import type { NavigationStartEvent, NavigationCompleteEvent, ScrollEvent, ExplorationPath, FormDetection, CaptchaResult, PageScannedEvent } from "@/lib/types";

interface Props {
  explorationPath: ExplorationPath | null;
  formDetections: FormDetection[];
  captchaResults: CaptchaResult[];
  pagesScanned: number;
}

export function ScoutTelemetry({ explorationPath, formDetections, captchaResults, pagesScanned }: Props) {
  const isEmpty = !explorationPath && !formDetections?.length && !captchaResults?.length && !pagesScanned;
  if (isEmpty) return <GhostPanel message="SCOUT TELEMETRY - AWAITING DATA" />;

  return (
    <div className="w-full h-full overflow-y-auto p-3 flex flex-col gap-4 align-top items-start">
      <div className="w-full flex justify-between border-b border-[var(--t-dim)] pb-2 mb-2">
        <div className="text-[10px] flex flex-col gap-1">
          <span className="text-[var(--t-dim)]">PAGES SCANNED</span>
          <span className="text-[var(--t-green)] text-lg">{pagesScanned}</span>
        </div>
        <div className="text-[10px] flex flex-col gap-1 text-right">
          <span className="text-[var(--t-dim)]">RUNTIME (ms)</span>
          <span className="text-[var(--t-text)] text-lg">{explorationPath?.total_time_ms || 0}</span>
        </div>
      </div>

      {explorationPath && (
        <div className="w-full flex-col gap-2 min-w-0">
          <div className="text-[10px] text-[var(--t-text)] border-b border-[var(--t-border)] pb-1 shrink-0 mb-2">
            EXPLORATION_PATH <span className="opacity-70">[{explorationPath.visited_urls.length}]</span>
          </div>
          <div className="flex flex-col gap-1">
            {explorationPath.visited_urls.slice(0, 5).map((url, i) => (
              <div key={i} className="text-[9px] flex items-center gap-2 bg-[#111] p-1 border-l border-[var(--t-dim)]">
                <span className="text-[var(--t-dim)]">[{i + 1}]</span>
                <span className="truncate text-[var(--t-text)]">{url}</span>
              </div>
            ))}
            {explorationPath.visited_urls.length > 5 && (
              <div className="text-[9px] text-[var(--t-dim)] pl-2">...and {explorationPath.visited_urls.length - 5} more</div>
            )}
          </div>
        </div>
      )}

      {/* Forms & Captchas */}
      <div className="flex w-full gap-4 mt-2">
        <div className="flex-1 flex flex-col gap-2 min-w-0">
          <div className="text-[10px] text-[var(--t-amber)] border-b border-[var(--t-amber)] pb-1 shrink-0">
            FORMS_DETECTED <span className="opacity-70">[{formDetections?.length || 0}]</span>
          </div>
          <div className="flex flex-col gap-1">
            {formDetections?.slice(0, 3).map((formEvent, i) => (
              <div key={i} className="text-[9px] flex flex-col gap-1 bg-[#111] p-1.5 border-l border-[var(--t-amber)]">
                {formEvent.forms.map((f, j) => (
                  <div key={j} className="flex justify-between">
                    <span className="font-bold">{f.method.toUpperCase()} FORM</span>
                    <span className="opacity-70">Inputs: {f.inputs} {f.has_password && "(PWD)"}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
        <div className="flex-1 flex flex-col gap-2 min-w-0 border-l border-[var(--t-border)] pl-4">
          <div className="text-[10px] text-[var(--t-red)] border-b border-[var(--t-red)] pb-1 shrink-0">
            CAPTCHA_DETECTED <span className="opacity-70">[{captchaResults?.length || 0}]</span>
          </div>
          <div className="flex flex-col gap-1">
            {captchaResults?.map((captcha, i) => (
              <div key={i} className="text-[9px] bg-[#111] p-1.5 border-l border-[var(--t-red)]">
                <span className="font-bold">{captcha.captcha_type?.toUpperCase() || "UNKNOWN"}</span>
                <span className="opacity-70 block">Status: {captcha.detected ? "DETECTED" : "CLEARED"}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
