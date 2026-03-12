"use client";

/* ========================================
   EvidenceStack — Stacked Evidence Panels
   Replaces tabbed EvidencePanel with Bloomberg stacked layout.
   Screenshots + Metrics + OSINT — all visible simultaneously.
   ======================================== */

import { cn } from "@/lib/utils";
import { PanelChrome } from "@/components/layout/PanelChrome";
import type { AuditStats, Finding, Screenshot } from "@/lib/types";
import type { OSINTResult } from "@/lib/types";
import { Camera, BarChart3, Globe, ExternalLink } from "lucide-react";
import { useMemo, useState } from "react";

interface EvidenceStackProps {
  screenshots: Screenshot[];
  findings: Finding[];
  stats: AuditStats;
  osintResults?: OSINTResult[];
  trustScore?: number | null;
  domainInfo?: {
    domain?: string;
    registrar?: string;
    created?: string;
    whois_privacy?: boolean;
    hosting?: string;
    ssl_issuer?: string;
    ip?: string;
    asn?: string;
  } | null;
  className?: string;
}

export function EvidenceStack({
  screenshots,
  findings,
  stats,
  osintResults = [],
  trustScore,
  domainInfo,
  className,
}: EvidenceStackProps) {
  return (
    <div className={cn("flex flex-col gap-2 overflow-y-auto", className)}>
      {/* Screenshots panel */}
      <PanelChrome
        title="Screenshots"
        icon={<Camera className="w-3.5 h-3.5" />}
        count={screenshots.length}
        elevation={2}
        collapsible
        defaultCollapsed={screenshots.length === 0}
      >
        <div className="p-2">
          {screenshots.length === 0 ? (
            <p className="text-[11px] text-[var(--v-text-tertiary)] text-center py-4">
              No screenshots yet
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-1.5">
              {screenshots.map((ss) => (
                <ScreenshotThumbnail key={ss.index} screenshot={ss} />
              ))}
            </div>
          )}
        </div>
      </PanelChrome>

      {/* Metrics panel */}
      <PanelChrome
        title="Metrics"
        icon={<BarChart3 className="w-3.5 h-3.5" />}
        elevation={2}
        collapsible
      >
        <div className="p-2 space-y-1.5">
          <MetricRow label="Trust Score" value={trustScore != null ? trustScore.toString() : "—"} status={trustScore != null ? (trustScore >= 70 ? "pass" : trustScore >= 40 ? "warn" : "fail") : "pending"} />
          <MetricRow
            label="Pages Analyzed"
            value={stats.pages_scanned.toString()}
          />
          <MetricRow
            label="Unique Findings"
            value={stats.findings.toString()}
            status={stats.findings > 10 ? "fail" : stats.findings > 0 ? "warn" : "pass"}
          />
          <MetricRow
            label="Screenshots"
            value={stats.screenshots.toString()}
          />
          <MetricRow
            label="Time Elapsed"
            value={`${stats.elapsed_seconds.toFixed(1)}s`}
          />
          <MetricRow
            label="AI Calls"
            value={stats.ai_calls.toString()}
          />
          <MetricRow
            label="Sec Checks"
            value={stats.security_checks.toString()}
          />
        </div>
      </PanelChrome>

      {/* OSINT panel */}
      <PanelChrome
        title="OSINT"
        icon={<Globe className="w-3.5 h-3.5" />}
        count={osintResults.length}
        elevation={2}
        collapsible
        defaultCollapsed={!domainInfo && osintResults.length === 0}
      >
        <div className="p-2 space-y-1">
          {domainInfo ? (
            <>
              {domainInfo.domain && (
                <OsintRow label="Domain" value={domainInfo.domain} />
              )}
              {domainInfo.registrar && (
                <OsintRow label="Registrar" value={domainInfo.registrar} />
              )}
              {domainInfo.created && (
                <OsintRow label="Created" value={domainInfo.created} />
              )}
              {domainInfo.whois_privacy !== undefined && (
                <OsintRow
                  label="WHOIS"
                  value={domainInfo.whois_privacy ? "Privacy Protected" : "Public"}
                />
              )}
              {domainInfo.hosting && (
                <OsintRow label="Hosting" value={domainInfo.hosting} />
              )}
              {domainInfo.ssl_issuer && (
                <OsintRow label="SSL Issuer" value={domainInfo.ssl_issuer} />
              )}
              {domainInfo.ip && (
                <OsintRow label="IP" value={domainInfo.ip} />
              )}
              {domainInfo.asn && (
                <OsintRow label="ASN" value={domainInfo.asn} />
              )}
            </>
          ) : osintResults.length > 0 ? (
            osintResults.slice(0, 8).map((r, i) => (
              <OsintRow
                key={i}
                label={r.source || `Source ${i + 1}`}
                value={r.query_value || r.status || "—"}
              />
            ))
          ) : (
            <p className="text-[11px] text-[var(--v-text-tertiary)] text-center py-4">
              Awaiting OSINT data...
            </p>
          )}
        </div>
      </PanelChrome>
    </div>
  );
}

