"use client";
import React, { useEffect, useRef, useState } from "react";
import { GhostPanel } from "./TerminalPanel";
import { Finding } from "@/lib/types";

interface AdvancedGraphProps {
  findings?: Finding[];
  knowledgeGraph?: { nodes: any[], edges: any[] } | null;
}

export function KnowledgeGraph({ findings = [], knowledgeGraph = null }: AdvancedGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [simNodes, setSimNodes] = useState<any[]>([]);
  const [simLinks, setSimLinks] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const animationRef = useRef<number>(0);

  // Initialize nodes based on real graph data OR fallback to findings
  useEffect(() => {
    let rawNodes: any[] = [];
    let rawEdges: any[] = [];

    if (knowledgeGraph && knowledgeGraph.nodes && knowledgeGraph.nodes.length > 0) {
      // Use real generated graph
      rawNodes = knowledgeGraph.nodes.map((n: any, idx: number) => {
        const type = n.node_type || n.type || "NODE";
        return {
          id: n.id || 'node-'+idx,
          label: n.label || type,
          type: type,
          isRoot: n.id === "root" || idx === 0,
          raw: n,
          color: ["threat", "IOCNode", "MITRETacticNode", "ClaimNode"].includes(type) ? "var(--t-red)" : ["agent_result", "EvidenceNode", "EntityNode", "OSINTSourceNode"].includes(type) ? "var(--t-amber)" : "var(--t-cyan)"
        };
      });

      const nodeMap = new Map(rawNodes.map(n => [n.id, n]));
      rawEdges = (knowledgeGraph.edges || []).map((e: any) => ({
        source: nodeMap.get(e.source) || rawNodes[0],
        target: nodeMap.get(e.target) || rawNodes[0],
        type: e.edge_type || e.type || "link"
      }));
    } else if (findings && findings.length > 0) {
      // Create root node
      const root = { id: "root", label: "TARGET.DOM", type: "root", isRoot: true, color: "var(--t-green)" };
      rawNodes.push(root);

      findings.forEach((f, i) => {
        const color = f.severity === "critical" || f.severity === "high" ? "var(--t-red)" : f.severity === "medium" ? "var(--t-amber)" : "var(--t-green)";
        const node = { id: f.id || 'f-'+i, label: f.category || "FINDING", type: "finding", isRoot: false, color, raw: f };
        rawNodes.push(node);
        rawEdges.push({ source: root, target: node });
      });
    }

    // Assign random initial positions
    const finalNodes = rawNodes.map(n => ({
      ...n,
      x: 150 + (Math.random() * 80 - 40),
      y: 150 + (Math.random() * 80 - 40),
      vx: 0,
      vy: 0
    }));

    setSimNodes(finalNodes);
    setSimLinks(rawEdges);
  }, [findings, knowledgeGraph]);

  // Simulation step
  useEffect(() => {
    if (simNodes.length === 0) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: false }); // Optimization
    if (!ctx) return;

    let targetW = canvas.offsetWidth;
    let targetH = canvas.offsetHeight;
    if (canvas.width !== targetW) canvas.width = targetW;
    canvas.height = canvas.parentElement?.clientHeight || 300;
    const W = canvas.width;
    const H = canvas.height;

    let time = 0;

    const tick = () => {
      time += 0.05;
      const centerForce = 0.04;
      const repelForce = 150;
      const springLength = 60;
      const springK = 0.03;
      const damping = 0.8;

      // Reset root to center with slight orbital shift
      if (simNodes[0]) {
        simNodes[0].x = W / 2 + Math.cos(time) * 5;
        simNodes[0].y = H / 2 + Math.sin(time) * 5;
      }

      // Apply forces
      for (let i = 1; i < simNodes.length; i++) {
        const n1 = simNodes[i];
        n1.vx += (W/2 - n1.x) * centerForce;
        n1.vy += (H/2 - n1.y) * centerForce;
        for (let j = 0; j < simNodes.length; j++) {
          if (i === j) continue;
          const n2 = simNodes[j];
          const dx = n1.x - n2.x;
          const dy = n1.y - n2.y;
          const distSq = dx*dx + dy*dy;
          if (distSq > 0 && distSq < 15000) {
            const f = repelForce / distSq;
            n1.vx += dx * f;
            n1.vy += dy * f;
          }
        }
      }

      // Apply spring along links
      for (const link of simLinks) {
        if (!link.target || !link.source) continue;
        const dx = link.target.x - link.source.x;
        const dy = link.target.y - link.source.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist > 0) {
          const f = (dist - springLength) * springK;
          const fx = (dx / dist) * f;
          const fy = (dy / dist) * f;
          if (!link.target.isRoot) { link.target.vx -= fx; link.target.vy -= fy; }
          if (!link.source.isRoot) { link.source.vx += fx; link.source.vy += fy; }
        }
      }

      // Draw Background
      ctx.fillStyle = "#050505";
      ctx.fillRect(0, 0, W, H);

      // Draw Grid lines
      ctx.strokeStyle = "rgba(0, 255, 65, 0.03)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      for(let x=0; x<W; x+=20) { ctx.moveTo(x,0); ctx.lineTo(x,H); }
      for(let y=0; y<H; y+=20) { ctx.moveTo(0,y); ctx.lineTo(W,y); }
      ctx.stroke();

        // Draw links
      ctx.lineWidth = 1.0;
      for (const link of simLinks) {
        if (!link.target || !link.source) continue;
        if (!Number.isFinite(link.source.x) || !Number.isFinite(link.target.x) || !Number.isFinite(link.source.y) || !Number.isFinite(link.target.y)) continue;
        
        ctx.strokeStyle = "rgba(0,255,65,0.2)";
        if (link.type === "has_vulnerability") ctx.strokeStyle = "rgba(239, 68, 68, 0.4)";
        else if (link.type === "resolves_to" || link.type === "associated_with") ctx.strokeStyle = "rgba(56, 189, 248, 0.3)";

        ctx.beginPath();
        ctx.moveTo(link.source.x, link.source.y);
        ctx.lineTo(link.target.x, link.target.y);
        ctx.stroke();

        // Flow dots mapping
        const flowPos = (time * 0.4 + Math.random()*0.05) % 1;
        const dotX = link.source.x + (link.target.x - link.source.x) * flowPos;
        const dotY = link.source.y + (link.target.y - link.source.y) * flowPos;
        ctx.fillStyle = ctx.strokeStyle;
        ctx.beginPath();
        ctx.arc(dotX, dotY, 2, 0, Math.PI*2);
        ctx.fill();
      }

      // Draw nodes
      for (const n of simNodes) {
        if (!n.isRoot) {
          n.vx *= damping;
          n.vy *= damping;
          n.x += n.vx;
          n.y += n.vy;
          n.x = Math.max(15, Math.min(W - 15, n.x));
          n.y = Math.max(15, Math.min(H - 15, n.y));
        }

        const colorStr = getComputedStyle(document.documentElement).getPropertyValue(n.color.replace('var(', '').replace(')', '')) || "#00FF41";
        
        // Advanced icons rendering
        let iconChar = "●";
        let iconFont = "12px 'JetBrains Mono', monospace";
        if (n.type === "IOCNode") iconChar = "⚡";
        else if (n.type === "MITRETacticNode") iconChar = "⚔️";
        else if (n.type === "OSINTSourceNode") iconChar = "🌐";
        else if (n.type === "EntityNode") iconChar = "👤";
        else if (n.type === "threat") iconChar = "💀";
        else if (n.isRoot) iconChar = "🎯";

        ctx.shadowColor = colorStr;
        ctx.shadowBlur = n.isRoot ? 20 : 10;
        
        ctx.fillStyle = colorStr;
        // Central circle behind icon
        ctx.beginPath();
        if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
        ctx.arc(n.x, n.y, n.isRoot ? 9 : 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0; // reset

        // Draw icon
        ctx.fillStyle = "#fff";
        ctx.font = iconFont;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(iconChar, n.x, n.y);

        if (n.isRoot || simNodes.length < 25) {
          ctx.fillStyle = "rgba(255,255,255,0.8)";
          ctx.font = n.isRoot ? "bold 10px 'JetBrains Mono', monospace" : "9px 'JetBrains Mono', monospace";
          ctx.textAlign = "center";
          ctx.fillText(n.label.substring(0,14), n.x, n.y + 14);
        }
      }

      animationRef.current = requestAnimationFrame(tick);
    };

    tick();
    return () => cancelAnimationFrame(animationRef.current);
  }, [simNodes, simLinks]);

  const totalNodes = simNodes.length;
  if (totalNodes === 0) return <GhostPanel message="AWAITING TOPOLOGY MAP" />;

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Find nearest node
    let nearest = null;
    let minDist = 20 * 20; // 20px radius click tolerance
    for (const n of simNodes) {
      if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
      const dx = n.x - x;
      const dy = n.y - y;
      const distSq = dx*dx + dy*dy;
      if (distSq < minDist) {
        minDist = distSq;
        nearest = n;
      }
    }
    setSelectedNode(nearest);
  };

  return (
    <div className="w-full h-full relative bg-[#050505] overflow-hidden group">
      <div className="absolute top-2 left-2 text-[10px] text-[var(--t-dim)] z-10 select-none uppercase font-mono bg-black/60 p-1 border border-white/5 rounded-sm">
        <div className="text-[var(--t-green)]">TOPOLOGY.DETECT</div>
        NODES: {totalNodes} <br />
        LINKS: {simLinks.length}
      </div>
      <canvas ref={canvasRef} onClick={handleCanvasClick} className="w-full h-full block cursor-pointer" />

      {/* NODE DETAIL SLIDE-OVER */}
      <div 
        className={`absolute top-0 right-0 w-80 h-full bg-[#0a0a0a]/95 backdrop-blur-md border-l border-[var(--t-border)] p-4 shadow-[-5px_0_15px_rgba(0,0,0,0.8)] z-20 flex flex-col font-mono overflow-y-auto transition-transform duration-300 ${selectedNode ? 'translate-x-0' : 'translate-x-full'}`}
      >
        {selectedNode && (
          <>
            <div className="flex justify-between items-center mb-4 border-b border-[var(--t-border)] pb-2 shrink-0">
              <h3 className="text-[var(--t-cyan)] text-[12px] uppercase font-bold tracking-widest flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-[var(--t-cyan)] animate-pulse"></span>
                NODE.INSPECT
              </h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-[var(--t-dim)] hover:text-white transition-colors text-[14px]"
              >
                [X]
              </button>
            </div>

            <div className="text-[14px] text-white font-bold mb-2 break-words">
              {selectedNode.label}
            </div>
            <div className="text-[10px] text-[var(--t-dim)] mb-6">
              CLASS: <span className="text-[var(--t-amber)] bg-[var(--t-amber)]/10 px-1 py-0.5 rounded uppercase">{selectedNode.type}</span>
            </div>

            <div className="flex-1 overflow-y-auto pr-1">
              <div className="text-[10px] uppercase text-[var(--t-dim)] mb-2 border-b border-[var(--t-border)] pb-1">METADATA</div>
              {selectedNode.raw ? (
                <div className="text-[11px] text-[var(--t-dim)] whitespace-pre-wrap break-words flex flex-col gap-3">
                  {Object.entries(selectedNode.raw).map(([key, val]) => {
                    if (["id", "label", "type", "node_type"].includes(key)) return null;
                    if (val === null || val === undefined || val === "") return null;
                    const displayValue = typeof val === "object" ? JSON.stringify(val, null, 2) : String(val);
                    return (
                      <div key={key} className="bg-black/30 p-2 border border-white/5 rounded-sm">
                        <div className="text-[var(--t-cyan)] uppercase mb-1 text-[9px] tracking-wider">{key}</div>
                        <div className="text-[var(--t-text)] font-sans opacity-90">{displayValue}</div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-[11px] text-[var(--t-dim)] italic">No additional metadata available.</div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}