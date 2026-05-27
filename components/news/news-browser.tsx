"use client";

import { useMemo, useState } from "react";
import { Download, ExternalLink, Search, ShieldCheck } from "lucide-react";
import type { DailyNews, NewsItem } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function NewsBrowser({ report }: { report: DailyNews }) {
  const [query, setQuery] = useState("");
  const [source, setSource] = useState("全部来源");
  const [tag, setTag] = useState("全部主题");
  const [selectedId, setSelectedId] = useState(report.items[0]?.id ?? "");
  const sources = ["全部来源", ...new Set(report.items.map((item) => item.source))];
  const tags = ["全部主题", ...new Set(report.items.flatMap((item) => item.tags ?? []))];

  const items = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return report.items.filter((item) => {
      const sourceMatched = source === "全部来源" || item.source === source;
      const tagMatched = tag === "全部主题" || item.tags?.includes(tag);
      const text = `${item.title} ${item.summary} ${item.keywords.join(" ")} ${(item.tags ?? []).join(" ")}`.toLowerCase();
      return sourceMatched && tagMatched && (!keyword || text.includes(keyword));
    });
  }, [query, report.items, source, tag]);
  const selected = items.find((item) => item.id === selectedId) ?? items[0];

  function downloadMarkdown() {
    const text = buildMarkdown(report);
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = `${report.date}-daily-news.md`;
    link.click();
    URL.revokeObjectURL(href);
  }

  return (
    <>
      <Card className="no-print label-sans flex flex-wrap items-center gap-3 p-4">
        <label className="flex min-w-[240px] flex-1 items-center gap-2 rounded-lg border bg-white/70 px-3 py-2">
          <Search size={17} className="text-[#75817b]" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="w-full bg-transparent text-sm outline-none"
            placeholder="搜索标题、摘要或关键词"
          />
        </label>
        <select
          value={source}
          onChange={(event) => setSource(event.target.value)}
          className="rounded-lg border bg-white/70 px-4 py-2 text-sm outline-none"
        >
          {sources.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
        <select
          value={tag}
          onChange={(event) => setTag(event.target.value)}
          className="rounded-lg border bg-white/70 px-4 py-2 text-sm outline-none"
        >
          {tags.map((item) => (
            <option key={item}>{item}</option>
          ))}
        </select>
        <Button variant="outline" size="sm" onClick={downloadMarkdown}>
          <Download size={15} />
          Markdown 下载
        </Button>
      </Card>
      <p className="label-sans text-sm text-[#6c7872]">当前显示 {items.length} 条经整理资讯；左侧选题，右侧阅读详情。</p>
      <div className="grid items-start gap-5 xl:grid-cols-[.9fr_1.1fr]">
        <Card className="p-5 xl:sticky xl:top-[96px]">
          <h2 className="section-title mb-5">热点标题</h2>
          <div className="space-y-3">
            {items.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => setSelectedId(item.id)}
                className={`label-sans w-full rounded-xl border p-4 text-left transition-colors ${
                  selected?.id === item.id
                    ? "border-[#9eb1a1] bg-[#eef1ea]"
                    : "bg-white/45 hover:bg-white/75"
                }`}
              >
                <div className="mb-2 flex items-start justify-between gap-3">
                  <span className="font-medium leading-6 text-[#273731]">{item.title}</span>
                  {item.importance ? <Badge className="shrink-0">{item.importance}</Badge> : null}
                </div>
                <p className="text-xs text-[#527565]">{item.source} · {item.publishTime}</p>
              </button>
            ))}
            {!items.length ? (
              <p className="py-8 text-center text-sm text-[#6c7872]">没有符合当前筛选条件的热点。</p>
            ) : null}
          </div>
        </Card>
        <Card className="ornament-pavilion relative overflow-hidden p-6 lg:p-8">
          {selected ? <NewsDetail item={selected} /> : <p className="muted-copy">请选择左侧资讯标题查看详情。</p>}
        </Card>
      </div>
    </>
  );
}

function NewsDetail({ item }: { item: NewsItem }) {
  return (
    <article className="relative z-10">
      <div className="flex flex-wrap items-center gap-2">
        {item.keywords.map((keyword) => <Badge key={keyword}>{keyword}</Badge>)}
      </div>
      <h2 className="ink-title mt-4 text-2xl leading-relaxed">{item.title}</h2>
      <p className="muted-copy mt-2 text-sm">{item.source} · {item.publishTime}</p>
      {item.verification ? (
        <p className="label-sans mt-3 flex items-center gap-2 text-xs text-[#527565]">
          <ShieldCheck size={14} />
          {item.verification.note}（核验于 {item.verification.verifiedAt}）
        </p>
      ) : null}
      <DetailBlock title="事件摘要" text={item.summary} />
      {item.policyBackground ? <DetailBlock title="政策背景" text={item.policyBackground} /> : null}
      {item.shenlunAngles?.length ? (
        <DetailBlock title="申论角度" text={item.shenlunAngles.map((angle) => `${angle.title}：${angle.explanation}`).join("\n")} />
      ) : null}
      {item.xingceLinks?.length ? (
        <DetailBlock title="行测关联" text={item.xingceLinks.map((link) => `${link.module}：${link.explanation}`).join("\n")} />
      ) : null}
      {item.materials?.length ? (
        <DetailBlock title="积累表达" text={item.materials.map((material) => `• ${material}`).join("\n")} />
      ) : null}
      {item.examQuestions?.length ? (
        <DetailBlock title="可能出题方向" text={item.examQuestions.map((question) => `• ${question}`).join("\n")} />
      ) : null}
      <a
        href={item.url}
        target="_blank"
        rel="noreferrer"
        className="label-sans mt-6 inline-flex items-center gap-2 text-sm text-[#466c5b] hover:underline"
      >
        查看原始信源 <ExternalLink size={14} />
      </a>
    </article>
  );
}

function DetailBlock({ title, text }: { title: string; text: string }) {
  return (
    <section className="mt-5">
      <h3 className="font-semibold tracking-[.08em] text-[#273731]">{title}</h3>
      <p className="muted-copy mt-2 whitespace-pre-line text-sm leading-7">{text}</p>
    </section>
  );
}

function buildMarkdown(report: DailyNews) {
  const lines = [`# ${report.title}`, "", report.summary, ""];
  for (const item of report.items) {
    lines.push(`## ${item.title}`, "", `- 来源：[${item.source}](${item.url})`, `- 发布时间：${item.publishTime}`, "", item.summary, "");
    if (item.verification) {
      lines.push(`- 信源核验：${item.verification.note}（${item.verification.verifiedAt}）`, "");
    }
    if (item.tags?.length) {
      lines.push(`- 主题：${item.tags.join("、")}`, "");
    }
    if (item.policyBackground) {
      lines.push("### 政策背景", "", item.policyBackground, "");
    }
    if (item.shenlunAngles?.length) {
      lines.push("### 申论角度", "");
      item.shenlunAngles.forEach((angle) => lines.push(`- ${angle.title}：${angle.explanation}`));
      lines.push("");
    }
    if (item.materials?.length) {
      lines.push("### 积累表达", "");
      item.materials.forEach((material) => lines.push(`- ${material}`));
      lines.push("");
    }
    if (item.examQuestions?.length) {
      lines.push("### 可能出题方向", "");
      item.examQuestions.forEach((question) => lines.push(`- ${question}`));
      lines.push("");
    }
  }
  return lines.join("\n");
}
