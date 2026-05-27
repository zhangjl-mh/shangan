import { AlertCircle, Clock3, MapPinned } from "lucide-react";
import { PrintButton } from "@/components/export/print-button";
import { JobDirectory } from "@/components/job/job-directory";
import { Card } from "@/components/ui/card";
import { Reveal } from "@/components/ui/reveal";
import { readEligibleJobs } from "@/lib/content";

export const dynamic = "force-dynamic";

function formatScanMinute(value?: string) {
  if (!value) return "尚无检索记录";
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("zh-CN", {
      timeZone: "Asia/Shanghai",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(new Date(value))
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  );
  return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`;
}

export default async function JobPage() {
  const report = await readEligibleJobs();
  const activePositions = report?.positions.filter(
    (position) => position.status === "报名中" || position.status === "即将报名",
  ) ?? [];

  return (
    <main className="mx-auto max-w-[1310px] space-y-5 px-5 py-9 lg:px-6">
      <Reveal className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="ink-title text-[38px]">岗位判断工作台</h1>
          <p className="mt-3 text-lg text-[#56665e]">
            看清能报哪些、值不值得报、需要避开什么，以及下一步如何准备。
          </p>
        </div>
        <PrintButton label="导出岗位页" />
      </Reveal>
      <Reveal delay={0.04}>
        <Card className="label-sans flex flex-wrap gap-x-3 gap-y-3 p-3 text-sm text-[#5d6d65]">
          <a href="#coverage" className="flex items-center gap-2 rounded-xl px-4 py-3 hover:bg-[#f1f5ee]"><MapPinned size={17} />北京、天津、雄安新区及石家庄指定区县</a>
          <a href="#sources" className="flex items-center gap-2 rounded-xl px-4 py-3 hover:bg-[#f1f5ee]"><Clock3 size={17} />最近检索：{formatScanMinute(report?.generatedAt)}</a>
          <a href="#sources" className="flex items-center gap-2 rounded-xl px-4 py-3 hover:bg-[#f1f5ee]"><AlertCircle size={17} />{report?.searchedSources?.length ? `已核验 ${report.searchedSources.length} 个官方来源记录` : "尚无官方核验记录"}</a>
        </Card>
      </Reveal>
      <Reveal className="space-y-5" delay={0.08}>
        <JobDirectory positions={activePositions} />
        <details id="sources" open className="label-sans scroll-mt-24 rounded-[24px] border border-[#d7e0d8] bg-[#f5f7f1] p-5 text-sm leading-7 text-[#596a61]">
          <summary className="cursor-pointer font-semibold text-[#304b40]">
            官方检索记录与排除原因（{report?.searchedSources?.length ?? 0}）
          </summary>
          <p className="mt-4">{report?.screeningNote ?? "尚未执行岗位检索。"}</p>
          {report?.referencePolicy ? (
            <p className="mt-3 rounded-lg bg-white/60 px-4 py-3 text-xs text-[#6a776f]">
              展示规则：{report.referencePolicy}
            </p>
          ) : null}
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {report?.searchedSources?.map((source) => (
              <a
                key={`${source.name}-${source.url}`}
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border border-transparent bg-white/70 px-4 py-3 text-[#496b5b] transition-colors hover:border-[#bfccbe] hover:bg-white"
              >
                <span className="block font-medium">{source.name}</span>
                <span className="mt-1 block text-xs leading-6 text-[#66756e]">{source.result}</span>
              </a>
            ))}
          </div>
        </details>
      </Reveal>
    </main>
  );
}
