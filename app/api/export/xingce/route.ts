import { readRoadmap } from "@/app/services/content";
import { renderXingceMarkdown } from "@/app/services/export";
import type { XingceRoadmap } from "@/app/types/content";

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
