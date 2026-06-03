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
  const positions = report?.positions ?? [];

  return (
    <main className="mx-auto max-w-[1800px] space-y-5 px-5 py-9 lg:px-6">
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
        <JobDirectory positions={positions} />
        <details id="sources" className="label-sans scroll-mt-24 rounded-[24px] border border-[#d7e0d8] bg-[#f5f7f1] p-5 text-sm leading-7 text-[#596a61]">
          <summary className="cursor-pointer font-semibold text-[#304b40]">
            官方检索记录与排除原因（{report?.searchedSources?.length ?? 0}）
          </summary>
          <p className="mt-4">{report?.screeningNote ?? "尚未执行岗位检索。"}</p>
          {report?.referencePolicy ? (
            <p className="mt-3 rounded-lg bg-white/60 px-4 py-3 text-xs text-[#6a776f]">
              展示规则：{report.referencePolicy}
            </p>
          ) : null}
          {report?.sourceScreening?.length ? (
            <div className="mt-4 rounded-lg bg-white/60 px-4 py-3 text-xs text-[#607168]">
              <p className="font-semibold text-[#304b40]">逐来源全量筛选</p>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {report.sourceScreening.map((item) => (
                  <div key={item.sourceId} className="rounded-lg border border-[#dfe8dc] bg-[#fbfcf8] p-3">
                    <p className="font-medium text-[#385548]">{item.name}</p>
                    <p className="mt-1">
                      硬条件 {item.hardMatchedCount} 个 / 目标地区 {item.targetRegionCount} 个 / 其他地区 {item.outOfRegionCount} 个
                    </p>
                    {item.districtDistribution && Object.keys(item.districtDistribution).length ? (
                      <p className="mt-1 leading-5 text-[#6f7d75]">
                        县区：{Object.entries(item.districtDistribution).map(([name, count]) => `${name} ${count}`).join(" / ")}
                      </p>
                    ) : null}
                    <p className="mt-1 leading-5 text-[#718078]">{item.note}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {report?.screeningAudit?.length ? (
            <div className="mt-4 rounded-lg bg-white/60 px-4 py-3 text-xs text-[#607168]">
              <p className="font-semibold text-[#304b40]">国考县区审计</p>
              <div className="mt-3 grid gap-2 md:grid-cols-2">
                {report.screeningAudit.map((item) => (
                  <div key={item.sourceId} className="rounded-lg border border-[#dfe8dc] bg-[#fbfcf8] p-3">
                    <p>
                      目标地点原始行：{item.targetLocationRowCount ?? 0} / 石家庄目标县区：{item.shijiazhuangTargetCountyRowCount ?? 0} /
                      石家庄硬条件通过：{item.shijiazhuangHardMatchedCount ?? 0}
                    </p>
                    {item.hardMatchedDistribution ? (
                      <p className="mt-1">硬条件通过：{Object.entries(item.hardMatchedDistribution).map(([name, count]) => `${name} ${count}`).join(" / ") || "0"}</p>
                    ) : null}
                    {item.excludedHardConditionDistribution ? (
                      <p className="mt-1 leading-5 text-[#718078]">
                        排除：{Object.entries(item.excludedHardConditionDistribution).map(([name, count]) => `${name} ${count}`).join(" / ")}
                      </p>
                    ) : null}
                    {item.shijiazhuangRows?.length ? (
                      <details className="mt-3">
                        <summary className="cursor-pointer font-medium text-[#385548]">
                          展开石家庄目标县区国考原始行（{item.shijiazhuangRows.length}）
                        </summary>
                        <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
                          {item.shijiazhuangRows.map((row) => (
                            <div key={row.positionCode} className="rounded-lg border border-[#e2e9df] bg-white/70 p-2.5 leading-5">
                              <div className="flex items-start justify-between gap-2">
                                <p className="font-medium text-[#385548]">{row.district}</p>
                                <span className={`rounded-full px-2 py-0.5 text-[11px] ${row.screeningStatus === "硬条件通过" ? "bg-[#edf4eb] text-[#42624f]" : "bg-[#fff4e2] text-[#80663b]"}`}>
                                  {row.screeningStatus}
                                </span>
                              </div>
                              <p className="mt-1 line-clamp-2 text-[#4c6258]">{row.department}</p>
                              <p className="line-clamp-1 text-[#6b7a72]">{row.title} / {row.positionCode}</p>
                              <p className="mt-1 line-clamp-2 text-[#718078]">{row.majorRequirement}</p>
                              <p className="mt-1 text-[#718078]">{row.educationRequirement} / 招 {row.recruitCount}</p>
                              {row.exclusionReasons.length ? (
                                <p className="mt-1 text-[#9a6a39]">排除：{row.exclusionReasons.join("、")}</p>
                              ) : null}
                            </div>
                          ))}
                        </div>
                      </details>
                    ) : null}
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {report?.outOfRegionCandidates?.length ? (
            <p className="mt-3 rounded-lg bg-[#fff8e8] px-4 py-3 text-xs text-[#7a6237]">
              其他地区硬条件匹配 {report.outOfRegionCandidates.length} 个，已在“其他”分组展示。
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
