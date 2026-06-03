"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import {
  Bookmark,
  MapPin,
  Search,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { EligiblePosition, JobTrackingData } from "@/lib/types";
const categoryOrder = ["国考", "省考", "编制", "国企"];
const regionOrder = ["北京", "雄安", "天津", "石家庄", "其他"];
const publicCategories = ["全部类型", ...categoryOrder];
type DisplayPosition = EligiblePosition & {
  category: string;
  recruitmentClass: string;
  regionGroup: string;
  district: string;
};
type CountItem = { name: string; count: number };
type CategoryRegionGroup = CountItem & { regions: CountItem[] };

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

function getDistrict(position: EligiblePosition) {
  if (position.district) return position.district;
  const text = `${position.region} ${position.department ?? ""} ${position.organization}`;
  const directMatch = text.match(/(?:北京市|天津市|石家庄市)([^省市县区（）()，,、\s]+[区县])/);
  if (directMatch?.[1]) return directMatch[1];
  if (text.includes("井陉矿区")) return "井陉矿区";
  if (text.includes("井陉县")) return "井陉县";
  if (text.includes("鹿泉")) return "鹿泉区";
  if (text.includes("藁城")) return "藁城区";
  if (text.includes("栾城")) return "栾城区";
  if (text.includes("正定")) return "正定县";
  if (text.includes("雄县")) return "雄县";
  if (text.includes("容城")) return "容城县";
  if (text.includes("安新")) return "安新县";
  if (position.regionGroup === "石家庄") return "市级待确认";
  if (position.regionGroup === "其他") return position.region.split(/[、/\s-]/).filter(Boolean).at(-1) ?? "其他地区";
  return "未细分";
}

