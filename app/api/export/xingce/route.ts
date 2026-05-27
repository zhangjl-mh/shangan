import { readRoadmap } from "@/lib/content";
import { renderXingceMarkdown } from "@/lib/export";
import type { XingceRoadmap } from "@/lib/types";

export const dynamic = "force-dynamic";

export async function GET() {
  const roadmap = await readRoadmap<XingceRoadmap>("xingce");

  if (!roadmap) {
    return new Response("行测学习内容尚未生成。", { status: 404 });
  }

  return new Response(renderXingceMarkdown(roadmap), {
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": 'attachment; filename="xingce-study-handbook.md"',
    },
  });
}
