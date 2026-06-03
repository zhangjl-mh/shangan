"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  CalendarClock,
  ExternalLink,
  House,
  IdCard,
  MapPin,
  ShieldCheck,
  Target,
  Users,
  Wallet,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { EligiblePosition, JobTrackingData, JobTrackingStatus } from "@/lib/types";

const trackingStatuses: JobTrackingStatus[] = [
  "未处理",
  "已收藏",
  "准备报名",
  "已报名",
  "待考试",
  "已结束",
  "放弃",
];

function displayCategory(category: string) {
  if (["事业单位", "教师", "医疗卫生"].includes(category)) return "编制";
  if (category === "国有企业") return "国企";
  return category;
}

function getRecruitmentClass(position: EligiblePosition) {
  if (position.recruitmentClass) return position.recruitmentClass;
  const category = displayCategory(position.category);
  if (position.sourceName.includes("国家公务员局") || position.recruitmentType?.includes("国考")) return "国考";
  if (category === "公务员") return "省考";
  return category;
}

function getRegionGroup(position: EligiblePosition) {
  if (position.regionGroup) return position.regionGroup;
  const text = position.region;
  if (text.includes("北京")) return "北京";
  if (["雄安", "雄县", "容城", "安新"].some((keyword) => text.includes(keyword))) return "雄安";
  if (text.includes("天津")) return "天津";
  if (["石家庄", "井陉", "鹿泉", "矿区", "藁城", "栾城", "正定"].some((keyword) => text.includes(keyword))) return "石家庄";
  return "其他";
}

