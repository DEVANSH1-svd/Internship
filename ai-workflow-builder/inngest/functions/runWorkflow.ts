import { inngest } from "@/inngest/client";
import OpenAI from "openai";

type WorkflowNode = {
  id: string;
  data: { prompt: string };
};

type WorkflowEdge = {
  id: string;
  source: string;
  target: string;
  sourceHandle: "yes" | "no";
};

type WorkflowPayload = {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  startNodeId?: string;
};

function getClient() {
  return new OpenAI({
    baseURL: process.env.OPENAI_BASE_URL,
    apiKey: process.env.OPENAI_API_KEY,
    timeout: 30000,
  });
}

function findStartNode(nodes: WorkflowNode[], edges: WorkflowEdge[]): WorkflowNode | undefined {
  const targetIds = new Set(edges.map((e) => e.target));
  return nodes.find((n) => !targetIds.has(n.id));
}

export const runWorkflow = inngest.createFunction(
  { id: "run-workflow", triggers: [{ event: "workflow/run" }] },
  async ({ event, step }) => {
    const { nodes, edges, startNodeId } = event.data as WorkflowPayload;

    const executionLog: {
      nodeId: string;
      prompt: string;
      answer: "YES" | "NO";
    }[] = [];

    let currentNode = startNodeId
      ? nodes.find((n) => n.id === startNodeId)
      : findStartNode(nodes, edges);

    let stepCount = 0;
    const MAX_STEPS = 50; // safety limit against accidental cycles

    while (currentNode && stepCount < MAX_STEPS) {
      const node = currentNode;
      stepCount++;

      const answer = await step.run(`ask-node-${node.id}`, async () => {
        const client = getClient();
        const response = await client.chat.completions.create({
          model: process.env.OPENAI_MODEL!,
          temperature: 0,
          messages: [
            {
              role: "system",
              content:
                "You answer yes/no decision questions. Reply with exactly one word: YES or NO. Never explain, never add punctuation, never say anything else.",
            },
            { role: "user", content: node.data.prompt },
          ],
        });

        const raw = response.choices[0].message.content?.trim().toUpperCase() ?? "";
        if (raw !== "YES" && raw !== "NO") {
          throw new Error(`Model returned unexpected answer: "${raw}"`);
        }
        return raw as "YES" | "NO";
      });

      executionLog.push({ nodeId: node.id, prompt: node.data.prompt, answer });

      const nextHandle = answer === "YES" ? "yes" : "no";
      const nextEdge = edges.find(
        (e) => e.source === node.id && e.sourceHandle === nextHandle
      );

      currentNode = nextEdge ? nodes.find((n) => n.id === nextEdge.target) : undefined;
    }

        const result = { executionLog, stepCount };

    await step.run("save-result", async () => {
      const fs = await import("fs/promises");
      const path = await import("path");
      const filePath = path.join(process.cwd(), ".workflow-results", `${event.id}.json`);
      await fs.mkdir(path.dirname(filePath), { recursive: true });
      await fs.writeFile(filePath, JSON.stringify(result));
    });

    return result;
  }
);
