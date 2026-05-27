"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Bookmark,
  BookOpen,
  ExternalLink,
  GraduationCap,
  House,
  IdCard,
  MapPin,
  Search,
  ShieldCheck,
  Target,
  Users,
  Wallet,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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

export function JobDirectory({ positions }: { positions: EligiblePosition[] }) {
  const [query, setQuery] = useState("");
  const [region, setRegion] = useState("全部地区");
  const [category, setCategory] = useState("全部类型");
  const [status, setStatus] = useState("全部状态");
  const [selectedId, setSelectedId] = useState(positions[0]?.id ?? "");
  const [showTrackedOnly, setShowTrackedOnly] = useState(false);
  const [tracking, setTracking] = useState<JobTrackingData>({ updatedAt: "", items: [] });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch("/api/job-tracking")
      .then((response) => response.json())
      .then((data: JobTrackingData) => setTracking(data))
      .catch(() => setTracking({ updatedAt: "", items: [] }));
  }, []);

  const regions = ["全部地区", ...new Set(positions.map((position) => position.region))];
  const categories = ["全部类型", ...new Set(positions.map((position) => position.category))];
  const sourcePositions = useMemo(() => {
    if (!showTrackedOnly) return positions;
    return tracking.items
      .filter((item) => item.status !== "未处理")
      .map((item) => positions.find((position) => position.id === item.positionId) ?? item.positionSnapshot)
      .filter((position): position is EligiblePosition => Boolean(position));
  }, [positions, showTrackedOnly, tracking.items]);
  const filtered = useMemo(() => sourcePositions.filter((position) => {
    const keyword = query.trim().toLowerCase();
    const text = [
      position.title,
      position.organization,
      position.department,
      position.positionCode,
      position.region,
      position.majorRequirement,
    ].join(" ").toLowerCase();
    const isOpen = position.status === "报名中" || position.status === "即将报名";
    return (
      (!keyword || text.includes(keyword)) &&
      (region === "全部地区" || position.region === region) &&
      (category === "全部类型" || position.category === category) &&
      (status === "全部状态" || (status === "可报名" ? isOpen : position.status === status))
    );
  }), [category, query, region, sourcePositions, status]);
  const selected = filtered.find((position) => position.id === selectedId) ?? filtered[0] ?? positions[0];

  async function saveTracking(position: EligiblePosition, nextStatus: JobTrackingStatus) {
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

  const openCount = positions.filter((position) => position.status === "报名中" || position.status === "即将报名").length;
  const strongCount = positions.filter((position) => (position.matchScore ?? 0) >= 90).length;

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-3">
        <SummaryCard label="符合条件岗位" value={`${positions.length} 个`} detail="含可比历史岗位" />
        <SummaryCard label="当前可报名" value={`${openCount} 个`} detail={openCount ? "请核验截止时间" : "等待新公告发布"} />
        <SummaryCard label="高度适配" value={`${strongCount} 个`} detail="匹配分 90 分以上" />
      </section>

      <Card className="label-sans rounded-[24px] border-[#e3ddcf] bg-[#fcfbf7]/95 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex min-w-[250px] flex-1 items-center gap-2 rounded-xl border border-[#e6e0d5] bg-white/80 px-4 py-2.5">
            <Search size={17} className="text-[#718178]" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="w-full bg-transparent text-sm outline-none"
              placeholder="搜索岗位、单位、地区或专业"
            />
          </label>
          <FilterSelect value={region} options={regions} onChange={setRegion} />
          <FilterSelect value={category} options={categories} onChange={setCategory} />
          <FilterSelect value={status} options={["全部状态", "可报名", "报名中", "即将报名", "已截止", "已结束"]} onChange={setStatus} />
          <Button size="sm" variant={showTrackedOnly ? "default" : "outline"} onClick={() => setShowTrackedOnly((current) => !current)}>
            <Bookmark size={15} /> 我已关注
          </Button>
        </div>
      </Card>

      {selected ? (
        <DecisionPanel
          position={selected}
          saving={saving}
          trackingStatus={tracking.items.find((item) => item.positionId === selected.id)?.status ?? "未处理"}
          onTrackingChange={(nextStatus) => saveTracking(selected, nextStatus)}
        />
      ) : null}

      <section>
        <div className="mb-4 flex items-end justify-between gap-3">
          <div>
            <h2 className="ink-title text-[27px]">全部符合岗位</h2>
            <p className="label-sans mt-1 text-sm text-[#66756d]">当前筛选显示 {filtered.length} 个，点击卡片查看判断结论与官方来源。</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((position) => (
            <PositionCard
              key={position.id}
              position={position}
              active={selected?.id === position.id}
              onSelect={() => setSelectedId(position.id)}
            />
          ))}
        </div>
        {!filtered.length ? <Card className="p-10 text-center text-[#67756e]">没有符合当前筛选条件的岗位。</Card> : null}
      </section>
    </div>
  );
}

