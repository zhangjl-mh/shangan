import Link from "next/link";
import { BriefcaseBusiness, ExternalLink, Search } from "lucide-react";
import { Card } from "@/app/components/ui/card";
import { EmptyState } from "@/app/components/layout/empty-state";
import { queryJobs } from "@/app/services/jobs";
import type { JobEligibility } from "@/app/types/content";

export const dynamic = "force-dynamic";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function value(params: Record<string, string | string[] | undefined>, key: string) {
  const item = params[key];
  return Array.isArray(item) ? item[0] : item;
}

function pageHref(
  params: Record<string, string | string[] | undefined>,
  page: number,
) {
  const query = new URLSearchParams();
  for (const [key, item] of Object.entries(params)) {
    const current = Array.isArray(item) ? item[0] : item;
    if (current && key !== "page") query.set(key, current);
  }
  query.set("page", String(page));
  return `/jobs?${query.toString()}`;
}

const eligibilityLabels: Record<JobEligibility, string> = {
  eligible: "资格符合",
  needs_confirmation: "待确认",
  ineligible: "不符合",
};

export default async function JobsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const result = await queryJobs({
    exam: value(params, "exam"),
    region: value(params, "region"),
    eligibility:
      (value(params, "eligibility") as JobEligibility | "default" | "all") ??
      "default",
    timing:
      (value(params, "timing") as "active" | "historical" | "all") ?? "all",
    keyword: value(params, "q"),
    page: Number(value(params, "page") ?? 1),
    pageSize: 20,
  });

  return (
    <main className="mx-auto max-w-[1450px] space-y-5 px-5 py-8 lg:px-10">
      <section>
        <p className="muted-copy text-sm">官方附件归档、统一解析、保守筛选</p>
        <h1 className="ink-title mt-2 flex items-center gap-3 text-3xl">
          <BriefcaseBusiness /> 岗位筛选
        </h1>
        <p className="muted-copy mt-3">
          资格判断与报名时效分开显示。未知条件不会自动算作符合。
        </p>
      </section>

      <Card className="p-5">
        <form className="grid gap-3 md:grid-cols-2 xl:grid-cols-6">
          <label className="xl:col-span-2">
            <span className="muted-copy mb-1 block text-sm">关键词</span>
            <span className="flex items-center gap-2 rounded-lg border bg-white/70 px-3">
              <Search size={16} />
              <input
                name="q"
                defaultValue={value(params, "q")}
                placeholder="职位、单位、专业或代码"
                className="h-10 min-w-0 flex-1 bg-transparent outline-none"
              />
            </span>
          </label>
          <FilterSelect name="exam" label="考试" current={value(params, "exam")}>
            <option value="all">全部考试</option>
            {result.exams.map((exam) => (
              <option key={exam.id} value={exam.id}>{exam.label}</option>
            ))}
          </FilterSelect>
          <FilterSelect name="region" label="地区" current={value(params, "region")}>
            <option value="all">全部地区</option>
            {result.regions.map((region) => (
              <option key={region} value={region}>{region}</option>
            ))}
          </FilterSelect>
          <FilterSelect
            name="eligibility"
            label="资格"
            current={value(params, "eligibility") ?? "default"}
          >
            <option value="default">符合与待确认</option>
            <option value="eligible">仅资格符合</option>
            <option value="needs_confirmation">仅待确认</option>
            <option value="ineligible">仅不符合</option>
            <option value="all">全部资格结果</option>
          </FilterSelect>
          <FilterSelect name="timing" label="时效" current={value(params, "timing") ?? "all"}>
            <option value="all">全部时效</option>
            <option value="active">报名中</option>
            <option value="historical">历史参考</option>
          </FilterSelect>
          <button className="label-sans h-10 rounded-lg bg-deep-green px-5 text-white md:col-span-2 xl:col-span-6 xl:justify-self-end">
            应用筛选
          </button>
        </form>
      </Card>

      {result.index ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Metric label="目录岗位" value={result.index.stats.total} />
          <Metric label="资格符合" value={result.index.stats.eligible} />
          <Metric label="待确认" value={result.index.stats.needsConfirmation} />
          <Metric label="不符合" value={result.index.stats.ineligible} />
          <Metric label="当前报名中" value={result.index.stats.active} />
        </div>
      ) : null}

      {result.items.length ? (
        <section className="space-y-3">
          <p className="muted-copy text-sm">
            共 {result.total} 条，第 {result.page}/{result.pageCount} 页
          </p>
          {result.items.map((job) => (
            <Card key={job.id} className="p-5">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge>{job.examLabel}</Badge>
                    <Badge tone={job.eligibility}>{eligibilityLabels[job.eligibility]}</Badge>
                    <Badge tone={job.timingStatus}>
                      {job.timingStatus === "active" ? "报名中" : "历史参考"}
                    </Badge>
                  </div>
                  <h2 className="mt-3 text-xl font-semibold">{job.title}</h2>
                  <p className="muted-copy mt-1">
                    {job.organization}{job.department ? ` · ${job.department}` : ""}
                  </p>
                  <p className="muted-copy mt-1 text-sm">
                    {job.region || "地区未标注"} · 职位代码 {job.positionCode} · 招录 {job.recruitCount || "未标注"} 人
                  </p>
                </div>
                <a
                  href={job.source.portalUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="label-sans inline-flex items-center gap-1 text-sm text-deep-green"
                >
                  官方来源 <ExternalLink size={14} />
                </a>
              </div>
              <details className="mt-4 border-t pt-4">
                <summary className="cursor-pointer font-semibold">查看条件与判断依据</summary>
                <div className="muted-copy mt-3 grid gap-3 text-sm md:grid-cols-2">
                  <Requirement label="专业" value={job.requirements.major} />
                  <Requirement label="学历/学位" value={[job.requirements.education, job.requirements.degree].filter(Boolean).join("；")} />
                  <Requirement label="政治面貌" value={job.requirements.politicalStatus} />
                  <Requirement label="基层/项目经历" value={[job.requirements.grassrootsYears, job.requirements.serviceProject].filter(Boolean).join("；")} />
                  <Requirement label="备注" value={job.requirements.remarks} wide />
                  <Requirement
                    label="判断"
                    value={
                      job.exclusionReasons.join("；") ||
                      (job.confirmationFields.length
                        ? `待确认：${job.confirmationFields.join("、")}`
                        : job.matchReasons.join("；"))
                    }
                    wide
                  />
                </div>
              </details>
            </Card>
          ))}
          <div className="flex items-center justify-between pt-2">
            {result.page > 1 ? <Link href={pageHref(params, result.page - 1)}>上一页</Link> : <span />}
            {result.page < result.pageCount ? <Link href={pageHref(params, result.page + 1)}>下一页</Link> : <span />}
          </div>
        </section>
      ) : (
        <EmptyState
          title="没有找到符合当前筛选的岗位"
          description={
            result.index
              ? "可放宽地区、资格或时效条件后重新筛选。"
              : "岗位官方附件尚未完成下载与构建。"
          }
        />
      )}
    </main>
  );
}

