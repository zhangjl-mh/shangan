import {
  BriefcaseBusiness,
  ChevronRight,
  Search,
} from "lucide-react";
import { Card } from "@/app/components/ui/card";
import { EmptyState } from "@/app/components/layout/empty-state";
import { JobCard } from "@/app/jobs/components/job-card";
import { RecruitmentTimeline } from "@/app/jobs/components/recruitment-timeline";
import {
  getJobRecruitmentCalendar,
  queryJobs,
} from "@/app/services/jobs";
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

const categoryLabels: Record<JobCategory, string> = {
  civil_service: "公务员",
  institution: "事业单位",
  military_civilian: "军队文职",
  state_owned_enterprise: "国央企",
};

export default async function JobsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params = await searchParams;
  const selectedCategory =
    (value(params, "category") as JobCategory | "all") ?? "civil_service";
  const requestedExam = value(params, "exam");
  const selectedExam =
    selectedCategory !== "civil_service" &&
    requestedExam === "national-civil-service"
      ? "all"
      : requestedExam ?? "national-civil-service";
  const [result, recruitmentCalendar] = await Promise.all([
    queryJobs({
      exam: selectedExam,
      region: value(params, "region"),
      category: selectedCategory,
      eligibility:
        (value(params, "eligibility") as JobEligibility) ?? "eligible",
      batch: (value(params, "batch") as JobBatchStatus | "all") ?? "all",
      application:
        (value(params, "application") as
          | JobApplicationStatus
          | "all") ?? "all",
      keyword: value(params, "q"),
      paginate: false,
    }),
    selectedCategory === "state_owned_enterprise"
      ? getJobRecruitmentCalendar("state_owned_enterprise")
      : Promise.resolve(null),
  ]);

  return (
    <main className="mx-auto max-w-[1800px] px-4 pb-10 pt-8 lg:px-9 lg:pt-9">
      <section>
        <div className="muted-copy flex items-center gap-2 text-sm">
          <span>首页</span>
          <ChevronRight size={14} strokeWidth={1.7} />
          <span>岗位</span>
        </div>
        <h1 className="ink-title mt-6 flex items-center gap-4 text-[30px] leading-none lg:text-[32px]">
          <BriefcaseBusiness size={36} strokeWidth={1.8} />
          岗位筛选
        </h1>
      </section>

      <Card className="mt-7 px-5 py-6 lg:px-7 lg:py-8">
        <form className="grid items-end gap-4 sm:grid-cols-2 lg:grid-cols-4 2xl:grid-cols-[2.1fr_1.03fr_1.06fr_1.08fr_.99fr_.9fr_.88fr_130px] 2xl:gap-x-[30px]">
          <label className="lg:col-span-2 2xl:col-span-1">
            <span className="muted-copy mb-2.5 block text-[15px]">关键词</span>
            <span className="flex h-[54px] items-center gap-3 rounded-[10px] border bg-white/70 px-4">
              <Search size={18} strokeWidth={1.8} />
              <input
                name="q"
                defaultValue={value(params, "q")}
                placeholder="职位、单位、专业或代码"
                className="min-w-0 flex-1 bg-transparent text-[17px] outline-none placeholder:text-[#9a9b99]"
              />
            </span>
          </label>
          <FilterSelect
            name="category"
            label="类别"
            current={selectedCategory}
          >
            <option value="all">全部类别</option>
            {Object.entries(categoryLabels).map(([id, label]) => (
              <option key={id} value={id}>{label}</option>
            ))}
          </FilterSelect>
          <FilterSelect name="exam" label="来源" current={selectedExam}>
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
          <button className="label-sans h-[54px] rounded-[10px] bg-deep-green px-5 text-[17px] font-medium text-white shadow-[0_6px_16px_rgba(21,58,53,.12)] sm:col-span-2 lg:col-span-4 2xl:col-span-1">
            应用筛选
          </button>
        </form>
      </Card>

      {recruitmentCalendar ? (
        <RecruitmentTimeline calendar={recruitmentCalendar} />
      ) : null}

      {result.index ? (
        <div className="mt-5 flex min-h-[58px] flex-wrap items-center gap-x-7 gap-y-1 rounded-[14px] border bg-white/55 px-6 py-3 text-base">
          <CompactMetric label="符合" value={result.index.stats.eligible} />
          <CompactMetric label="待确认" value={result.index.stats.needsConfirmation} />
          <CompactMetric label="当前批次" value={result.index.stats.currentCampaigns} />
          <CompactMetric label="上届参考" value={result.index.stats.referenceCampaigns} />
          <span className="muted-copy ml-auto">
            当前显示
            <strong className="mx-2 text-[17px] text-deep-green">{result.total}</strong>
            个岗位
          </span>
        </div>
      ) : null}

      {result.items.length ? (
        <section className="mt-5">
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
            {result.items.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                categoryLabel={categoryLabels[job.category]}
              />
            ))}
          </div>
        </section>
      ) : (
        <EmptyState
          title="没有找到符合当前筛选的岗位"
          description={
            result.index
              ? selectedCategory === "state_owned_enterprise"
                ? "当前没有“确认符合”的国央企岗位，可将资格切换为“待确认”；下一轮招聘节奏见上方。"
                : "可切换资格、地区、类别或批次后重新筛选。"
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
      <span className="muted-copy mb-2.5 block text-[15px]">{label}</span>
      <select
        name={name}
        defaultValue={current}
        className="h-[54px] w-full rounded-[10px] border bg-white/70 px-4 text-[17px]"
      >
        {children}
      </select>
    </label>
  );
}

function CompactMetric({ label, value }: { label: string; value: number }) {
  return (
    <span>
      <span className="muted-copy">{label}</span>
      <strong className="ml-2 text-foreground">{value}</strong>
    </span>
  );
}
