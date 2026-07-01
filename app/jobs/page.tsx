import Link from "next/link";
import { BriefcaseBusiness, ExternalLink, Search } from "lucide-react";
import { Card } from "@/app/components/ui/card";
import { EmptyState } from "@/app/components/layout/empty-state";
import { queryJobs } from "@/app/services/jobs";
import type {
  JobApplicationStatus,
  JobBatchStatus,
  JobCategory,
  JobEligibility,
} from "@/app/types/content";

export const dynamic = "force-dynamic";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

function value(
  params: Record<string, string | string[] | undefined>,
  key: string,
) {
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
};

const categoryLabels: Record<JobCategory, string> = {
  civil_service: "公务员",
  institution: "事业单位",
  military_civilian: "军队文职",
  state_owned_enterprise: "国央企",
};

const applicationLabels: Record<JobApplicationStatus, string> = {
  upcoming: "报名未开始",
  open: "报名中",
  closed: "报名已结束",
  unknown: "报名时间待确认",
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
    category:
      (value(params, "category") as JobCategory | "all") ?? "all",
    eligibility:
      (value(params, "eligibility") as JobEligibility) ?? "eligible",
    batch: (value(params, "batch") as JobBatchStatus | "all") ?? "all",
    application:
      (value(params, "application") as
        | JobApplicationStatus
        | "all") ?? "all",
    keyword: value(params, "q"),
    page: Number(value(params, "page") ?? 1),
    pageSize: 20,
  });

  return (
    <main className="mx-auto max-w-[1450px] space-y-5 px-5 py-8 lg:px-10">
      <section>
        <p className="muted-copy text-sm">官方附件归档、严格资格判断、批次可追溯</p>
        <h1 className="ink-title mt-2 flex items-center gap-3 text-3xl">
          <BriefcaseBusiness /> 岗位筛选
        </h1>
        <p className="muted-copy mt-3">
          默认仅展示确认符合岗位。未知条件进入待确认，上届岗位会明确标注。
        </p>
      </section>

      <Card className="p-5">
        <form className="grid gap-3 md:grid-cols-2 xl:grid-cols-8">
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
          <FilterSelect
            name="category"
            label="类别"
            current={value(params, "category") ?? "all"}
          >
            <option value="all">全部类别</option>
            {Object.entries(categoryLabels).map(([id, label]) => (
              <option key={id} value={id}>{label}</option>
            ))}
          </FilterSelect>
          <FilterSelect name="exam" label="来源" current={value(params, "exam")}>
            <option value="all">全部来源</option>
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
            current={value(params, "eligibility") ?? "eligible"}
          >
            <option value="eligible">确认符合</option>
            <option value="needs_confirmation">待确认</option>
          </FilterSelect>
          <FilterSelect
            name="batch"
            label="批次"
            current={value(params, "batch") ?? "all"}
          >
            <option value="all">全部批次</option>
            <option value="current">当前批次</option>
            <option value="previous_reference">上届参考</option>
          </FilterSelect>
          <FilterSelect
            name="application"
            label="报名"
            current={value(params, "application") ?? "all"}
          >
            <option value="all">全部状态</option>
            <option value="open">报名中</option>
            <option value="upcoming">报名未开始</option>
            <option value="closed">报名已结束</option>
            <option value="unknown">时间待确认</option>
          </FilterSelect>
          <button className="label-sans h-10 rounded-lg bg-deep-green px-5 text-white md:col-span-2 xl:col-span-8 xl:justify-self-end">
            应用筛选
          </button>
        </form>
      </Card>

      {result.index ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Metric label="已处理岗位" value={result.index.stats.processed} />
          <Metric label="资格符合" value={result.index.stats.eligible} />
          <Metric label="待确认" value={result.index.stats.needsConfirmation} />
          <Metric label="当前批次" value={result.index.stats.currentCampaigns} />
          <Metric label="上届参考" value={result.index.stats.referenceCampaigns} />
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
                    <Badge>{categoryLabels[job.category]}</Badge>
                    <Badge>{job.sourceLabel}</Badge>
                    <Badge tone={job.eligibility}>
                      {eligibilityLabels[job.eligibility]}
                    </Badge>
                    <Badge tone={job.batchStatus}>
                      {job.batchStatus === "current" ? "当前批次" : "上届参考"}
                    </Badge>
                    <Badge tone={job.applicationStatus}>
                      {applicationLabels[job.applicationStatus]}
                    </Badge>
                  </div>
                  <h2 className="mt-3 text-xl font-semibold">{job.title}</h2>
                  <p className="muted-copy mt-1">
                    {job.organization}{job.department ? ` · ${job.department}` : ""}
                  </p>
                  <p className="muted-copy mt-1 text-sm">
                    {job.region || "地区未标注"} · 职位代码 {job.positionCode} ·
                    招录 {job.recruitCount || "未标注"} 人
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
                <summary className="cursor-pointer font-semibold">
                  查看条件与判断依据
                </summary>
                <div className="muted-copy mt-3 grid gap-3 text-sm md:grid-cols-2">
                  <Requirement label="专业" value={job.requirements.major} />
                  <Requirement
                    label="学历/学位"
                    value={[
                      job.requirements.education,
                      job.requirements.degree,
                    ].filter(Boolean).join("；")}
                  />
                  <Requirement
                    label="政治面貌"
                    value={job.requirements.politicalStatus}
                  />
                  <Requirement
                    label="基层/项目经历"
                    value={[
                      job.requirements.grassrootsYears,
                      job.requirements.serviceProject,
                    ].filter(Boolean).join("；")}
                  />
                  <Requirement
                    label="其他限制"
                    value={[
                      job.requirements.freshGraduate,
                      job.requirements.age,
                      job.requirements.gender,
                      job.requirements.household,
                      job.requirements.certificate,
                    ].filter(Boolean).join("；")}
                    wide
                  />
                  <Requirement label="备注" value={job.requirements.remarks} wide />
                  <Requirement
                    label="判断"
                    value={
                      job.confirmationFields.length
                        ? `待确认：${job.confirmationFields.join("、")}`
                        : job.matchReasons.join("；")
                    }
                    wide
                  />
                </div>
              </details>
            </Card>
          ))}
          <div className="flex items-center justify-between pt-2">
            {result.page > 1 ? (
              <Link href={pageHref(params, result.page - 1)}>上一页</Link>
            ) : <span />}
            {result.page < result.pageCount ? (
              <Link href={pageHref(params, result.page + 1)}>下一页</Link>
            ) : <span />}
          </div>
        </section>
      ) : (
        <EmptyState
          title="没有找到符合当前筛选的岗位"
          description={
            result.index
              ? "可切换资格、地区、类别或批次后重新筛选。"
              : "岗位数据尚未通过4.0校验，请先完成岗位数据构建。"
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
      <select
        name={name}
        defaultValue={current}
        className="h-10 w-full rounded-lg border bg-white/70 px-3"
      >
        {children}
      </select>
    </label>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <Card className="p-4">
      <p className="muted-copy text-sm">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </Card>
  );
}

type BadgeTone =
  | JobEligibility
  | JobBatchStatus
  | JobApplicationStatus;

function Badge({
  children,
  tone,
}: {
  children: React.ReactNode;
  tone?: BadgeTone;
}) {
  const colors =
    tone === "eligible" || tone === "open" || tone === "current"
      ? "bg-[#e2ece5] text-[#356249]"
      : tone === "needs_confirmation" ||
          tone === "upcoming" ||
          tone === "unknown"
        ? "bg-[#f4ead7] text-[#8a652d]"
        : tone === "previous_reference"
          ? "bg-[#e7e8e5] text-[#626963]"
          : "bg-[#f4e1dc] text-[#934d41]";
  return (
    <span className={`label-sans rounded-full px-2.5 py-1 text-xs ${colors}`}>
      {children}
    </span>
  );
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
  return (
    <p className={wide ? "md:col-span-2" : ""}>
      <strong className="text-foreground">{label}：</strong>
      {value || "未标注"}
    </p>
  );
}
