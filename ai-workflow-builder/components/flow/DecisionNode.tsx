"use client";

import { useState } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

export type DecisionNodeData = {
  prompt: string;
  onPromptChange?: (nodeId: string, newPrompt: string) => void;
};

export function DecisionNode({ id, data, selected }: NodeProps) {
  const nodeData = data as DecisionNodeData;
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(nodeData.prompt);

  const handleOpen = () => {
    setDraft(nodeData.prompt);
    setOpen(true);
  };

  const handleSave = () => {
    nodeData.onPromptChange?.(id, draft);
    setOpen(false);
  };

  return (
    <>
      <Card
        className={`w-64 cursor-pointer ${selected ? "ring-2 ring-primary" : ""}`}
        onClick={handleOpen}
      >
        <Handle type="target" position={Position.Top} />
        <CardHeader className="pb-2">
          <p className="text-xs font-medium text-muted-foreground">Decision</p>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{nodeData.prompt || "Click to edit prompt..."}</p>
        </CardContent>

        <Handle
          type="source"
          position={Position.Bottom}
          id="yes"
          style={{ left: "30%", background: "#22c55e" }}
        />
        <Handle
          type="source"
          position={Position.Bottom}
          id="no"
          style={{ left: "70%", background: "#ef4444" }}
        />
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent onClick={(e) => e.stopPropagation()}>
          <DialogHeader>
            <DialogTitle>Edit decision prompt</DialogTitle>
          </DialogHeader>
          <Textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="e.g. Is this a support request?"
            rows={3}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}