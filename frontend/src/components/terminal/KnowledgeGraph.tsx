"use client";
import React, { useEffect, useRef, useState, useMemo } from "react";
import { GhostPanel } from "./TerminalPanel";
import { NodeDetailPanel } from "./NodeDetailPanel";
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
  const [hoveredNode, setHoveredNode] = useState<any | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<string | null>(null);
  const animationRef = useRef<number>(0);

  // Memoize display nodes based on search/filter
  const displayNodes = useMemo(() => {
    return simNodes.filter((n) => {
      if (filterType && n.type !== filterType) return false;
      if (
        searchQuery &&
        !n.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
        return false;
      return true;
    });
  }, [simNodes, searchQuery, filterType]);

  // Get unique node types for filter dropdown
  const nodeTypes = useMemo(() => {
    const types = new Set<string>();
    simNodes.forEach((n) => types.add(n.type));
    return Array.from(types).sort();
  }, [simNodes]);
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
        const centerForce = 0.08;
        const repelForce = 350;
        const springLength = 80;
        const springK = 0.05;
        const damping = 0.7;
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

      // Determine which nodes/edges should be highlighted
      const connectedNodeIds = new Set<string>();
      if (hoveredNode || selectedNode) {
        const targetNode = selectedNode || hoveredNode;
        connectedNodeIds.add(targetNode.id);
        for (const link of simLinks) {
          if ((link.source?.id === targetNode.id || link.source === targetNode.id) ||
              (link.target?.id === targetNode.id || link.target === targetNode.id)) {
            if (link.source?.id) connectedNodeIds.add(link.source.id);
            else if (typeof link.source === "string") connectedNodeIds.add(link.source);
            if (link.target?.id) connectedNodeIds.add(link.target.id);
            else if (typeof link.target === "string") connectedNodeIds.add(link.target);
          }
        }
      }

      // Draw links with highlighting
      ctx.lineWidth = 1.0;
      for (const link of simLinks) {
        if (!link.target || !link.source) continue;
        if (!Number.isFinite(link.source.x) || !Number.isFinite(link.target.x) || !Number.isFinite(link.source.y) || !Number.isFinite(link.target.y)) continue;
        
        const sourceId = link.source?.id || link.source;
        const targetId = link.target?.id || link.target;
        const isHighlighted = connectedNodeIds.has(sourceId) || connectedNodeIds.has(targetId);
        
        ctx.strokeStyle = "rgba(0,255,65,0.15)";
        if (link.type === "has_vulnerability") ctx.strokeStyle = "rgba(239, 68, 68, 0.25)";
        else if (link.type === "resolves_to" || link.type === "associated_with") ctx.strokeStyle = "rgba(56, 189, 248, 0.2)";
        
        if (isHighlighted) {
          ctx.lineWidth = 2.5;
          if (link.type === "has_vulnerability") ctx.strokeStyle = "rgba(239, 68, 68, 0.7)";
          else if (link.type === "resolves_to" || link.type === "associated_with") ctx.strokeStyle = "rgba(56, 189, 248, 0.6)";
          else ctx.strokeStyle = "rgba(0,255,65,0.6)";
        }

        ctx.beginPath();
        ctx.moveTo(link.source.x, link.source.y);
        ctx.lineTo(link.target.x, link.target.y);
        ctx.stroke();

        if (isHighlighted) {
          ctx.lineWidth = 1.0;
        }

        // Flow dots mapping for highlighted edges
        if (isHighlighted) {
          const flowPos = (time * 0.5 + Math.random()*0.05) % 1;
          const dotX = link.source.x + (link.target.x - link.source.x) * flowPos;
          const dotY = link.source.y + (link.target.y - link.source.y) * flowPos;
          ctx.fillStyle = ctx.strokeStyle;
          ctx.beginPath();
          ctx.arc(dotX, dotY, 2.5, 0, Math.PI*2);
          ctx.fill();
        }
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

        const isSelected = selectedNode?.id === n.id;
        const isHovered = hoveredNode?.id === n.id;
        const isConnected = connectedNodeIds.has(n.id);
        const shouldShowLabel = n.isRoot || (simNodes.length < 25) || isSelected || isHovered || isConnected;
        
        const colorStr = getComputedStyle(document.documentElement).getPropertyValue(n.color.replace('var(', '').replace(')', '')) || "#00FF41";
        
        let iconChar = "●";
        let iconFont = "12px 'JetBrains Mono', monospace";
        if (n.type === "IOCNode") iconChar = "⚡";
        else if (n.type === "MITRETacticNode") iconChar = "⚔️";
        else if (n.type === "OSINTSourceNode") iconChar = "🌐";
        else if (n.type === "EntityNode") iconChar = "👤";
        else if (n.type === "threat") iconChar = "💀";
        else if (n.isRoot) iconChar = "🎯";

        ctx.shadowColor = colorStr;
        ctx.shadowBlur = isSelected ? 35 : isHovered ? 25 : n.isRoot ? 20 : 12;

        const size = isSelected ? 14 : isHovered ? 10 : n.isRoot ? 12 : 7;
        
        // Outer Glow Tech Bracket
        let bracketColor = colorStr;
        let bracketWidth = 1.5;
        if (isSelected) {
          bracketColor = "#00FF00";
          bracketWidth = 2.5;
        } else if (isHovered || isConnected) {
          bracketColor = "#00FFFF";
          bracketWidth = 2.0;
        }
        
        ctx.strokeStyle = bracketColor;
        ctx.lineWidth = bracketWidth;
        ctx.beginPath();
        ctx.moveTo(n.x - size, n.y - size/2);
        ctx.lineTo(n.x - size, n.y - size);
        ctx.lineTo(n.x - size/2, n.y - size);
        ctx.stroke();

          ctx.beginPath();
        ctx.moveTo(n.x + size, n.y + size/2);
        ctx.lineTo(n.x + size, n.y + size);
        ctx.lineTo(n.x + size/2, n.y + size);
        ctx.stroke();

        // Central fill
        ctx.fillStyle = "rgba(0,0,0,0.8)";
        ctx.beginPath();
        ctx.rect(n.x - size + 2, n.y - size + 2, size*2 - 4, size*2 - 4);
        ctx.fill();
        
        ctx.fillStyle = isSelected ? "#00FF00" : colorStr;
        ctx.globalAlpha = isSelected ? 0.4 : isHovered ? 0.35 : 0.2;
        ctx.fill();
        ctx.globalAlpha = 1.0;

        ctx.shadowBlur = 0; // reset

        // Draw icon
        ctx.fillStyle = isSelected ? "#00FF00" : colorStr;
        ctx.font = iconFont;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(iconChar, n.x, n.y);

        // Draw label with better logic
        if (shouldShowLabel) {
          ctx.fillStyle = isSelected ? "rgba(0,255,0,1)" : isHovered ? "rgba(0,255,255,0.9)" : "rgba(255,255,255,0.8)";
          ctx.font = isSelected ? "bold 12px 'JetBrains Mono', monospace" : isHovered ? "bold 11px 'JetBrains Mono', monospace" : n.isRoot ? "bold 11px 'JetBrains Mono', monospace" : "10px 'JetBrains Mono', monospace";
          ctx.textAlign = "center";
          const labelText = n.label.substring(0, 16);
          ctx.fillText(labelText, n.x, n.y + size + 12);
          if (n.label.length > 16) {
            ctx.fillText("...", n.x, n.y + size + 22);
          }
        }
      }

      animationRef.current = requestAnimationFrame(tick);
    };

    tick();
    return () => cancelAnimationFrame(animationRef.current);
  }, [simNodes, simLinks, selectedNode, hoveredNode]);

  const totalNodes = simNodes.length;
  const visibleCount = displayNodes.length;
  
  if (totalNodes === 0) return <GhostPanel message="AWAITING TOPOLOGY MAP" />;

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Find nearest node within hover radius
    let nearest = null;
    let minDist = 25 * 25; // 25px radius hover tolerance
    for (const n of simNodes) {
      if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
      const dx = n.x - x;
      const dy = n.y - y;
      const distSq = dx * dx + dy * dy;
      if (distSq < minDist) {
        minDist = distSq;
        nearest = n;
      }
    }
    setHoveredNode(nearest);
    if (canvasRef.current) {
      canvasRef.current.style.cursor = nearest ? "pointer" : "crosshair";
    }
  };

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Find nearest node
    let nearest = null;
    let minDist = 25 * 25; // 25px radius click tolerance
    for (const n of simNodes) {
      if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) continue;
      const dx = n.x - x;
      const dy = n.y - y;
      const distSq = dx * dx + dy * dy;
      if (distSq < minDist) {
        minDist = distSq;
        nearest = n;
      }
    }
    setSelectedNode(nearest);
  };

  const handleCanvasLeave = () => {
    setHoveredNode(null);
    if (canvasRef.current) {
      canvasRef.current.style.cursor = "crosshair";
    }
  };

  return (
    <div className="w-full h-full relative bg-[#050505] overflow-hidden group">
      {/* Stats Panel */}
      <div className="absolute top-2 left-2 text-[11px] text-[var(--t-dim)] z-10 select-none uppercase font-mono bg-black/70 p-2 border border-[var(--t-green)]/30 rounded-sm">
        <div className="text-[var(--t-green)] font-bold mb-1">TOPOLOGY.DETECT</div>
        <div>NODES: <span className="text-[var(--t-cyan)]">{totalNodes}</span> <span className="text-[var(--t-dim)]">(Visible: {visibleCount})</span></div>
        <div>LINKS: <span className="text-[var(--t-amber)]">{simLinks.length}</span></div>
      </div>

      {/* Search & Filter Panel */}
      <div className="absolute bottom-2 left-2 max-w-[220px] text-[11px] z-10 select-none uppercase font-mono bg-black/70 p-2 border border-[var(--t-border)] rounded-sm space-y-2">
        <input
          type="text"
          placeholder="Search nodes..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full bg-black/60 border border-white/10 rounded px-2 py-1 text-[var(--t-text)] placeholder:text-[var(--t-dim)] text-[10px] focus:outline-none focus:border-[var(--t-cyan)]/50"
        />
        <select
          value={filterType || ""}
          onChange={(e) => setFilterType(e.target.value || null)}
          className="w-full bg-black/60 border border-white/10 rounded px-2 py-1 text-[var(--t-text)] text-[10px] focus:outline-none focus:border-[var(--t-cyan)]/50"
        >
          <option value="">All Types</option>
          {nodeTypes.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>

      {/* Canvas */}
      <canvas
        ref={canvasRef}
        onMouseMove={handleCanvasMouseMove}
        onClick={handleCanvasClick}
        onMouseLeave={handleCanvasLeave}
        className="w-full h-full block"
      />

      {/* NODE DETAIL PANEL */}
      <NodeDetailPanel
        node={selectedNode}
        allNodes={simNodes}
        allEdges={simLinks}
        onClose={() => setSelectedNode(null)}
        onSelectNode={setSelectedNode}
      />
    </div>
  );
}
