"use client";
import React, { useMemo } from "react";

interface RelatedNode {
  id: string;
  label: string;
  type: string;
  relationshipType: string;
  direction: "in" | "out";
}

interface NodeDetailPanelProps {
  node: any | null;
  allNodes: any[];
  allEdges: any[];
  onClose: () => void;
  onSelectNode: (node: any) => void;
}

export function NodeDetailPanel({
  node,
  allNodes,
  allEdges,
  onClose,
  onSelectNode,
}: NodeDetailPanelProps) {
  if (!node) {
    return (
      <div className={`absolute top-0 right-0 w-80 h-full bg-[#0a0a0a]/95 backdrop-blur-md border-l border-[var(--t-border)] p-4 shadow-[-5px_0_15px_rgba(0,0,0,0.8)] z-20 flex flex-col font-mono overflow-y-auto transition-transform duration-300 translate-x-full`} />
    );
  }

  // Find related nodes
  const relatedNodes = useMemo(() => {
    const nodeMap = new Map(allNodes.map((n) => [n.id, n]));
    const related: RelatedNode[] = [];

    allEdges.forEach((edge: any) => {
      if (edge.source?.id === node.id || edge.source === node.id) {
        const targetId =
          typeof edge.target === "object" ? edge.target.id : edge.target;
        const targetNode = nodeMap.get(targetId);
        if (targetNode) {
          related.push({
            id: targetId,
            label: targetNode.label,
            type: targetNode.type,
            relationshipType: edge.type || "connected_to",
            direction: "out",
          });
        }
      }
      if (edge.target?.id === node.id || edge.target === node.id) {
        const sourceId =
          typeof edge.source === "object" ? edge.source.id : edge.source;
        const sourceNode = nodeMap.get(sourceId);
        if (sourceNode) {
          related.push({
            id: sourceId,
            label: sourceNode.label,
            type: sourceNode.type,
            relationshipType: edge.type || "connected_to",
            direction: "in",
          });
        }
      }
    });

    return related;
  }, [node, allNodes, allEdges]);

  const incomingCount = relatedNodes.filter(
    (n) => n.direction === "in"
  ).length;
  const outgoingCount = relatedNodes.filter(
    (n) => n.direction === "out"
  ).length;

  // Extract metadata entries
  const metadataEntries = useMemo(() => {
    if (!node.raw) return [];
    return Object.entries(node.raw)
      .filter(
        ([key, val]) =>
          !["id", "label", "type", "node_type"].includes(key) &&
          val !== null &&
          val !== undefined &&
          val !== ""
      )
      .slice(0, 5); // Limit to 5 most important fields for space
  }, [node.raw]);

  const getTypeColor = (type: string) => {
    if (["threat", "IOCNode", "MITRETacticNode", "ClaimNode"].includes(type))
      return "text-[var(--t-red)]";
    if (["agent_result", "EvidenceNode", "EntityNode", "OSINTSourceNode"].includes(type))
      return "text-[var(--t-amber)]";
    return "text-[var(--t-cyan)]";
  };

  const getTypeIcon = (type: string) => {
    const iconMap: Record<string, string> = {
      IOCNode: "⚡",
      MITRETacticNode: "⚔️",
      OSINTSourceNode: "🌐",
      EntityNode: "👤",
      threat: "💀",
      root: "🎯",
      finding: "📍",
      default: "●",
    };
    return iconMap[type] || iconMap.default;
  };

  return (
    <div
      className={`absolute top-0 right-0 w-96 h-full bg-gradient-to-b from-[#0a0a0a]/95 to-[#050505]/95 backdrop-blur-md border-l border-[var(--t-border)] shadow-[-5px_0_15px_rgba(0,0,0,0.8)] z-20 flex flex-col font-mono overflow-hidden transition-transform duration-300 ${
        node ? "translate-x-0" : "translate-x-full"
      }`}
    >
      {/* Header */}
      <div className="flex-0 border-b border-[var(--t-border)] bg-black/40 p-3 shrink-0 flex justify-between items-start gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <span className="w-2 h-2 rounded-full bg-[var(--t-cyan)] animate-pulse"></span>
            <h3 className="text-[var(--t-cyan)] text-[10px] uppercase font-bold tracking-widest">
              NODE.INSPECT
            </h3>
          </div>
          <div className="text-[13px] text-white font-bold break-words mb-1">
            {node.label}
          </div>
          <div className={`inline-flex items-center gap-1 text-[10px] uppercase font-semibold ${getTypeColor(node.type)} bg-black/60 px-2 py-1 rounded`}>
            <span>{getTypeIcon(node.type)}</span>
            <span>{node.type}</span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-[var(--t-dim)] hover:text-white transition-colors text-[14px] font-bold flex-shrink-0 h-8 w-8 flex items-center justify-center hover:bg-white/5 rounded"
        >
          ×
        </button>
      </div>

      {/* Scroll Container */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Connection Stats */}
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-black/40 border border-[var(--t-cyan)]/20 rounded p-2">
            <div className="text-[10px] text-[var(--t-dim)] uppercase mb-1">
              Incoming
            </div>
            <div className="text-[18px] font-bold text-[var(--t-cyan)]">
              {incomingCount}
            </div>
          </div>
          <div className="bg-black/40 border border-[var(--t-amber)]/20 rounded p-2">
            <div className="text-[10px] text-[var(--t-dim)] uppercase mb-1">
              Outgoing
            </div>
            <div className="text-[18px] font-bold text-[var(--t-amber)]">
              {outgoingCount}
            </div>
          </div>
        </div>

        {/* Relationships */}
        {relatedNodes.length > 0 && (
          <div>
            <div className="text-[10px] uppercase text-[var(--t-green)] font-bold mb-2 pb-1 border-b border-[var(--t-border)]">
              RELATIONSHIPS ({relatedNodes.length})
            </div>
            <div className="space-y-1">
              {relatedNodes.slice(0, 8).map((rel) => (
                <button
                  key={`${rel.id}-${rel.direction}`}
                  onClick={() => {
                    const targetNode = allNodes.find((n) => n.id === rel.id);
                    if (targetNode) onSelectNode(targetNode);
                  }}
                  className="w-full text-left text-[10px] p-2 bg-black/30 hover:bg-black/60 border border-white/5 hover:border-[var(--t-cyan)]/40 rounded transition-colors group"
                >
                  <div className="flex items-center gap-1 mb-0.5">
                    <span
                      className={`text-[9px] font-bold uppercase ${
                        rel.direction === "in"
                          ? "text-[var(--t-amber)]"
                          : "text-[var(--t-cyan)]"
                      }`}
                    >
                      {rel.direction === "in" ? "← FROM" : "TO →"}
                    </span>
                    <span className="text-[var(--t-dim)] flex-1">
                      {rel.relationshipType}
                    </span>
                  </div>
                  <div className="text-[var(--t-text)] group-hover:text-[var(--t-cyan)] transition-colors truncate">
                    {rel.label}
                  </div>
                </button>
              ))}
              {relatedNodes.length > 8 && (
                <div className="text-[9px] text-[var(--t-dim)] italic p-1">
                  +{relatedNodes.length - 8} more connections...
                </div>
              )}
            </div>
          </div>
        )}

        {/* Properties */}
        {metadataEntries.length > 0 && (
          <div>
            <div className="text-[10px] uppercase text-[var(--t-amber)] font-bold mb-2 pb-1 border-b border-[var(--t-border)]">
              PROPERTIES
            </div>
            <div className="space-y-1.5">
              {metadataEntries.map(([key, val]) => {
                const displayValue =
                  typeof val === "object"
                    ? JSON.stringify(val).substring(0, 50)
                    : String(val).substring(0, 100);
                return (
                  <div key={key} className="text-[9px]">
                    <div className="text-[var(--t-cyan)] uppercase mb-0.5 tracking-wider font-semibold">
                      {key}
                    </div>
                    <div className="text-[var(--t-dim)] bg-black/40 p-1.5 rounded border border-white/5 break-all font-mono">
                      {displayValue}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Summary */}
        {metadataEntries.length === 0 && relatedNodes.length === 0 && (
          <div className="text-[11px] text-[var(--t-dim)] italic text-center py-4 px-2 bg-black/20 rounded border border-white/5">
            No additional metadata or connections available for this node.
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="flex-0 border-t border-[var(--t-border)] bg-black/40 p-2 shrink-0 text-[9px] text-[var(--t-dim)] flex justify-between">
        <span>ID: {node.id.substring(0, 12)}</span>
        <span>Connections: {relatedNodes.length}</span>
      </div>
    </div>
  );
}
