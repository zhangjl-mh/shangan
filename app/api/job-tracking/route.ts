import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";
import { dataDirectory } from "@/lib/storage-paths";
import type { JobTrackingData } from "@/lib/types";

const trackingPath = path.join(dataDirectory, "job-tracking.local.json");

export async function GET() {
  try {
    const content = await readFile(trackingPath, "utf8");
    return NextResponse.json(JSON.parse(content) as JobTrackingData);
  } catch {
    return NextResponse.json({ updatedAt: "", items: [] } satisfies JobTrackingData);
  }
}

export async function PUT(request: Request) {
  const data = (await request.json()) as JobTrackingData;

  if (!Array.isArray(data.items)) {
    return NextResponse.json({ message: "跟踪数据格式无效" }, { status: 400 });
  }

  await mkdir(path.dirname(trackingPath), { recursive: true });
  const normalized: JobTrackingData = {
    updatedAt: new Date().toISOString(),
    items: data.items,
  };
  await writeFile(trackingPath, `${JSON.stringify(normalized, null, 2)}\n`, "utf8");

  return NextResponse.json(normalized);
}