function orderIndex(order: string[], value?: string) {
  const index = order.indexOf(value ?? "");
  return index === -1 ? order.length : index;
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

function anchorId(...parts: string[]) {
  return parts
    .join("-")
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function JobDirectory({ positions }: { positions: EligiblePosition[] }) {
  const activePositions = useMemo<DisplayPosition[]>(
    () =>
      positions
        .map((position) => {
          const recruitmentClass = getRecruitmentClass(position);
          return {
            ...position,
            category: displayCategory(position.category),
            recruitmentClass,
            regionGroup: getRegionGroup(position),
            district: getDistrict(position),
          };
        })
        .sort(
          (a, b) =>
            orderIndex(categoryOrder, a.recruitmentClass) - orderIndex(categoryOrder, b.recruitmentClass) ||
            orderIndex(regionOrder, a.regionGroup) - orderIndex(regionOrder, b.regionGroup) ||
            a.district.localeCompare(b.district, "zh-CN") ||
            (b.matchScore ?? 0) - (a.matchScore ?? 0) ||
            a.organization.localeCompare(b.organization, "zh-CN"),
        ),
    [positions],
  );
  const [query, setQuery] = useState("");
  const [region, setRegion] = useState("全部地区");
  const [district, setDistrict] = useState("全部县区");
  const [category, setCategory] = useState("全部类型");
  const [status, setStatus] = useState("全部状态");
  const [showTrackedOnly, setShowTrackedOnly] = useState(false);
  const [tracking, setTracking] = useState<JobTrackingData>({ updatedAt: "", items: [] });

  useEffect(() => {
    fetch("/api/job-tracking")
      .then((response) => response.json())
      .then((data: JobTrackingData) => setTracking(data))
      .catch(() => setTracking({ updatedAt: "", items: [] }));
  }, []);

  const regions = ["全部地区", ...regionOrder.filter((name) => activePositions.some((position) => position.regionGroup === name))];
  const districts = useMemo(
    () => [
      "全部县区",
      ...Array.from(
        new Set(
          activePositions
            .filter((position) => region === "全部地区" || position.regionGroup === region)
            .map((position) => position.district),
        ),
      ).sort((a, b) => a.localeCompare(b, "zh-CN")),
    ],
    [activePositions, region],
  );
  useEffect(() => {
    if (!districts.includes(district)) setDistrict("全部县区");
  }, [district, districts]);
  const statusOptions = useMemo(
    () => ["全部状态", ...Array.from(new Set(activePositions.map((position) => position.status)))],
    [activePositions],
  );
  const sourcePositions = useMemo(() => {
    if (!showTrackedOnly) return activePositions;
    return tracking.items
      .filter((item) => item.status !== "未处理")
      .map((item) => activePositions.find((position) => position.id === item.positionId))
      .filter((position): position is DisplayPosition => Boolean(position));
  }, [activePositions, showTrackedOnly, tracking.items]);
  const filtered = useMemo(
    () =>
      sourcePositions.filter((position) => {
        const keyword = query.trim().toLowerCase();
        const text = [
          position.title,
          position.organization,
          position.department,
          position.positionCode,
          position.region,
          position.responsibilities,
        ]
          .join(" ")
          .toLowerCase();
        return (
          (!keyword || text.includes(keyword)) &&
          (region === "全部地区" || position.regionGroup === region) &&
          (district === "全部县区" || position.district === district) &&
          (category === "全部类型" || position.recruitmentClass === category) &&
          (status === "全部状态" || position.status === status)
        );
      }),
    [category, district, query, region, sourcePositions, status],
  );
  const previewGroups = useMemo(
    () =>
      categoryOrder
        .map((groupCategory) => {
          const positionsInGroup = filtered.filter((position) => position.recruitmentClass === groupCategory);
          return {
            id: anchorId("job-preview", groupCategory),
            category: groupCategory,
            count: positionsInGroup.length,
            positions: positionsInGroup,
          };
        })
        .filter((group) => group.count > 0),
    [filtered],
  );
  const registeringCount = activePositions.filter((position) => position.status === "报名中").length;
  const upcomingCount = activePositions.filter((position) => position.status === "即将报名").length;
  const pendingExamCount = activePositions.filter((position) => position.status === "待考试").length;
  const endedCount = activePositions.filter((position) => ["已截止", "已结束", "已完成录用"].includes(position.status)).length;
  const locatorGroups = useMemo<CategoryRegionGroup[]>(
    () =>
      categoryOrder.map((name) => {
        const categoryPositions = sourcePositions.filter(
          (position) =>
            position.recruitmentClass === name &&
            (status === "全部状态" || position.status === status),
        );
        return {
          name,
          count: categoryPositions.length,
          regions: regionOrder.map((regionName) => ({
            name: regionName,
            count: categoryPositions.filter((position) => position.regionGroup === regionName).length,
          })),
        };
      }),
    [sourcePositions, status],
  );
  const locatorDistricts = useMemo(() => {
    const base = sourcePositions.filter(
      (position) =>
        (category === "全部类型" || position.recruitmentClass === category) &&
        (region === "全部地区" || position.regionGroup === region) &&
        (status === "全部状态" || position.status === status),
    );
    return Array.from(new Set(base.map((position) => position.district)))
      .sort((a, b) => a.localeCompare(b, "zh-CN"))
      .map((name) => ({
        name,
        count: base.filter((position) => position.district === name).length,
      }));
  }, [category, region, sourcePositions, status]);

  function handleRegionChange(nextRegion: string) {
    setRegion(nextRegion);
    setDistrict("全部县区");
  }

  function handleDistrictChange(nextDistrict: string) {
    setDistrict(nextDistrict);
  }

  function handleLocatorReset() {
    setCategory("全部类型");
    setRegion("全部地区");
    setDistrict("全部县区");
  }

  function handleCategorySelect(nextCategory: string) {
    setCategory(nextCategory);
    setRegion("全部地区");
    setDistrict("全部县区");
  }

  function handleCategoryRegionSelect(nextCategory: string, nextRegion: string) {
    setCategory(nextCategory);
    setRegion(nextRegion);
    setDistrict("全部县区");
  }

  return (
    <div className="space-y-4">
      <FilterBar
        query={query}
        onQueryChange={setQuery}
        category={category}
        onCategoryChange={setCategory}
        publicCategories={publicCategories}
        region={region}
        regionOptions={regions}
        onRegionChange={handleRegionChange}
        district={district}
        districtOptions={districts}
        onDistrictChange={handleDistrictChange}
        status={status}
        statusOptions={statusOptions}
        onStatusChange={setStatus}
        showTrackedOnly={showTrackedOnly}
        onToggleTracked={() => setShowTrackedOnly((current) => !current)}
        filteredCount={filtered.length}
      />

      <div className="grid gap-5 xl:grid-cols-[300px_minmax(0,1fr)]">
        <LocatorPanel
          activeCount={activePositions.length}
          filteredCount={filtered.length}
          registeringCount={registeringCount + upcomingCount}
          endedCount={endedCount}
          pendingExamCount={pendingExamCount}
          category={category}
          region={region}
          categoryRegionGroups={locatorGroups}
          onResetLocator={handleLocatorReset}
          onCategorySelect={handleCategorySelect}
          onCategoryRegionSelect={handleCategoryRegionSelect}
          district={district}
          districts={locatorDistricts}
          onDistrictChange={handleDistrictChange}
        />

        <section id="position-list" className="label-sans min-w-0 space-y-4 scroll-mt-24">
          {filtered.length ? (
            <div className="space-y-4">
              {previewGroups.map((group) => (
                <motion.section
                  id={group.id}
                  key={group.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                  className="scroll-mt-24 rounded-[22px] border border-[#e4ddcf] bg-[#fffdf8]/75 p-3"
                >
                  <div className="mb-3 flex items-center justify-between gap-3 px-1">
                    <h2 className="ink-title text-[24px]">{group.category}</h2>
                    <span className="rounded-full bg-[#edf4eb] px-3 py-1 text-xs text-[#4b6b5b]">{group.count} 个</span>
                  </div>
                  <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
                    {group.positions.map((position) => (
                      <PositionCard key={position.id} position={position} />
                    ))}
                  </div>
                </motion.section>
              ))}
            </div>
          ) : (
            <Card className="rounded-[28px] border-[#e3ddcf] bg-[#fffdf9] px-7 py-14 text-center">
              <h2 className="ink-title text-[28px] text-[#294a3b]">没有匹配当前筛选的岗位</h2>
              <p className="label-sans mx-auto mt-4 max-w-[610px] text-sm leading-7 text-[#67766e]">
                调整上方筛选或左侧定位器；也可以查看下方官方检索记录，确认排除原因。
              </p>
              <a href="#sources" className="label-sans mt-7 inline-flex rounded-xl border border-[#ccd9ce] bg-[#f1f5ee] px-5 py-3 text-sm font-medium text-[#345546]">
                查看官方检索记录
              </a>
            </Card>
          )}
        </section>
      </div>
    </div>
  );
}

function FilterBar({
  query,
  onQueryChange,
  category,
  onCategoryChange,
  publicCategories,
  region,
  regionOptions,
  onRegionChange,
  district,
  districtOptions,
  onDistrictChange,
  status,
  statusOptions,
  onStatusChange,
  showTrackedOnly,
  onToggleTracked,
  filteredCount,
}: {
  query: string;
  onQueryChange: (value: string) => void;
  category: string;
  onCategoryChange: (value: string) => void;
  publicCategories: string[];
  region: string;
  regionOptions: string[];
  onRegionChange: (value: string) => void;
  district: string;
  districtOptions: string[];
  onDistrictChange: (value: string) => void;
  status: string;
  statusOptions: string[];
  onStatusChange: (value: string) => void;
  showTrackedOnly: boolean;
  onToggleTracked: () => void;
  filteredCount: number;
}) {
  return (
    <Card id="positions" className="label-sans sticky top-20 z-20 scroll-mt-24 rounded-[22px] border-[#d8e0d6] bg-[#f8faf4]/95 p-3 shadow-[0_12px_32px_rgba(49,72,60,.06)]">
      <div className="flex flex-wrap items-center gap-2">
        <label className="flex min-w-[260px] flex-1 items-center gap-2 rounded-xl border border-[#e6e0d5] bg-white/80 px-3 py-2.5">
          <Search size={17} className="text-[#718178]" />
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            className="w-full bg-transparent text-sm outline-none"
            placeholder="搜岗位、单位、地区"
          />
        </label>
        <FilterSelect value={category} options={publicCategories} onChange={onCategoryChange} />
        <FilterSelect value={region} options={regionOptions} onChange={onRegionChange} />
        <FilterSelect value={district} options={districtOptions} onChange={onDistrictChange} />
        <FilterSelect value={status} options={statusOptions} onChange={onStatusChange} />
        <Button size="sm" variant={showTrackedOnly ? "default" : "outline"} onClick={onToggleTracked}>
          <Bookmark size={15} /> 我已关注
        </Button>
        <span className="rounded-full bg-[#e9f0e7] px-3 py-2 text-xs text-[#557064]">{filteredCount} 个</span>
      </div>
    </Card>
  );
}

function LocatorPanel({
  activeCount,
  filteredCount,
  registeringCount,
  endedCount,
  pendingExamCount,
  category,
  region,
  categoryRegionGroups,
  onResetLocator,
  onCategorySelect,
  onCategoryRegionSelect,
  district,
  districts,
  onDistrictChange,
}: {
  activeCount: number;
  filteredCount: number;
  registeringCount: number;
  endedCount: number;
  pendingExamCount: number;
  category: string;
  region: string;
  categoryRegionGroups: CategoryRegionGroup[];
  onResetLocator: () => void;
  onCategorySelect: (value: string) => void;
  onCategoryRegionSelect: (category: string, region: string) => void;
  district: string;
  districts: CountItem[];
  onDistrictChange: (value: string) => void;
}) {
  return (
    <aside className="label-sans xl:sticky xl:top-44 xl:self-start">
      <Card id="coverage" className="scroll-mt-24 rounded-[22px] border-[#d8e0d6] bg-[#f8faf4]/95 p-4 shadow-[0_12px_32px_rgba(49,72,60,.06)]">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm font-semibold text-[#304d40]">定位器</p>
          <a href="#sources" className="text-xs text-[#61746b] hover:underline">官方记录</a>
        </div>
        <div className="mt-4 grid grid-cols-2 gap-2 text-center text-xs">
          <LocatorStat label="匹配" value={`${activeCount}`} />
          <LocatorStat label="显示" value={`${filteredCount}`} />
          <LocatorStat label="可报名" value={`${registeringCount}`} />
          <LocatorStat label="待考" value={`${pendingExamCount}`} />
          <LocatorStat label="结束" value={`${endedCount}`} />
        </div>
        <CategoryRegionNavigator
          currentCategory={category}
          currentRegion={region}
          groups={categoryRegionGroups}
          onReset={onResetLocator}
          onCategorySelect={onCategorySelect}
          onCategoryRegionSelect={onCategoryRegionSelect}
        />
        <LocatorSection
          label="县区细分"
          current={district}
          allLabel="全部县区"
          items={districts}
          onChange={onDistrictChange}
        />
      </Card>
    </aside>
  );
}

function CategoryRegionNavigator({
  currentCategory,
  currentRegion,
  groups,
  onReset,
  onCategorySelect,
  onCategoryRegionSelect,
}: {
  currentCategory: string;
  currentRegion: string;
  groups: CategoryRegionGroup[];
  onReset: () => void;
  onCategorySelect: (value: string) => void;
  onCategoryRegionSelect: (category: string, region: string) => void;
}) {
  const allCount = groups.reduce((sum, group) => sum + group.count, 0);

  return (
    <div className="mt-4">
      <div className="mb-2 flex items-center justify-between gap-3">
        <p className="text-xs font-semibold text-[#6b7d73]">类型 / 地区</p>
        <span className="text-[11px] text-[#87938c]">先选类型，再点地区</span>
      </div>
      <button
        type="button"
        onClick={onReset}
        className={`flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left text-xs transition-colors ${
          currentCategory === "全部类型" && currentRegion === "全部地区"
            ? "border-[#8da995] bg-[#edf4eb] text-[#315545]"
            : "border-[#dfe7dc] bg-white/70 text-[#596f64] hover:border-[#b9c9b7] hover:bg-[#f1f5ee]"
        }`}
      >
        <span className="font-medium">全部岗位</span>
        <span className="text-[#7c8b82]">{allCount}</span>
      </button>
      <div className="mt-2 space-y-2">
        {groups.map((group) => {
          const categoryActive = currentCategory === group.name;
          return (
            <div
              key={group.name}
              className={`rounded-xl border p-2 ${
                categoryActive ? "border-[#c6d5c4] bg-[#f3f7ef]" : "border-[#e1e8de] bg-white/55"
              }`}
            >
              <button
                type="button"
                disabled={group.count === 0 && !categoryActive}
                onClick={() => onCategorySelect(group.name)}
                className={`flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-45 ${
                  categoryActive && currentRegion === "全部地区"
                    ? "bg-[#dfeadc] text-[#2f4f40]"
                    : "text-[#365447] hover:bg-[#edf4eb]"
                }`}
              >
                <span className="font-semibold">{group.name}</span>
                <span className="text-xs text-[#7c8b82]">{group.count} 个</span>
              </button>
              <div className="mt-1.5 grid grid-cols-2 gap-1.5">
                {group.regions.map((item) => {
                  const active = categoryActive && currentRegion === item.name;
                  return (
                    <button
                      type="button"
                      key={`${group.name}-${item.name}`}
                      disabled={item.count === 0 && !active}
                      onClick={() => onCategoryRegionSelect(group.name, item.name)}
                      className={`flex min-w-0 items-center justify-between gap-1 rounded-lg border px-2 py-1.5 text-left text-[11px] transition-colors disabled:cursor-not-allowed disabled:opacity-35 ${
                        active
                          ? "border-[#8da995] bg-[#edf4eb] text-[#315545]"
                          : "border-[#e2e8de] bg-white/70 text-[#65766d] hover:border-[#b9c9b7] hover:bg-[#f7faf4]"
                      }`}
                    >
                      <span className="min-w-0 truncate">{item.name}</span>
                      <span className="shrink-0 text-[#7c8b82]">{item.count}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LocatorSection({
  label,
  current,
  allLabel,
  items,
  onChange,
}: {
  label: string;
  current: string;
  allLabel: string;
  items: CountItem[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-semibold text-[#6b7d73]">{label}</p>
      <div className="space-y-1">
        <LocatorButton label={allLabel} count={items.reduce((sum, item) => sum + item.count, 0)} active={current === allLabel} onClick={() => onChange(allLabel)} />
        {items.map((item) => (
          <LocatorButton
            key={item.name}
            label={item.name}
            count={item.count}
            active={current === item.name}
            disabled={item.count === 0 && current !== item.name}
            onClick={() => onChange(item.name)}
          />
        ))}
      </div>
    </div>
  );
}

function LocatorButton({
  label,
  count,
  active,
  disabled = false,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`flex w-full items-center justify-between rounded-lg border px-2.5 py-1.5 text-left text-xs transition-colors ${
        active
          ? "border-[#8da995] bg-[#edf4eb] text-[#315545]"
          : "border-[#dfe7dc] bg-white/70 text-[#596f64] hover:border-[#b9c9b7] hover:bg-[#f1f5ee] disabled:cursor-not-allowed disabled:opacity-40"
      }`}
    >
      <span className="min-w-0 truncate">{label}</span>
      <span className="text-[#7c8b82]">{count}</span>
    </button>
  );
}

function LocatorStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[#e1e8de] bg-white/65 px-2 py-2">
      <p className="text-[#718178]">{label}</p>
      <p className="mt-1 font-semibold text-[#315545]">{value}</p>
    </div>
  );
}

function PositionCard({ position }: { position: EligiblePosition }) {
  const risk = position.riskLevel ?? "中";
  return (
    <motion.div
      layout
      whileHover={{ y: -4 }}
      className="h-full"
    >
      <Link
        href={`/job/${encodeURIComponent(position.id)}`}
        className="label-sans flex h-full flex-col rounded-[18px] border border-[#e5ded2] bg-[#fffdf9] p-4 text-left transition-all hover:border-[#bfccbe] hover:bg-[#f8fbf5] hover:shadow-[0_10px_28px_rgba(49,72,60,.08)]"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            <Badge className="border-[#d8c69f] bg-[#faf4e6] text-[#80663b]">{getRegionGroup(position)}</Badge>
            <Badge className="border-[#d9e2d6] bg-[#f5f8f2] text-[#60766a]">{getDistrict(position)}</Badge>
          </div>
          <RiskBadge risk={risk} />
        </div>
        <h3 className="mt-3 line-clamp-2 text-sm font-semibold leading-6 text-[#293d34]">{position.organization}</h3>
        <p className="mt-1 line-clamp-1 text-sm text-[#52675d]">{position.title}</p>
        <p className="mt-2 flex items-center gap-1.5 text-xs text-[#6a776f]"><MapPin size={13} />{position.region}</p>
        <div className="mt-3 grid grid-cols-3 gap-1.5 rounded-xl bg-[#f5f4ee] p-2.5 text-center">
          <CardMetric label="匹配度" value={`${position.matchScore ?? 80}`} />
          <CardMetric label="招录" value={`${position.recruitCount ?? "-"}人`} />
          <CardMetric label="风险" value={`${risk}风险`} />
        </div>
        <div className="mt-2 grid grid-cols-2 gap-1.5 rounded-xl border border-[#ebe5d9] bg-white/55 p-2.5 text-center">
          <CardMetric label="报名截止" value={formatTimePoint(position.registrationEndAt ?? position.registrationEndDate)} />
          <CardMetric label="笔试时间" value={formatTimePoint(position.examDate)} />
        </div>
        <div className="mt-auto flex items-center justify-between border-t border-[#eee7da] pt-3 text-xs">
          <StatusBadge status={position.status} />
          <span className="font-medium text-[#496b5b]">查看详情</span>
        </div>
      </Link>
    </motion.div>
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
  return <Badge className="border-[#9cb29e] bg-[#edf4eb] text-[#496953]">{status}</Badge>;
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
