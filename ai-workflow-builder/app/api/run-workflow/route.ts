import { NextRequest, NextResponse } from "next/server";
import { inngest } from "@/inngest/client";
import fs from "fs/promises";
import path from "path";

async function waitForResultFile(eventId: string, maxAttempts = 90): Promise<unknown> {
  const filePath = path.join(process.cwd(), ".workflow-results", `${eventId}.json`);

  for (let i = 0; i < maxAttempts; i++) {
    await new Promise((resolve) => setTimeout(resolve, 1000));

    try {
      const content = await fs.readFile(filePath, "utf-8");
      return JSON.parse(content);
    } catch {
      // file doesn't exist yet, keep waiting
      continue;
    }
  }

  throw new Error("Timed out waiting for workflow to complete");
}

export async function POST(req: NextRequest) {
  const body = await req.json();

  const { ids } = await inngest.send({
    name: "workflow/run",
    data: {
      nodes: body.nodes,
      edges: body.edges,
    },
  });

  try {
    const output = await waitForResultFile(ids[0]);
    return NextResponse.json({ eventId: ids[0], output });
  } catch (err) {
    return NextResponse.json(
      { eventId: ids[0], error: (err as Error).message },
      { status: 504 }
    );
  }
}