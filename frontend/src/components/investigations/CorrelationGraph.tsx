"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  Handle,
  Position,
  NodeProps
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Database, Cloud, Activity, AlertTriangle, PlayCircle } from "lucide-react";

interface CorrelationGraphProps {
  graphData?: any;
}

// Beautiful Custom Node for Investigations
function CustomInvestigationNode({ data }: NodeProps) {
  const isHighSeverity = data.severity?.toLowerCase() === "high";
  const Icon = data.icon === "Database" ? Database : 
               data.icon === "Cloud" ? Cloud :
               data.icon === "Activity" ? Activity : PlayCircle;
               
  return (
    <div className={`px-4 py-3 shadow-lg rounded-md border bg-zinc-900 min-w-[200px] max-w-[250px] ${isHighSeverity ? "border-rose-900 shadow-rose-900/20" : "border-zinc-800"}`}>
      <Handle type="target" position={Position.Top} className="w-2 h-2 !bg-zinc-500 border-none" />
      <div className="flex items-start space-x-3">
        <div className={`p-2 rounded mt-0.5 ${isHighSeverity ? "bg-rose-950 text-rose-500" : "bg-zinc-800 text-indigo-400"}`}>
          {isHighSeverity ? <AlertTriangle className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
        </div>
        <div className="flex-1">
          <div className="text-sm font-semibold text-zinc-100 leading-tight">{data.title || "Unknown Node"}</div>
          <div className="text-xs text-zinc-500 mt-1 line-clamp-2">{data.subtitle}</div>
          
          <div className="mt-3 flex items-center justify-between">
            <span className="text-[10px] font-mono text-zinc-600 uppercase">{data.source || "System"}</span>
            {isHighSeverity && (
              <span className="text-[10px] uppercase font-bold text-rose-500">Critical</span>
            )}
          </div>
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} className="w-2 h-2 !bg-zinc-500 border-none" />
    </div>
  );
}

export function CorrelationGraph({ graphData }: CorrelationGraphProps) {
  const nodeTypes = useMemo(() => ({ custom: CustomInvestigationNode }), []);

  // Convert backend graph format to React Flow format if provided, else empty
  const nodes = useMemo(() => {
    return graphData?.nodes?.map((n: any, i: number) => ({
      id: n.id,
      position: { x: 250, y: i * 150 + 50 }, // Simple vertical layout since dagre isn't available
      data: { 
        title: n.title || n.id,
        subtitle: n.subtitle,
        severity: n.severity,
        source: n.source,
        icon: n.icon
      },
      type: "custom",
    })) || [];
  }, [graphData]);

  const edges = useMemo(() => {
    return graphData?.edges?.map((e: any) => ({
      id: `${e.source}-${e.target}-${e.relationship}`,
      source: e.source,
      target: e.target,
      label: e.relationship,
      animated: true,
      style: { stroke: "#6366f1", strokeWidth: 2 },
      labelStyle: { fill: "#a1a1aa", fontSize: 10, fontWeight: 500 },
      labelBgStyle: { fill: "#18181b" },
    })) || [];
  }, [graphData]);

  if (!graphData) {
    return (
      <div className="flex h-full items-center justify-center text-zinc-500">
        Waiting for correlation engine to produce graph...
      </div>
    );
  }

  return (
    <div className="h-full w-full bg-zinc-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        colorMode="dark"
        minZoom={0.5}
        maxZoom={2}
      >
        <Controls className="bg-zinc-900 border-zinc-800 fill-zinc-400" />
        <MiniMap className="bg-zinc-900 border border-zinc-800" maskColor="#09090b80" nodeColor="#3f3f46" />
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#27272a" />
      </ReactFlow>
    </div>
  );
}