function FilterSelect({
  name,
  label,
  current,
  children,
}: {
  name: string;
  label: string;
  current?: string;
  children: React.ReactNode;
}) {
  return (
    <label>
      <span className="muted-copy mb-1 block text-sm">{label}</span>
      <select name={name} defaultValue={current} className="h-10 w-full rounded-lg border bg-white/70 px-3">
        {children}
      </select>
    </label>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <Card className="p-4"><p className="muted-copy text-sm">{label}</p><p className="mt-1 text-2xl font-semibold">{value}</p></Card>;
}

function Badge({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone?: JobEligibility | "active" | "historical";
}) {
  const colors = tone === "eligible" || tone === "active"
    ? "bg-[#e2ece5] text-[#356249]"
    : tone === "needs_confirmation"
      ? "bg-[#f4ead7] text-[#8a652d]"
      : tone === "ineligible"
        ? "bg-[#f4e1dc] text-[#934d41]"
        : "bg-[#e7e8e5] text-[#626963]";
  return <span className={`label-sans rounded-full px-2.5 py-1 text-xs ${colors}`}>{children}</span>;
}

function Requirement({
  label,
  value,
  wide = false,
}: {
  label: string;
  value: string;
  wide?: boolean;
}) {
  return <p className={wide ? "md:col-span-2" : ""}><strong className="text-foreground">{label}：</strong>{value || "未标注"}</p>;
}
