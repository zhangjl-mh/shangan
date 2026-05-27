import Link from "next/link";
import { CalendarDays, ShieldCheck } from "lucide-react";
import { PrintButton } from "@/components/export/print-button";
import { EmptyState } from "@/components/layout/empty-state";
import { PipelineStrip } from "@/components/layout/pipeline-strip";
import { NewsBrowser } from "@/components/news/news-browser";
import { Card } from "@/components/ui/card";
import { Reveal } from "@/components/ui/reveal";
import { listDailyNewsDates, readNewsByDate } from "@/lib/content";

export const dynamic = "force-dynamic";

export default async function NewsPage({
  searchParams,
}: {
  searchParams: Promise<{ date?: string }>;
}) {
  const { date } = await searchParams;
  const dates = await listDailyNewsDates();
  const selectedDate = date && dates.includes(date) ? date : dates[0];
  const report = selectedDate ? await readNewsByDate(selectedDate) : null;

  return (
    <main className="mx-auto max-w-[1310px] space-y-5 px-5 py-8 lg:px-6">
      <Reveal className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="ink-title text-[38px]">每日时政</h1>
          <p className="mt-3 text-lg text-[#56665e]">左侧选择权威资讯，右侧研读详情并沉淀为备考素材。</p>
        </div>
        <div className="label-sans flex items-center gap-3 text-sm text-[#68746e]">
          {report ? (
            <span className="flex items-center gap-2 rounded-lg border bg-white/65 px-4 py-2">
              <CalendarDays size={16} />
              {report.date}
            </span>
          ) : null}
          <PrintButton />
        </div>
      </Reveal>
      {dates.length ? (
        <Reveal delay={0.03}>
          <Card className="no-print label-sans flex flex-wrap items-center gap-3 p-4 text-sm">
            <span className="mr-2 text-[#67746d]">日期归档</span>
            {dates.map((item) => (
              <Link
                key={item}
                href={`/news?date=${item}`}
                className={`rounded-lg border px-4 py-2 transition-colors ${
                  item === selectedDate
                    ? "border-[#98ac9d] bg-[#eaf0e8] text-[#335646]"
                    : "bg-white/60 text-[#68746e] hover:bg-white"
                }`}
              >
                {item}
              </Link>
            ))}
          </Card>
        </Reveal>
      ) : null}
      {report?.items.length ? (
        <Reveal className="space-y-5" delay={0.06}>
          <Card className="border-[#d7e0d8] bg-[#f5f7f1] p-5">
            <h2 className="text-lg font-semibold text-deep-green">{report.title}</h2>
            <p className="muted-copy mt-2 text-sm leading-7">{report.summary}</p>
            {report.meta?.scopeNote ? (
              <p className="label-sans mt-3 text-xs leading-6 text-[#718078]">
                {report.meta.scopeNote}
              </p>
            ) : null}
            {report.meta?.verifiedAt ? (
              <p className="label-sans mt-3 flex items-center gap-2 text-xs text-[#547160]">
                <ShieldCheck size={14} />
                原文链接已核验：{report.meta.verifiedAt}
              </p>
            ) : null}
          </Card>
          <NewsBrowser report={report} />
        </Reveal>
      ) : (
        <Card className="p-6">
          <EmptyState
            className="min-h-[440px]"
            title="暂无本地时政数据"
            description="Skills 生成 content/local/news/YYYY-MM-DD.json 后，可在此筛选热点、核验信源并下载 Markdown。"
          />
        </Card>
      )}
      <PipelineStrip />
    </main>
  );
}
