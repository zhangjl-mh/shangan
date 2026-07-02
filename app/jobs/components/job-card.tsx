"use client";

import { useId, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ExternalLink, MapPin, Sparkles } from "lucide-react";
import type {
  JobApplicationStatus,
  JobBatchStatus,
  JobEligibility,
  JobPosition,
} from "@/app/types/content";

type PanelSide = "left" | "right" | "overlay";

const applicationLabels: Record<JobApplicationStatus, string> = {
  upcoming: "报名未开始",
  open: "报名中",
  closed: "报名已结束",
  unknown: "报名时间待确认",
};

export function JobCard({
  job,
  categoryLabel,
}: {
  job: JobPosition;
  categoryLabel: string;
}) {
  const cardRef = useRef<HTMLElement>(null);
  const panelId = useId();
  const reduceMotion = useReducedMotion();
  const [open, setOpen] = useState(false);
  const [panelSide, setPanelSide] = useState<PanelSide>("right");
  const [panelWidth, setPanelWidth] = useState(390);

  function positionPanel() {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    if (window.innerWidth < 768) {
      setPanelSide("overlay");
      return;
    }

    const rightSpace = window.innerWidth - rect.right - 16;
    const leftSpace = rect.left - 16;
    const side = rightSpace >= leftSpace ? "right" : "left";
    const available = Math.max(rightSpace, leftSpace);
    setPanelSide(side);
    setPanelWidth(Math.max(320, Math.min(390, available - 12)));
  }

  function revealPanel() {
    positionPanel();
    setOpen(true);
  }

  return (
    <motion.article
      ref={cardRef}
      tabIndex={0}
      aria-describedby={open ? panelId : undefined}
      onMouseEnter={revealPanel}
      onMouseLeave={(event) => {
        if (!event.currentTarget.contains(document.activeElement)) {
          setOpen(false);
        }
      }}
      onFocusCapture={revealPanel}
      onBlurCapture={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setOpen(false);
        }
      }}
      onKeyDown={(event) => {
        if (event.key === "Escape") {
          setOpen(false);
          cardRef.current?.focus();
        }
      }}
      whileHover={reduceMotion ? undefined : { y: -5, scale: 1.008 }}
      transition={{ type: "spring", stiffness: 360, damping: 28 }}
      className="surface group relative flex min-h-[340px] flex-col rounded-2xl p-4 outline-none transition-[border-color,box-shadow] duration-300 hover:z-30 hover:border-[#9fb4a5] hover:shadow-[0_18px_44px_rgba(29,57,48,.13)] focus:z-30 focus-visible:ring-2 focus-visible:ring-[#6f917f] focus-visible:ring-offset-4 focus-visible:ring-offset-background"
    >
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{categoryLabel}</Badge>
        {job.eligibility === "needs_confirmation" ? (
          <Badge tone="needs_confirmation">待确认</Badge>
        ) : null}
      </div>

      <div className="mt-4 flex min-w-0 items-start justify-between gap-3">
        <h2 className="line-clamp-2 min-w-0 text-[20px] font-semibold leading-[1.45]">
          {job.title}
        </h2>
        <span className="label-sans mt-0.5 shrink-0 rounded-full border border-[#d8dfd8] bg-[#f6f8f4] px-3 py-1 text-[15px] text-deep-green">
          {job.recruitCount ? `${job.recruitCount}人` : "人数待定"}
        </span>
      </div>

      <p className="muted-copy mt-2 line-clamp-1 text-[15px]">
        {job.organization}
      </p>
      <p className="muted-copy mt-3 flex items-center gap-2 text-[15px]">
        <MapPin size={16} strokeWidth={1.7} />
        <span className="line-clamp-1">
          {job.region || "地区未标注"}
          <span className="mx-2">·</span>
          {job.positionCode}
        </span>
      </p>

      <div className="mt-5 space-y-2.5 border-t pt-4 text-base leading-relaxed">
        <CompactRequirement label="专业" value={job.requirements.major} />
        <CompactRequirement
          label="学历"
          value={job.requirements.education}
        />
        {job.confirmationFields.length ? (
          <CompactRequirement
            label="待确认"
            value={job.confirmationFields.join("、")}
          />
        ) : null}
      </div>

      <div className="mt-auto flex items-center justify-between border-t pt-3">
        <Badge tone={job.applicationStatus}>
          {applicationLabels[job.applicationStatus]}
        </Badge>
        <a
          href={job.source.portalUrl}
          target="_blank"
          rel="noreferrer"
          className="label-sans flex items-center gap-2 text-[15px] text-foreground transition-colors hover:text-deep-green"
        >
          官方公告
          <ExternalLink size={15} strokeWidth={1.7} />
        </a>
      </div>

      <AnimatePresence>
        {open ? (
          <FullJobDetails
            id={panelId}
            job={job}
            categoryLabel={categoryLabel}
            side={panelSide}
            width={panelWidth}
            reduceMotion={Boolean(reduceMotion)}
          />
        ) : null}
      </AnimatePresence>
    </motion.article>
  );
}