function DecisionPanel({
  position,
  saving,
  trackingStatus,
  onTrackingChange,
}: {
  position: EligiblePosition;
  saving: boolean;
  trackingStatus: JobTrackingStatus;
  onTrackingChange: (status: JobTrackingStatus) => void;
}) {
  const score = position.matchScore ?? 80;
  const risk = position.riskLevel ?? (position.status === "报名中" ? "中" : "高");
  const entryScore = position.historicalReferences?.[0]?.finalEntryScore ?? "官方未公开";

  return (
    <Card className="ornament-pavilion overflow-hidden rounded-[30px] border-[#dfd7c8] bg-[#fffdf8]/95 p-6 lg:p-8">
      <div className="relative z-10">
        <header className="flex flex-wrap items-start justify-between gap-5 border-b border-[#e8e1d5] pb-6">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>{position.category}</Badge>
              <StatusBadge status={position.status} />
              <RiskBadge risk={risk} />
            </div>
            <h2 className="ink-title mt-4 text-[29px]">{position.organization}</h2>
            <p className="mt-2 text-lg text-[#3b5147]">{position.title}</p>
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

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <PanelMetric icon={Users} label="招录人数" value={`${position.recruitCount ?? "-"} 人`} />
          <PanelMetric icon={GraduationCap} label="学历要求" value={position.educationRequirement ?? "以公告为准"} />
          <PanelMetric icon={Target} label="最低进面分" value={entryScore} />
          <PanelMetric icon={AlertTriangle} label="风险等级" value={`${risk}风险`} />
        </div>

        <section className="mt-6 rounded-[20px] bg-[#edf3ec] p-5">
          <h3 className="flex items-center gap-2 font-semibold text-[#2f5141]"><ShieldCheck size={18} />推荐结论</h3>
          <p className="mt-3 text-sm leading-7 text-[#52675d]">
            {position.recommendation ?? "条件具有匹配基础，请在报名期以最新官方公告逐项复核。"}
          </p>
        </section>

        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <AdviceBlock title="匹配原因" icon={Target} items={position.matchReasons ?? ["专业、学历和地区在岗位公开条件范围内"]} />
          <AdviceBlock title="风险提醒" icon={AlertTriangle} items={position.riskReminders ?? ["报名状态及限制条件以官方公告为准"]} warning />
          <AdviceBlock title="备考建议" icon={BookOpen} items={position.studyAdvice ?? ["根据考试类别安排基础练习与真题复盘"]} />
        </div>

        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          <InfoBlock title="福利待遇" icon={Wallet} text={`${position.compensationReference?.text ?? "官方未公开具体待遇。"} ${position.benefits?.[0] ?? ""}`} note={position.compensationReference?.disclaimer} />
          <InfoBlock title="房子" icon={House} text={position.housingReference ?? "官方材料未载明住房安排。"} />
          <InfoBlock title="户口" icon={IdCard} text={position.householdReference ?? "官方材料未载明落户承诺。"} />
        </div>

        <footer className="label-sans mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-[#e8e1d5] pt-5 text-sm">
          <label className="flex items-center gap-3 text-[#64746c]">
            我的跟进
            <select
              aria-label={`${position.title} 跟踪状态`}
              disabled={saving}
              value={trackingStatus}
              onChange={(event) => onTrackingChange(event.target.value as JobTrackingStatus)}
              className="rounded-lg border border-[#ded8cc] bg-white/80 px-3 py-2 outline-none"
            >
              {trackingStatuses.map((tracking) => <option key={tracking}>{tracking}</option>)}
            </select>
          </label>
          <a href={position.sourceUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-[#496b5b] hover:underline">
            查看官方公告与附件 <ExternalLink size={14} />
          </a>
        </footer>
      </div>
    </Card>
  );
}

function PositionCard({ position, active, onSelect }: { position: EligiblePosition; active: boolean; onSelect: () => void }) {
  const risk = position.riskLevel ?? (position.status === "报名中" ? "中" : "高");
  return (
    <button
      type="button"
      onClick={onSelect}
      className={`label-sans flex h-full flex-col rounded-[25px] border p-5 text-left transition-all ${
        active ? "border-[#8da995] bg-[#f1f5ee] shadow-[0_10px_28px_rgba(49,72,60,.08)]" : "border-[#e5ded2] bg-[#fffdf9] hover:border-[#bfccbe]"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <Badge>{position.category}</Badge>
        <RiskBadge risk={risk} />
      </div>
      <h3 className="mt-4 text-base font-semibold leading-7 text-[#293d34]">{position.organization}</h3>
      <p className="mt-1 text-sm text-[#52675d]">{position.title}</p>
      <p className="mt-3 flex items-center gap-1.5 text-xs text-[#6a776f]"><MapPin size={13} />{position.region}</p>
      <div className="mt-4 grid grid-cols-3 gap-2 rounded-xl bg-[#f5f4ee] p-3 text-center">
        <CardMetric label="匹配度" value={`${position.matchScore ?? 80}`} />
        <CardMetric label="招录" value={`${position.recruitCount ?? "-"}人`} />
        <CardMetric label="进面分" value={position.historicalReferences?.[0]?.finalEntryScore ?? "-"} />
      </div>
      <p className="mt-4 line-clamp-2 text-xs leading-6 text-[#65746d]">
        <span className="font-medium text-[#3e5a4c]">学历专业：</span>
        {position.educationRequirement ?? "以公告为准"}；{position.majorRequirement ?? "以公告为准"}
      </p>
      <div className="mt-auto flex items-center justify-between border-t border-[#eee7da] pt-4 text-xs">
        <StatusBadge status={position.status} />
        <span className="font-medium text-[#496b5b]">查看判断</span>
      </div>
    </button>
  );
}

function SummaryCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <Card className="rounded-[24px] border-[#e6dfd2] bg-[#fffdf9] p-5">
      <p className="label-sans text-sm text-[#687970]">{label}</p>
      <p className="mt-2 text-[31px] text-[#294a3b]">{value}</p>
      <p className="label-sans mt-1 text-xs text-[#809087]">{detail}</p>
    </Card>
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

function AdviceBlock({ title, icon: Icon, items, warning = false }: { title: string; icon: typeof Target; items: string[]; warning?: boolean }) {
  return (
    <section className={`rounded-[18px] p-5 ${warning ? "bg-[#faf4e9]" : "bg-[#f7f6f1]"}`}>
      <h3 className="flex items-center gap-2 font-semibold text-[#304d40]"><Icon size={17} />{title}</h3>
      <ul className="label-sans mt-3 space-y-2 text-sm leading-6 text-[#617168]">
        {items.map((item) => <li key={item}>- {item}</li>)}
      </ul>
    </section>
  );
}

function InfoBlock({ title, icon: Icon, text, note }: { title: string; icon: typeof Wallet; text: string; note?: string }) {
  return (
    <section className="rounded-[18px] border border-[#ece4d6] bg-white/55 p-5">
      <h3 className="flex items-center gap-2 font-semibold text-[#304d40]"><Icon size={17} />{title}</h3>
      <p className="label-sans mt-3 text-sm leading-7 text-[#617168]">{text}</p>
      {note ? <p className="label-sans mt-2 text-xs leading-6 text-[#947a54]">{note}</p> : null}
    </section>
  );
}

function CardMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] text-[#75837c]">{label}</p>
      <p className="mt-1 font-semibold text-[#315545]">{value}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "报名中" || status === "即将报名"
      ? "border-[#9cb29e] bg-[#edf4eb] text-[#496953]"
      : "border-[#ddd5c5] bg-[#f6f2ea] text-[#806d50]";
  return <Badge className={color}>{status}</Badge>;
}

function RiskBadge({ risk }: { risk: string }) {
  const color = risk === "低" ? "bg-[#edf4eb] text-[#48705a]" : risk === "中" ? "bg-[#faf3e5] text-[#957043]" : "bg-[#f7ebe7] text-[#93584b]";
  return <span className={`rounded-full px-3 py-1 text-xs ${color}`}>{risk}风险</span>;
}

function FilterSelect({ value, options, onChange }: { value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="rounded-xl border border-[#e6e0d5] bg-white/80 px-3 py-2.5 text-sm text-[#52645d] outline-none"
    >
      {options.map((option) => <option key={option}>{option}</option>)}
    </select>
  );
}