/* ── Screenshot thumbnail ── */

function ScreenshotThumbnail({ screenshot }: { screenshot: Screenshot }) {
  const [expanded, setExpanded] = useState(false);
  const label = screenshot.label || screenshot.url;
  const shortLabel =
    label.length > 20 ? label.slice(0, 20) + "…" : label;

  return (
    <>
      <button
        onClick={() => setExpanded(true)}
        className="group relative rounded overflow-hidden border border-[rgba(255,255,255,0.06)] hover:border-[rgba(255,255,255,0.2)] transition-all hover:scale-[1.03] duration-150"
      >
        {screenshot.data ? (
          <img
            src={`data:image/png;base64,${screenshot.data}`}
            alt={label}
            className="w-full h-[60px] object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-[60px] bg-[rgba(255,255,255,0.04)] flex items-center justify-center">
            <Camera className="w-4 h-4 text-[var(--v-text-tertiary)]" />
          </div>
        )}
        <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent px-1 py-0.5">
          <span className="text-[8px] font-mono text-[var(--v-text-secondary)] truncate block">
            {shortLabel}
          </span>
        </div>
      </button>

      {/* Expanded overlay */}
      {expanded && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          onClick={() => setExpanded(false)}
        >
          <div
            className="relative max-w-[90vw] max-h-[90vh] elev-5 rounded-lg overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {screenshot.data && (
              <img
                src={`data:image/png;base64,${screenshot.data}`}
                alt={label}
                className="max-w-full max-h-[85vh] object-contain"
              />
            )}
            {/* Overlay bounding boxes for findings */}
            {screenshot.overlays?.map((overlay, i) => (
              <div
                key={i}
                className="absolute border-2 rounded-sm pointer-events-none"
                style={{
                  left: `${overlay.bbox[0]}%`,
                  top: `${overlay.bbox[1]}%`,
                  width: `${overlay.bbox[2]}%`,
                  height: `${overlay.bbox[3]}%`,
                  borderColor:
                    overlay.severity === "critical"
                      ? "#EF4444"
                      : overlay.severity === "high"
                      ? "#F59E0B"
                      : "#3B82F6",
                  background: `rgba(239, 68, 68, ${overlay.opacity || 0.1})`,
                }}
              />
            ))}
            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/90 to-transparent p-3">
              <span className="text-[12px] font-mono text-white">{label}</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

/* ── Metric row ── */

function MetricRow({
  label,
  value,
  status,
}: {
  label: string;
  value: string;
  status?: "pass" | "fail" | "warn" | "pending";
}) {
  const statusColor =
    status === "pass"
      ? "text-[var(--v-safe)]"
      : status === "fail"
      ? "text-[var(--v-danger)]"
      : status === "warn"
      ? "text-[var(--v-caution)]"
      : "";

  return (
    <div className="flex items-center justify-between">
      <span className="text-data-label">{label}</span>
      <span className={cn("text-[13px] font-mono font-bold text-[var(--v-text)]", statusColor)}>
        {value}
      </span>
    </div>
  );
}

/* ── OSINT row ── */

function OsintRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-2">
      <span className="text-data-label shrink-0">{label}</span>
      <span className="text-[11px] font-mono text-[var(--v-text-secondary)] text-right truncate">
        {value}
      </span>
    </div>
  );
}
