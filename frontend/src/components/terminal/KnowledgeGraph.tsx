"use client";
import React, { useEffect, useRef, useState } from "react";
import { GhostPanel } from "./TerminalPanel";
import { Finding } from "@/lib/types";

// Extremely primitive simulated physics graph to avoid D3/Cytoscape heavy lifting and DOM thrashing
interface Node {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  color: string;
  label: string;
}

interface Link {
  source: Node;
  target: Node;
}

export function KnowledgeGraph({ findings }: { findings: Finding[] }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [links, setLinks] = useState<Link[]>([]);
  const animationRef = useRef<number>(0);

  // Initialize nodes based on findings
  useEffect(() => {
    if (!findings || findings.length === 0) return;

    const newNodes: Node[] = [];
    const newLinks: Link[] = [];
    
    // Create root node
    const root: Node = {
      id: "root",
      x: 150,
      y: 150,
      vx: 0,
      vy: 0,
      color: "var(--t-green)",
      label: "TARGET.DOM"
    };
    newNodes.push(root);

    findings.forEach((f, i) => {
      const color = f.severity === "critical" || f.severity === "high" ? "var(--t-red)" : 
                    f.severity === "medium" ? "var(--t-amber)" : "var(--t-green)";
      
      const node: Node = {
        id: f.id || `node-${i}`,
        x: 150 + (Math.random() * 100 - 50),
        y: 150 + (Math.random() * 100 - 50),
        vx: 0,
        vy: 0,
        color,
        label: f.category || "FINDING"
      };
      newNodes.push(node);
      newLinks.push({ source: root, target: node });
    });

    setNodes(newNodes);
    setLinks(newLinks);
  }, [findings]);

  // Simulation step
  useEffect(() => {
    if (nodes.length === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;

    const tick = () => {
      // Very basic force-directed layout
      const centerForce = 0.05;
      const repelForce = 200;
      const springLength = 80;
      const springK = 0.02;
      const damping = 0.85;

      // Reset root to center
      nodes[0].x = W / 2;
      nodes[0].y = H / 2;

      // Apply forces
      for (let i = 1; i < nodes.length; i++) {
        const n1 = nodes[i];
        
        // Center gravity
        n1.vx += (W/2 - n1.x) * centerForce * 0.1;
        n1.vy += (H/2 - n1.y) * centerForce * 0.1;

        // Repel from others
        for (let j = 0; j < nodes.length; j++) {
          if (i === j) continue;
          const n2 = nodes[j];
          const dx = n1.x - n2.x;
          const dy = n1.y - n2.y;
          const distSq = dx*dx + dy*dy;
          if (distSq > 0 && distSq < 10000) {
            const f = repelForce / distSq;
            n1.vx += dx * f;
            n1.vy += dy * f;
          }
        }
      }

      // Apply spring along links
      for (const link of links) {
        const dx = link.target.x - link.source.x;
        const dy = link.target.y - link.source.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist > 0) {
          const f = (dist - springLength) * springK;
          const fx = (dx / dist) * f;
          const fy = (dy / dist) * f;
          
          if (link.target !== nodes[0]) {
            link.target.vx -= fx;
            link.target.vy -= fy;
          }
          if (link.source !== nodes[0]) {
            link.source.vx += fx;
            link.source.vy += fy;
          }
        }
      }

      // Update positions & draw
      ctx.clearRect(0, 0, W, H);
      
      // Draw links
      ctx.lineWidth = 1;
      for (const link of links) {
        ctx.beginPath();
        ctx.strokeStyle = "rgba(0, 255, 65, 0.2)";
        ctx.moveTo(link.source.x, link.source.y);
        ctx.lineTo(link.target.x, link.target.y);
        ctx.stroke();
      }

      // Draw nodes
      for (const n of nodes) {
        if (n !== nodes[0]) {
          n.vx *= damping;
          n.vy *= damping;
          n.x += n.vx;
          n.y += n.vy;
          // bounds
          n.x = Math.max(10, Math.min(W - 10, n.x));
          n.y = Math.max(10, Math.min(H - 10, n.y));
        }

        ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue(n.color.replace('var(', '').replace(')', '')) || "#00FF41";
        ctx.beginPath();
        ctx.arc(n.x, n.y, n === nodes[0] ? 6 : 4, 0, Math.PI * 2);
        ctx.fill();

        if (n === nodes[0]) {
          ctx.fillStyle = "#fff";
          ctx.font = "8px 'JetBrains Mono', monospace";
          ctx.fillText("DOM.ROOT", n.x + 8, n.y + 3);
        }
      }

      animationRef.current = requestAnimationFrame(tick);
    };

    tick();

    return () => cancelAnimationFrame(animationRef.current);
  }, [nodes, links]);

  if (!findings || findings.length === 0) return <GhostPanel message="AWAITING TOPOLOGY MAP" />;

  return (
    <div className="w-full h-full relative bg-[#050505] overflow-hidden group">
      <div className="absolute top-2 left-2 text-[10px] text-[var(--t-dim)] z-10 select-none uppercase">
        NODES: {nodes.length} <br />
        LINKS: {links.length}
      </div>
      {/* 
        We use raw width/height to match our typical bounds in grid,
        Resizing handled simply by locking layout in Terminal Grid
      */}
      <canvas 
        ref={canvasRef} 
        width={300} 
        height={300} 
        className="w-full h-[150%] -mt-[25%]" 
      />
    </div>
  );
}
