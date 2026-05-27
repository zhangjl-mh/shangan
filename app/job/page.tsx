import { AlertCircle, Clock3, MapPinned } from "lucide-react";
import { PrintButton } from "@/components/export/print-button";
import { JobDirectory } from "@/components/job/job-directory";
import { EmptyState } from "@/components/layout/empty-state";
import { Card } from "@/components/ui/card";
import { Reveal } from "@/components/ui/reveal";
import { readEligibleJobs } from "@/lib/content";

export const dynamic = "force-dynamic";

export default async function JobPage() {
  const report = await readEligibleJobs();

  return (
    <main className="mx-auto max-w-[1310px] space-y-5 px-5 py-9 lg:px-6">
      <Reveal className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="ink-title text-[38px]">符合岗位</h1>
          <p className="mt-3 text-lg text-[#56665e]">
            展示 Skills 依据画像筛选出的真实岗位，并保留官方信源。
          </p>
        </div>
        <PrintButton label="导出岗位页" />
      </Reveal>
      <Reveal delay={0.04}>
        <Card className="label-sans flex flex-wrap gap-x-8 gap-y-3 p-5 text-sm text-[#5d6d65]">
          <span className="flex items-center gap-2"><MapPinned size={17} />北京、天津、雄安新区及石家庄指定区县</span>
          <span className="flex items-center gap-2"><Clock3 size={17} />{report ? `最近生成：${report.generatedAt}` : "尚无生成记录"}</span>
          <span className="flex items-center gap-2"><AlertCircle size={17} />{report?.searchedSources?.length ? `已扫描 ${report.searchedSources.length} 个权威入口` : "仅显示当前采集到的符合岗位"}</span>
        </Card>
      </Reveal>
      {report?.positions.length ? (
        <Reveal className="space-y-4" delay={0.08}>
          <JobDirectory positions={report.positions} />
          {report.screeningNote ? (
            <details className="label-sans rounded-xl border border-[#d7e0d8] bg-[#f5f7f1] p-5 text-sm leading-7 text-[#596a61]">
              <summary className="cursor-pointer font-semibold text-[#304b40]">
                查看扫描结论与权威来源（{report.searchedSources?.length ?? 0}）
              </summary>
              <p className="mt-4">{report.screeningNote}</p>
              {report.referencePolicy ? (
                <p className="mt-3 rounded-lg bg-white/60 px-4 py-3 text-xs text-[#6a776f]">
                  参考信息规则：{report.referencePolicy}
                </p>
              ) : null}
              <div className="mt-5 flex flex-col gap-3">
                {report.searchedSources?.map((source) => (
                  <a
                    key={source.url}
                    href={source.url}
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg bg-white/60 px-4 py-3 text-[#496b5b] hover:underline"
                  >
                    <span className="block font-medium">{source.name}</span>
                    <span className="mt-1 block text-xs leading-6 text-[#66756e]">{source.result}</span>
                  </a>
                ))}
              </div>
            </details>
          ) : null}
        </Reveal>
      ) : (
        <Card className="p-6">
          <EmptyState
            className="min-h-[470px]"
            title={report ? "本次未发现可展示岗位" : "尚未生成符合岗位"}
            description={report ? "页面只展示已核实符合画像的真实岗位，并用状态标注是否可报名；新的官方公告或可核验历史资料出现后会纳入列表。" : "请通过 Skills 获取真实岗位。生成的 content/local/job/eligible-jobs.json 将在此支持筛选、详细信息、信源查看和报名跟踪。"}
          />
        </Card>
      )}
    </main>
  );
}