function formatTimePoint(value?: string) {
  if (!value) return "以公告为准";
  const date = new Date(value.includes("T") ? value : `${value}T00:00:00+08:00`);
  if (Number.isNaN(date.getTime())) return value;
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("zh-CN", {
      timeZone: "Asia/Shanghai",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: value.includes("T") ? "2-digit" : undefined,
      minute: value.includes("T") ? "2-digit" : undefined,
      hourCycle: "h23",
    })
      .formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  );

  if (value.includes("T")) return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`;
  return `${parts.year}-${parts.month}-${parts.day}`;
}

export function JobDetailView({ position }: { position: EligiblePosition }) {
  const [tracking, setTracking] = useState<JobTrackingData>({ updatedAt: "", items: [] });
  const [saving, setSaving] = useState(false);
  const score = position.matchScore ?? 80;
  const risk = position.riskLevel ?? "中";
  const entryScore = position.historicalReferences?.[0]?.finalEntryScore ?? "官方未公开";
  const trackingStatus = tracking.items.find((item) => item.positionId === position.id)?.status ?? "未处理";

  useEffect(() => {
    fetch("/api/job-tracking")
      .then((response) => response.json())
      .then((data: JobTrackingData) => setTracking(data))
      .catch(() => setTracking({ updatedAt: "", items: [] }));
  }, []);

  async function saveTracking(nextStatus: JobTrackingStatus) {
    setSaving(true);
    const next: JobTrackingData = {
      updatedAt: new Date().toISOString(),
      items: [
        ...tracking.items.filter((item) => item.positionId !== position.id),
        { positionId: position.id, status: nextStatus, examDate: position.examDate, positionSnapshot: position },
      ],
    };
    setTracking(next);
    try {
      await fetch("/api/job-tracking", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(next),
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-5">
      <Link href="/job" className="label-sans inline-flex items-center gap-2 text-sm font-medium text-[#496b5b] hover:underline">
        <ArrowLeft size={16} /> 返回岗位列表
      </Link>

      <Card className="ornament-pavilion overflow-hidden rounded-[30px] border-[#dfd7c8] bg-[#fffdf8]/95 p-6 lg:p-8">
        <div className="relative z-10">
          <header className="flex flex-wrap items-start justify-between gap-5 border-b border-[#e8e1d5] pb-6">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{getRecruitmentClass(position)}</Badge>
                <Badge className="border-[#d8c69f] bg-[#faf4e6] text-[#80663b]">{getRegionGroup(position)}</Badge>
                <StatusBadge status={position.status} />
                <RiskBadge risk={risk} />
              </div>
              <h1 className="ink-title mt-4 text-[32px]">{position.organization}</h1>
              <p className="mt-2 text-xl text-[#3b5147]">{position.title}</p>
              <p className="label-sans mt-3 flex items-center gap-2 text-sm text-[#66766d]">
                <MapPin size={15} />{position.region}
              </p>
            </div>
            <div className="min-w-[146px] rounded-[24px] bg-[#edf2eb] px-6 py-5 text-center">
              <p className="label-sans text-xs tracking-[.18em] text-[#687970]">匹配度</p>
              <p className="mt-1 text-[40px] font-semibold text-[#315545]">{score}</p>
              <p className="label-sans text-xs text-[#50705f]">{position.matchLevel ?? "较为适配"}</p>
            </div>
          </header>

          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <PanelMetric icon={Users} label="招录人数" value={`${position.recruitCount ?? "-"} 人`} />
            <PanelMetric icon={Target} label="最低进面分" value={entryScore} />
            <PanelMetric icon={CalendarClock} label="报名截止" value={formatTimePoint(position.registrationEndAt ?? position.registrationEndDate)} />
            <PanelMetric icon={CalendarClock} label="考试时间" value={formatTimePoint(position.examDate)} />
            <PanelMetric icon={AlertTriangle} label="风险等级" value={`${risk}风险`} />
          </div>

          <TimelinePanel position={position} />

          <section className="mt-6 rounded-[20px] bg-[#edf3ec] p-5">
            <h2 className="flex items-center gap-2 font-semibold text-[#2f5141]"><ShieldCheck size={18} />推荐结论</h2>
            <p className="mt-3 text-sm leading-7 text-[#52675d]">
              {position.recommendation ?? "条件具有匹配基础，请在报名期以最新官方公告逐项复核。"}
            </p>
          </section>

          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            <PolicyBlock
              title="福利待遇"
              icon={Wallet}
              text={`${position.compensationReference?.text ?? "官方公告未载明具体薪酬金额。"} ${position.benefits?.join("；") ?? ""}`}
              note={position.compensationReference?.disclaimer}
              sourceName={position.sourceName}
              sourceUrl={position.sourceUrl}
              defaultOpen
            />
            <PolicyBlock
              title="房子与住房支持"
              icon={House}
              text={position.housingReference ?? "官方公告未载明住房、配租或住房补贴安排。"}
              sourceName={position.sourceName}
              sourceUrl={position.sourceUrl}
            />
            <PolicyBlock
              title="户口与落户"
              icon={IdCard}
              text={position.householdReference ?? "官方公告未载明户口或落户承诺。"}
              sourceName={position.sourceName}
              sourceUrl={position.sourceUrl}
            />
          </div>

          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            <AdviceBlock title="风险提醒" icon={AlertTriangle} items={position.riskReminders ?? ["报名状态及限制条件以官方公告为准"]} warning />
            <AdviceBlock title="备考建议" icon={BookOpen} items={position.studyAdvice ?? ["根据考试类别安排基础练习与真题复盘"]} />
          </div>

          <footer className="label-sans mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-[#e8e1d5] pt-5 text-sm">
            <label className="flex items-center gap-3 text-[#64746c]">
              我的跟进
              <select
                aria-label={`${position.title} 跟踪状态`}
                disabled={saving}
                value={trackingStatus}
                onChange={(event) => saveTracking(event.target.value as JobTrackingStatus)}
                className="rounded-lg border border-[#ded8cc] bg-white/80 px-3 py-2 outline-none"
              >
                {trackingStatuses.map((status) => <option key={status}>{status}</option>)}
              </select>
            </label>
            <a href={position.sourceUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-[#496b5b] hover:underline">
              查看官方公告与附件 <ExternalLink size={14} />
            </a>
          </footer>
        </div>
      </Card>
    </div>
  );
}

function TimelinePanel({ position }: { position: EligiblePosition }) {
  const items = [
    { label: "公告发布", value: position.announcementDate, hint: "官方原文", state: "done" },
    {
      label: "报名截止",
      value: position.registrationEndAt ?? position.registrationEndDate,
      hint: position.status === "报名中" ? "窗口开放中" : "已截止",
      state: position.status === "报名中" ? "active" : "done",
    },
    { label: "资格初审", value: position.qualificationReviewEndAt, hint: "审核截止", state: position.status === "待考试" ? "active" : "upcoming" },
    { label: "缴费截止", value: position.paymentEndAt, hint: "缴费确认", state: position.status === "待考试" ? "active" : "upcoming" },
    { label: "笔试时间", value: position.examDate, hint: position.status === "待考试" ? "待进行" : "考试安排", state: "upcoming" },
  ].filter((item) => item.value);

  if (!items.length) return null;

  return (
    <section className="mt-6 rounded-[22px] border border-[#e6dfd2] bg-[#fbfaf5]/85 p-5">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2 font-semibold text-[#2f5141]">
          <CalendarClock size={18} />考试时间轴
        </h2>
        <span className="label-sans text-xs text-[#7a887f]">报名、审核、缴费、笔试一眼看清</span>
      </div>
      <div className="grid gap-3 md:grid-cols-5">
        {items.map((item, index) => (
          <div
            key={`${item.label}-${item.value}`}
            className={`relative overflow-hidden rounded-2xl border px-4 py-3 ${
              item.state === "done"
                ? "border-[#dae3d8] bg-[#eef4ed]"
                : item.state === "active"
                  ? "border-[#d9bc80] bg-[#fbf4e4]"
                  : "border-[#dde4ea] bg-[#f3f7f8]"
            }`}
          >
            <span className="label-sans text-[11px] text-[#728078]">0{index + 1}</span>
            <p className="mt-1 text-sm font-semibold text-[#304d40]">{item.label}</p>
            <p className="label-sans mt-2 text-sm text-[#52675d]">{formatTimePoint(item.value)}</p>
            <p className="label-sans mt-1 text-[11px] text-[#809087]">{item.hint}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function PanelMetric({ icon: Icon, label, value }: { icon: typeof Users; label: string; value: string }) {
  return (
    <div className="label-sans rounded-[17px] border border-[#ece5da] bg-white/65 p-4">
      <p className="flex items-center gap-2 text-xs text-[#718178]"><Icon size={15} />{label}</p>
      <p className="mt-2 text-sm font-medium leading-6 text-[#304c40]">{value}</p>
    </div>
  );
}

function AdviceBlock({ title, icon: Icon, items, warning = false }: { title: string; icon: typeof AlertTriangle; items: string[]; warning?: boolean }) {
  return (
    <section className={`rounded-[18px] p-5 ${warning ? "bg-[#faf4e9]" : "bg-[#f7f6f1]"}`}>
      <h2 className="flex items-center gap-2 font-semibold text-[#304d40]"><Icon size={17} />{title}</h2>
      <ul className="label-sans mt-3 space-y-2 text-sm leading-6 text-[#617168]">
        {items.map((item) => <li key={item}>- {item}</li>)}
      </ul>
    </section>
  );
}

function PolicyBlock({
  title,
  icon: Icon,
  text,
  note,
  sourceName,
  sourceUrl,
  defaultOpen = false,
}: {
  title: string;
  icon: typeof Wallet;
  text: string;
  note?: string;
  sourceName: string;
  sourceUrl: string;
  defaultOpen?: boolean;
}) {
  return (
    <details open={defaultOpen} className="group rounded-[18px] border border-[#e5ddcf] bg-[#fffdf8] p-5">
      <summary className="flex cursor-pointer list-none items-center justify-between font-semibold text-[#304d40]">
        <span className="flex items-center gap-2"><Icon size={17} />{title}</span>
        <span className="label-sans text-xs text-[#64786c] group-open:hidden">展开</span>
        <span className="label-sans hidden text-xs text-[#64786c] group-open:block">收起</span>
      </summary>
      <p className="label-sans mt-4 text-sm leading-7 text-[#617168]">{text}</p>
      {note ? <p className="label-sans mt-2 text-xs leading-6 text-[#947a54]">{note}</p> : null}
      <a href={sourceUrl} target="_blank" rel="noreferrer" className="label-sans mt-4 inline-flex items-center gap-1.5 text-xs font-medium text-[#466858] hover:underline">
        核对公告来源：{sourceName} <ExternalLink size={12} />
      </a>
    </details>
  );
}

function StatusBadge({ status }: { status: string }) {
  return <Badge className="border-[#9cb29e] bg-[#edf4eb] text-[#496953]">{status}</Badge>;
}

function RiskBadge({ risk }: { risk: string }) {
  const color = risk === "低" ? "bg-[#edf4eb] text-[#48705a]" : risk === "中" ? "bg-[#faf3e5] text-[#957043]" : "bg-[#f7ebe7] text-[#93584b]";
  return <span className={`rounded-full px-3 py-1 text-xs ${color}`}>{risk}风险</span>;
}