function FullJobDetails({
  id,
  job,
  categoryLabel,
  side,
  width,
  reduceMotion,
}: {
  id: string;
  job: JobPosition;
  categoryLabel: string;
  side: PanelSide;
  width: number;
  reduceMotion: boolean;
}) {
  const requirementRows: Array<[string, string]> = [
    ["专业", requirementValue(job, "major")],
    ["学历", requirementValue(job, "education")],
    ["学位", requirementValue(job, "degree")],
    ["政治面貌", requirementValue(job, "politicalStatus")],
    ["应届身份", requirementValue(job, "freshGraduate")],
    ["基层年限", requirementValue(job, "grassrootsYears")],
    ["服务项目", requirementValue(job, "serviceProject")],
    ["年龄", requirementValue(job, "age")],
    ["性别", requirementValue(job, "gender")],
    ["户籍", requirementValue(job, "household")],
    ["资格证书", requirementValue(job, "certificate")],
    ["备注", requirementValue(job, "remarks")],
  ];
  const direction = side === "right" ? -1 : 1;
  const placement =
    side === "right"
      ? "left-full top-1/2 -translate-y-1/2 pl-3"
      : side === "left"
        ? "right-full top-1/2 -translate-y-1/2 pr-3"
        : "inset-x-0 top-0 px-2";

  return (
    <motion.div
      id={id}
      role="dialog"
      aria-label={`${job.title}完整岗位条件`}
      className={`absolute z-50 ${placement}`}
      style={side === "overlay" ? undefined : { width: width + 12 }}
      initial={
        reduceMotion
          ? { opacity: 0 }
          : {
              opacity: 0,
              x: side === "overlay" ? 0 : 24 * direction,
              scale: 0.94,
              rotateY: side === "overlay" ? 0 : 4 * direction,
              filter: "blur(7px)",
            }
      }
      animate={{
        opacity: 1,
        x: 0,
        scale: 1,
        rotateY: 0,
        filter: "blur(0px)",
      }}
      exit={
        reduceMotion
          ? { opacity: 0 }
          : {
              opacity: 0,
              x: side === "overlay" ? 0 : 14 * direction,
              scale: 0.97,
              filter: "blur(4px)",
            }
      }
      transition={
        reduceMotion
          ? { duration: 0.01 }
          : { type: "spring", stiffness: 340, damping: 28, mass: 0.82 }
      }
    >
      <div
        className="relative rounded-[23px] bg-[linear-gradient(135deg,rgba(95,137,112,.9),rgba(217,178,105,.76),rgba(186,100,82,.72))] p-px shadow-[0_28px_70px_rgba(20,46,39,.28)]"
        style={side === "overlay" ? undefined : { width }}
      >
        <div className="relative max-h-[min(78vh,720px)] overflow-y-auto rounded-[22px] bg-[rgba(255,253,249,.97)] p-5 backdrop-blur-xl">
          <div className="pointer-events-none absolute -right-16 -top-20 h-44 w-44 rounded-full bg-[#d9c58d]/25 blur-3xl" />
          <div className="pointer-events-none absolute -left-12 bottom-4 h-32 w-32 rounded-full bg-[#82aa91]/20 blur-3xl" />
          <div className="pointer-events-none absolute inset-x-8 top-0 h-px bg-gradient-to-r from-transparent via-white to-transparent" />

          <div className="relative flex flex-wrap items-center gap-2">
            <Badge>{categoryLabel}</Badge>
            <Badge tone={job.applicationStatus}>
              {applicationLabels[job.applicationStatus]}
            </Badge>
            <span className="label-sans ml-auto rounded-full border border-[#d8dfd8] bg-[#f6f8f4]/90 px-3 py-1 text-[15px] text-deep-green">
              {job.recruitCount ? `${job.recruitCount}人` : "人数待定"}
            </span>
          </div>

          <div className="relative mt-4 flex items-start gap-3">
            <span className="mt-1 grid size-8 shrink-0 place-items-center rounded-full bg-deep-green text-white shadow-[0_8px_20px_rgba(21,58,53,.24)]">
              <Sparkles size={15} strokeWidth={1.8} />
            </span>
            <div>
              <h3 className="text-[20px] font-semibold leading-snug">
                {job.title}
              </h3>
              <p className="muted-copy mt-1 text-[15px]">{job.organization}</p>
            </div>
          </div>

          <div className="relative mt-4 grid grid-cols-[78px_minmax(0,1fr)] gap-x-3 gap-y-2 border-t pt-4 text-[14px] leading-relaxed">
            <FullDetail label="部门" value={job.department || "未标注"} />
            <FullDetail label="地区" value={job.region || "未标注"} />
            <FullDetail label="职位代码" value={job.positionCode} />
            <FullDetail label="岗位来源" value={job.sourceLabel} />
            <FullDetail
              label="岗位批次"
              value={job.batchStatus === "current" ? "当前批次" : "上届参考"}
            />
            <FullDetail
              label="考试时间"
              value={formatJobDate(job.examAt) || "时间待确认"}
            />
            <FullDetail
              label="报名时间"
              value={formatRegistration(job.registration)}
            />
            {requirementRows.map(([label, detail]) => (
              <FullDetail key={label} label={label} value={detail} />
            ))}
            {job.confirmationFields.length ? (
              <FullDetail
                label="待确认项"
                value={job.confirmationFields.join("、")}
              />
            ) : null}
          </div>

          <a
            href={job.source.portalUrl}
            target="_blank"
            rel="noreferrer"
            className="label-sans relative mt-4 flex items-center justify-end gap-2 border-t pt-3 text-[15px] text-deep-green"
          >
            查看官方详情
            <ExternalLink size={15} strokeWidth={1.7} />
          </a>
        </div>
      </div>
    </motion.div>
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
    <span className={`label-sans rounded-[9px] px-2.5 py-1 text-[15px] ${colors}`}>
      {children}
    </span>
  );
}

function CompactRequirement({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <p className="line-clamp-2">
      <strong className="text-foreground">{label}：</strong>
      {value || "未标注"}
    </p>
  );
}

function FullDetail({ label, value }: { label: string; value: string }) {
  return (
    <>
      <span className="muted-copy">{label}</span>
      <span className="break-words">{value}</span>
    </>
  );
}

function requirementValue(
  job: JobPosition,
  field: keyof JobPosition["requirements"],
) {
  const state = job.requirementStates[field];
  if (state === "unrestricted") return "不限";
  if (state === "unparsed") return job.requirements[field] || "解析待确认";
  if (state === "missing") return "未标注";
  return job.requirements[field] || "未标注";
}

function formatRegistration(registration: JobPosition["registration"]) {
  const opensAt = formatJobDate(registration.opensAt);
  const closesAt = formatJobDate(registration.closesAt);
  if (opensAt && closesAt) return `${opensAt} 至 ${closesAt}`;
  return opensAt || closesAt || "时间待确认";
}

function formatJobDate(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Shanghai",
  }).format(date);
}
