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
import { Button } from "@/components/ui/button";

const nodeTypes = {
  decision: DecisionNode,
};

let nodeIdCounter = 2;

type ExecutionLogEntry = {
  nodeId: string;
  prompt: string;
  answer: "YES" | "NO";
};

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
  const [isRunning, setIsRunning] = useState(false);
  const [executionLog, setExecutionLog] = useState<ExecutionLogEntry[] | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

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

  const runWorkflow = useCallback(async () => {
    setIsRunning(true);
    setExecutionLog(null);
    setRunError(null);

    try {
      const cleanNodes = nodes.map((n) => ({
        id: n.id,
        data: { prompt: (n.data as DecisionNodeData).prompt },
      }));
      const cleanEdges = edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
      }));

      const res = await fetch("/api/run-workflow", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nodes: cleanNodes, edges: cleanEdges }),
      });

      const result = await res.json();

      if (!res.ok) {
        setRunError(result.error || "Workflow run failed");
      } else {
        setExecutionLog(result.output?.executionLog ?? []);
      }
    } catch (err) {
      setRunError((err as Error).message);
    } finally {
      setIsRunning(false);
    }
  }, [nodes, edges]);

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

      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={addNode}
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md shadow-md text-sm font-medium"
        >
          + Add Node
        </button>
        <Button onClick={runWorkflow} disabled={isRunning}>
          {isRunning ? "Running..." : "▶ Run Workflow"}
        </Button>
      </div>

      {(executionLog || runError) && (
        <div className="absolute top-16 left-4 z-10 w-80 bg-background border rounded-md shadow-lg p-4 max-h-96 overflow-y-auto">
          <h3 className="font-semibold text-sm mb-2">Execution Result</h3>
          {runError && <p className="text-sm text-red-500">{runError}</p>}
          {executionLog?.map((entry, i) => (
            <div key={i} className="text-sm py-1 border-b last:border-0">
              <p className="text-muted-foreground">{entry.prompt}</p>
              <p className={entry.answer === "YES" ? "text-green-600 font-medium" : "text-red-600 font-medium"}>
                {entry.answer}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}