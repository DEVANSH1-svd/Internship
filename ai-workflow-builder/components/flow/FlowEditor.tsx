"use client";

import { useCallback, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  type Connection,
} from "@xyflow/react";
import { DecisionNode, type DecisionNodeData } from "./DecisionNode";

const nodeTypes = {
  decision: DecisionNode,
};

let nodeIdCounter = 2;

export function FlowEditor() {
  const onPromptChange = useCallback((nodeId: string, newPrompt: string) => {
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, prompt: newPrompt } }
          : node
      )
    );
  }, []);

  const [nodes, setNodes] = useState<Node[]>([
    {
      id: "1",
      type: "decision",
      position: { x: 250, y: 50 },
      data: { prompt: "Is this a support request?", onPromptChange },
    },
  ]);
  const [edges, setEdges] = useState<Edge[]>([]);

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect: OnConnect = useCallback((connection: Connection) => {
    const isYes = connection.sourceHandle === "yes";
    const newEdge: Edge = {
      ...connection,
      id: `e${connection.source}-${connection.target}-${connection.sourceHandle}`,
      label: isYes ? "YES" : "NO",
      style: { stroke: isYes ? "#22c55e" : "#ef4444" },
      labelStyle: { fill: isYes ? "#22c55e" : "#ef4444", fontWeight: 700 },
    };
    setEdges((eds) => addEdge(newEdge, eds));
  }, []);

  const addNode = useCallback(() => {
    const newNode: Node<DecisionNodeData> = {
      id: String(nodeIdCounter++),
      type: "decision",
      position: { x: 250, y: 50 + nodes.length * 150 },
      data: { prompt: "New question...", onPromptChange },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [nodes.length, onPromptChange]);

  return (
    <div className="w-full h-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>

      <button
        onClick={addNode}
        className="absolute top-4 left-4 z-10 bg-primary text-primary-foreground px-4 py-2 rounded-md shadow-md text-sm font-medium"
      >
        + Add Node
      </button>
    </div>
  );
}