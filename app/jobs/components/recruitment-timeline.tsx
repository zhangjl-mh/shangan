import {
  ArrowUpRight,
  CalendarClock,
  ChartNoAxesColumnIncreasing,
  ClipboardPenLine,
  FileText,
  UsersRound,
} from "lucide-react";
import type {
  JobRecruitmentCalendar,
  JobRecruitmentStageId,
} from "@/app/types/content";

const stageIcons: Record<
  JobRecruitmentStageId,
  React.ComponentType<{ size?: number; strokeWidth?: number }>
> = {
  announcement: FileText,
  registration: ClipboardPenLine,
  exam: CalendarClock,
  result: ChartNoAxesColumnIncreasing,
  second_interview: UsersRound,
};

export function RecruitmentTimeline({
  calendar,
}: {
  calendar: JobRecruitmentCalendar;
}) {
  return (
    <section className="surface relative mt-5 overflow-hidden rounded-2xl px-5 py-5 lg:px-7 lg:py-6">
      <div className="pointer-events-none absolute -right-24 -top-28 size-72 rounded-full bg-[#d6bc83]/16 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 left-1/3 size-56 rounded-full bg-[#7da08b]/12 blur-3xl" />

      <div className="relative flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-[21px] font-semibold text-deep-green">
              {calendar.title}
            </h2>
            <span className="label-sans rounded-full border border-[#ddcda9] bg-[#f6ecd8] px-3 py-1 text-xs font-medium tracking-[0.12em] text-[#806131]">
              规划参考 · 非官宣
            </span>
          </div>
          <p className="muted-copy mt-2 max-w-4xl text-sm leading-6">
            {calendar.description}
          </p>
        </div>
        <a
          href={calendar.sourcePortal.url}
          target="_blank"
          rel="noreferrer"
          className="label-sans inline-flex shrink-0 items-center gap-2 text-sm text-deep-green transition-transform hover:-translate-y-0.5"
        >
          {calendar.sourcePortal.label}
          <ArrowUpRight size={16} strokeWidth={1.8} />
        </a>
      </div>

      <div className="relative mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <div className="pointer-events-none absolute left-[8%] right-[8%] top-[25px] hidden h-px bg-gradient-to-r from-transparent via-[#aebcad] to-transparent xl:block" />
        {calendar.stages.map((stage, index) => {
          const Icon = stageIcons[stage.id];
          return (
            <article
              key={stage.id}
              className="group relative rounded-[14px] border border-white/70 bg-white/55 p-4 transition duration-300 hover:-translate-y-1 hover:border-[#b9c9bc] hover:bg-white/80 hover:shadow-[0_12px_30px_rgba(34,59,49,.08)]"
            >
              <div className="relative flex items-center justify-between">
                <span className="grid size-[50px] place-items-center rounded-full border border-[#d6dfd7] bg-[#f9fbf7] text-deep-green shadow-[0_7px_18px_rgba(39,68,55,.08)] transition duration-300 group-hover:scale-105 group-hover:bg-deep-green group-hover:text-white">
                  <Icon size={20} strokeWidth={1.7} />
                </span>
                <span className="label-sans text-xs tracking-[0.14em] text-[#8b948e]">
                  0{index + 1}
                </span>
              </div>
              <h3 className="mt-4 font-semibold text-deep-green">{stage.label}</h3>
              <p className="label-sans mt-1.5 text-[15px] font-medium text-[#ad604f]">
                {stage.display}
              </p>
              <p className="muted-copy mt-2 text-xs leading-5">{stage.note}</p>
            </article>
          );
        })}
      </div>

      <div className="relative mt-4 flex flex-col gap-3 border-t pt-4 lg:flex-row lg:items-center lg:justify-between">
        <p className="muted-copy text-xs leading-5">{calendar.disclaimer}</p>
        <details className="label-sans shrink-0 text-xs text-[#596861]">
          <summary className="cursor-pointer select-none">查看预测依据</summary>
          <div className="mt-2 grid gap-1.5 lg:absolute lg:right-0 lg:z-10 lg:w-[460px] lg:rounded-xl lg:border lg:bg-[#fffdf9] lg:p-3 lg:shadow-xl">
            {calendar.forecastBasis.map((source) => (
              <a
                key={source.url}
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="flex items-start justify-between gap-3 hover:text-deep-green"
              >
                <span>{source.label}</span>
                <span className="shrink-0">{source.publishedAt}</span>
              </a>
            ))}
          </div>
        </details>
      </div>
    </section>
  );
}
