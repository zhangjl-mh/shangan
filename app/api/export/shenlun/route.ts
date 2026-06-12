import { readRoadmap } from "@/app/services/content";
import { renderShenlunMarkdown } from "@/app/services/export";

export const dynamic = "force-dynamic";

export async function GET() {
  const roadmap = await readRoadmap("shenlun");

  if (!roadmap) {
    return new Response("申论学习内容尚未生成。", { status: 404 });
  }

  return new Response(renderShenlunMarkdown(roadmap), {
    headers: {
      "Content-Type": "text/markdown; charset=utf-8",
      "Content-Disposition": 'attachment; filename="shenlun-study-handbook.md"',
    },
  });
}
