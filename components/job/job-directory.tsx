"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Bookmark,
  Building2,
  CalendarClock,
  ExternalLink,
  FileText,
  MapPin,
  Search,
  ShieldCheck,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type {
  EligiblePosition,
  JobTrackingData,
  JobTrackingStatus,
} from "@/lib/types";

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
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/job-tracking")
      .then((response) => response.json())
      .then((data: JobTrackingData) => setTracking(data))
      .catch(() => setTracking({ updatedAt: "", items: [] }));
  }, []);

  const regions = ["全部地区", ...new Set(positions.map((position) => position.region))];
  const categories = ["全部类型", ...new Set(positions.map((position) => position.category))];
  const sourcePositions = useMemo(() => {
    if (!showTrackedOnly) {
      return positions;
    }

    return tracking.items
      .filter((item) => item.status !== "未处理")
      .map((item) => positions.find((position) => position.id === item.positionId) ?? item.positionSnapshot)
      .filter((position): position is EligiblePosition => Boolean(position));
  }, [positions, showTrackedOnly, tracking.items]);

  const filtered = useMemo(() => sourcePositions.filter((position) => {
    const keyword = query.trim().toLowerCase();
    const searchable = [
      position.title,
      position.organization,
      position.department,
      position.positionCode,
      position.region,
      position.majorRequirement,
      position.responsibilities,
    ].join(" ").toLowerCase();
    const isOpen = position.status === "报名中" || position.status === "即将报名";

    return (
      (!keyword || searchable.includes(keyword)) &&
      (region === "全部地区" || position.region === region) &&
      (category === "全部类型" || position.category === category) &&
      (status === "全部状态" || (status === "可报名" ? isOpen : position.status === status))
    );
  }), [category, query, region, sourcePositions, status]);

  const selected = filtered.find((position) => position.id === selectedId) ?? filtered[0];

  async function saveTracking(position: EligiblePosition, nextStatus: JobTrackingStatus) {
    setSaving(position.id);
    const existing = tracking.items.filter((item) => item.positionId !== position.id);
    const next: JobTrackingData = {
      updatedAt: new Date().toISOString(),
      items: [
        ...existing,
        {
          positionId: position.id,
          status: nextStatus,
          examDate: position.examDate,
          positionSnapshot: position,
        },
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
      setSaving(null);
    }
  }

  function trackingStatusFor(positionId: string) {
    return tracking.items.find((item) => item.positionId === positionId)?.status ?? "未处理";
  }

  return (
    <>
      <Card className="no-print label-sans flex flex-wrap items-center gap-3 p-4">
        <label className="flex min-w-[250px] flex-1 items-center gap-2 rounded-lg border bg-white/70 px-3 py-2">
          <Search size={17} className="text-[#75817b]" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="w-full bg-transparent text-sm outline-none"
            placeholder="搜索单位、岗位代码、地区或专业"
          />
        </label>
        <FilterSelect value={region} options={regions} onChange={setRegion} />
        <FilterSelect value={category} options={categories} onChange={setCategory} />
        <FilterSelect
          value={status}
          options={["全部状态", "可报名", "报名中", "即将报名", "已截止", "已结束"]}
          onChange={setStatus}
        />
        <Button
          size="sm"
          variant={showTrackedOnly ? "default" : "outline"}
          onClick={() => setShowTrackedOnly((current) => !current)}
        >
          <Bookmark size={15} />
          我已跟踪
        </Button>
      </Card>
      <p className="label-sans text-sm text-[#6c7872]">
        共收录 {positions.length} 个已确认符合画像的岗位，当前显示 {filtered.length} 个；左侧浏览全部结果，右侧查看完整资料。
      </p>
      <div className="grid items-start gap-5 xl:grid-cols-[390px_minmax(0,1fr)]">
        <Card className="overflow-hidden p-0 xl:sticky xl:top-[96px]">
          <div className="border-b border-[#e7e3d9] px-5 py-4">
            <h2 className="section-title">符合岗位列表</h2>
            <p className="label-sans mt-2 text-xs text-[#6b7771]">全部岗位保留在列表中，状态如实展示</p>
          </div>
          <div className="max-h-[calc(100vh-235px)] space-y-2 overflow-y-auto p-3">
            {filtered.map((position) => (
              <button
                key={position.id}
                type="button"
                onClick={() => setSelectedId(position.id)}
                className={`label-sans w-full rounded-xl border p-4 text-left transition-colors ${
                  selected?.id === position.id
                    ? "border-[#98ad9d] bg-[#eef2ea]"
                    : "border-[#ebe7dd] bg-white/45 hover:bg-white/80"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <span className="text-sm font-semibold leading-6 text-[#263731]">
                    {position.department ?? position.organization}
                  </span>
                  <StatusBadge status={position.status} />
                </div>
                <p className="mt-2 text-sm text-[#455c52]">{position.title}</p>
                <p className="mt-2 text-xs text-[#64736c]">
                  {position.region} · {position.positionCode ?? "无岗位代码"} · 招 {position.recruitCount ?? "-"} 人
                </p>
                <p className="mt-2 text-xs font-medium text-[#527565]">
                  最低进面分：{position.historicalReferences?.[0]?.finalEntryScore ?? "官方未公开"}
                </p>
              </button>
            ))}
            {!filtered.length ? (
              <p className="px-3 py-10 text-center text-sm text-[#6c7872]">没有符合当前筛选条件的岗位。</p>
            ) : null}
          </div>
        </Card>
        <Card className="ornament-pavilion relative overflow-hidden p-6 lg:p-8">
          {selected ? (
            <JobDetail
              position={selected}
              saving={saving === selected.id}
              trackingStatus={trackingStatusFor(selected.id)}
              onTrackingChange={(nextStatus) => saveTracking(selected, nextStatus)}
            />
          ) : (
            <p className="muted-copy">请选择左侧岗位查看详细情况。</p>
          )}
        </Card>
      </div>
    </>
  );
}

function JobDetail({
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
  return (
    <article className="relative z-10 space-y-6">
      <header>
        <div className="flex flex-wrap items-center gap-2">
          <Badge>{position.category}</Badge>
          <StatusBadge status={position.status} />
          {position.recruitmentType ? <Badge className="bg-[#f4f1e9]">{position.recruitmentType}</Badge> : null}
        </div>
        <h2 className="ink-title mt-4 text-2xl leading-relaxed">
          {position.department ?? position.organization}
        </h2>
        <p className="mt-1 text-lg font-medium text-[#364d43]">{position.title}</p>
        <div className="label-sans mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-[#5d6d65]">
          <span className="flex items-center gap-2"><Building2 size={15} />{position.organization}</span>
          <span className="flex items-center gap-2"><MapPin size={15} />{position.region}{position.district ? ` · ${position.district}` : ""}</span>
          <span className="flex items-center gap-2"><Users size={15} />招录 {position.recruitCount ?? "未公开"} 人</span>
        </div>
      </header>

      <section className="label-sans grid gap-3 rounded-xl border border-[#e7e3d9] bg-white/55 p-4 sm:grid-cols-2 lg:grid-cols-3">
        <DetailFact label="岗位代码" value={position.positionCode ?? "官方未公开"} />
        <DetailFact label="学历学位" value={position.educationRequirement ?? "以公告为准"} />
        <DetailFact label="届别要求" value={position.freshGraduateRequirement ?? "以公告为准"} />
        <DetailFact label="公告日期" value={position.announcementDate ?? "官方附件未标注"} />
        <DetailFact label="报名截止" value={position.registrationEndDate ?? "已结束/以原公告为准"} />
        <DetailFact label="考试日期" value={position.examDate ?? "以原公告为准"} />
      </section>

      {position.responsibilities ? (
        <DetailBlock title="工作内容" text={position.responsibilities} icon={FileText} />
      ) : null}
      <DetailBlock title="报考专业要求" text={position.majorRequirement ?? "以公告为准"} icon={ShieldCheck} />

      <section>
        <h3 className="font-semibold tracking-[.08em] text-[#273731]">考试数据与薪资估算</h3>
        <div className="mt-3 space-y-3">
          {position.historicalReferences?.length ? position.historicalReferences.map((reference) => (
            <div className="label-sans rounded-xl border border-[#e7e3d9] bg-[#f7f6f1] p-4 text-sm text-[#65736c]" key={`${reference.year}-${reference.sourceUrl}`}>
              <p className="font-medium text-[#324c40]">{reference.year}</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-3">
                <p>最低进面/入围分：<strong className="text-[#344c41]">{reference.finalEntryScore ?? "官方未公开"}</strong></p>
                <p>报录比：<strong className="text-[#344c41]">{reference.applicationRatio ?? "官方未公开"}</strong></p>
                <p>招录人数：<strong className="text-[#344c41]">{reference.recruitmentCount ?? "官方未公开"}</strong></p>
              </div>
              {reference.note ? <p className="mt-3 leading-6">{reference.note}</p> : null}
              <a href={reference.sourceUrl} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-[#496b5b] hover:underline">
                {reference.sourceName}<ExternalLink size={13} />
              </a>
            </div>
          )) : (
            <p className="label-sans rounded-xl bg-[#f7f6f1] p-4 text-sm text-[#65736c]">
              暂未取得可对应到该岗位的官方历年数据。
            </p>
          )}
          <div className="label-sans rounded-xl border border-[#e7e3d9] bg-[#f7f6f1] p-4 text-sm leading-7 text-[#65736c]">
            <p className="font-medium text-[#324c40]">大概薪资范围</p>
            <p className="mt-2">{position.compensationReference?.text ?? "暂无足够依据推算该岗位薪资范围。"}</p>
            <p className="text-xs text-[#927c59]">
              {position.compensationReference?.disclaimer ?? "推算信息不等同于招录单位待遇承诺。"}
            </p>
          </div>
        </div>
      </section>

      {position.applicationNotes?.length ? <ItemBlock title="报考要点" items={position.applicationNotes} /> : null}

      <footer className="label-sans flex flex-wrap items-center justify-between gap-4 border-t border-[#e7e3d9] pt-5">
        <label className="flex items-center gap-3 text-sm text-[#65736c]">
          跟踪状态
          <select
            aria-label={`${position.title} 跟踪状态`}
            disabled={saving}
            value={trackingStatus}
            onChange={(event) => onTrackingChange(event.target.value as JobTrackingStatus)}
            className="rounded-lg border bg-white/75 px-3 py-2 text-sm outline-none"
          >
            {trackingStatuses.map((tracking) => <option key={tracking}>{tracking}</option>)}
          </select>
        </label>
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <span className="flex items-center gap-2 text-[#75817a]"><CalendarClock size={14} />采集于 {position.capturedAt}</span>
          <a href={position.sourceUrl} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-[#496b5b] hover:underline">
            查看官方原文 <ExternalLink size={14} />
          </a>
        </div>
      </footer>
    </article>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color =
    status === "报名中" || status === "即将报名"
      ? "border-[#9cb29e] bg-[#edf4eb] text-[#496953]"
      : status === "已结束" || status === "已截止"
        ? "border-[#ddd5c5] bg-[#f6f2ea] text-[#806d50]"
        : "";
  return <Badge className={`shrink-0 ${color}`}>{status}</Badge>;
}

function DetailFact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-[#75817a]">{label}</p>
      <p className="mt-1 leading-6 text-[#354b41]">{value}</p>
    </div>
  );
}

function DetailBlock({
  title,
  text,
  icon: Icon,
}: {
  title: string;
  text: string;
  icon: typeof FileText;
}) {
  return (
    <section>
      <h3 className="flex items-center gap-2 font-semibold tracking-[.08em] text-[#273731]">
        <Icon size={17} className="text-[#557565]" />
        {title}
      </h3>
      <p className="muted-copy mt-2 whitespace-pre-line text-sm leading-7">{text}</p>
    </section>
  );
}

function ItemBlock({
  title,
  items,
}: {
  title: string;
  items: string[];
}) {
  return (
    <section>
      <h3 className="font-semibold tracking-[.08em] text-[#273731]">{title}</h3>
      <ul className="label-sans mt-3 space-y-2 rounded-xl bg-[#f7f6f1] p-4 text-sm leading-7 text-[#63716a]">
        {items.map((item) => <li key={item}>- {item}</li>)}
      </ul>
    </section>
  );
}

function FilterSelect({
  value,
  options,
  onChange,
}: {
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="rounded-lg border bg-white/70 px-3 py-2 text-sm outline-none"
    >
      {options.map((option) => <option key={option}>{option}</option>)}
    </select>
  );
}
