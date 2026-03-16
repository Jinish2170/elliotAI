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
  const animationRef = useRef<number>(0);

  // Initialize nodes based on real graph data OR fallback to findings
  useEffect(() => {
    let rawNodes: any[] = [];
    let rawEdges: any[] = [];

    if (knowledgeGraph && knowledgeGraph.nodes && knowledgeGraph.nodes.length > 0) {
      // Use real generated graph
      rawNodes = knowledgeGraph.nodes.map((n: any, idx: number) => ({
        id: n.id || 'node-'+idx,
        label: n.type || n.label || "NODE",
        isRoot: n.id === "root" || idx === 0,
        color: ["threat", "IOCNode", "MITRETacticNode", "ClaimNode"].includes(n.node_type || n.type) ? "var(--t-red)" : ["agent_result", "EvidenceNode", "EntityNode", "OSINTSourceNode"].includes(n.node_type || n.type) ? "var(--t-amber)" : "var(--t-cyan)", label: n.label || n.node_type || n.type || "NODE" 
      }));
      
      const nodeMap = new Map(rawNodes.map(n => [n.id, n]));
      rawEdges = (knowledgeGraph.edges || []).map((e: any) => ({
        source: nodeMap.get(e.source) || rawNodes[0],
        target: nodeMap.get(e.target) || rawNodes[0],
      }));
    } else if (findings && findings.length > 0) {
      // Create root node
      const root = { id: "root", label: "TARGET.DOM", isRoot: true, color: "var(--t-green)" };
      rawNodes.push(root);

      findings.forEach((f, i) => {
        const color = f.severity === "critical" || f.severity === "high" ? "var(--t-red)" : f.severity === "medium" ? "var(--t-amber)" : "var(--t-green)";
        const node = { id: f.id || 'f-'+i, label: f.category || "FINDING", isRoot: false, color };
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
          if (distSq > 0 && distSq < 8000) {
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
      ctx.lineWidth = 1.5;
      for (const link of simLinks) {
        if (!link.target || !link.source) continue;
        if (!Number.isFinite(link.source.x) || !Number.isFinite(link.target.x) || !Number.isFinite(link.source.y) || !Number.isFinite(link.target.y)) continue; const grad = ctx.createLinearGradient(link.source.x, link.source.y, link.target.x, link.target.y);
        grad.addColorStop(0, "rgba(0,255,65,0.4)");
        grad.addColorStop(1, "rgba(0,255,65,0.1)");
        ctx.strokeStyle = grad;
        ctx.beginPath();
        ctx.moveTo(link.source.x, link.source.y);
        ctx.lineTo(link.target.x, link.target.y);
        ctx.stroke();
        
        // Flow dots
        const flowPos = (time * 0.5 + Math.random()*0.1) % 1;
        const dotX = link.source.x + (link.target.x - link.source.x) * flowPos;
        const dotY = link.source.y + (link.target.y - link.source.y) * flowPos;
        ctx.fillStyle = "rgba(0, 255, 65, 0.8)";
        ctx.beginPath();
        ctx.arc(dotX, dotY, 1.5, 0, Math.PI*2);
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
        
        ctx.shadowColor = colorStr;
        ctx.shadowBlur = n.isRoot ? 15 : 5;
        
        ctx.fillStyle = colorStr;
        ctx.beginPath();
        if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
          ctx.arc(n.x, n.y, n.isRoot ? 7 : 3, 0, Math.PI * 2);
        ctx.fill();

        ctx.shadowBlur = 0; // reset for text

        if (n.isRoot || simNodes.length < 15) {
          ctx.fillStyle = "rgba(255,255,255,0.9)";
          ctx.font = n.isRoot ? "bold 9px 'JetBrains Mono', monospace" : "8px 'JetBrains Mono', monospace";
          ctx.fillText(n.label.substring(0,10), n.x + 8, n.y + 3);
        }
      }

      animationRef.current = requestAnimationFrame(tick);
    };

    tick();
    return () => cancelAnimationFrame(animationRef.current);
  }, [simNodes, simLinks]);

  const totalNodes = simNodes.length;
  if (totalNodes === 0) return <GhostPanel message="AWAITING TOPOLOGY MAP" />;

  return (
    <div className="w-full h-full relative bg-[#050505] overflow-hidden group">
      <div className="absolute top-2 left-2 text-[10px] text-[var(--t-dim)] z-10 select-none uppercase font-mono bg-black/60 p-1 border border-white/5 rounded-sm">
        <div className="text-[var(--t-green)]">TOPOLOGY.DETECT</div>
        NODES: {totalNodes} <br />
        LINKS: {simLinks.length}
      </div>
      <canvas ref={canvasRef} className="w-full h-full block" />
    </div>
  );
}




