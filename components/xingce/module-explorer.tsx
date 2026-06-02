"use client";

import Link from "next/link";
import { AlertTriangle, Dumbbell, GraduationCap, Layers3, Route } from "lucide-react";
import type { XingceRoadmap } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type ModuleGuide = NonNullable<XingceRoadmap["moduleGuides"]>[number];
type TeacherGroup = NonNullable<XingceRoadmap["teacherGroups"]>[number];

export function XingceModuleExplorer({
  modules,
  teacherGroups = [],
  selectionRules = [],
  activeModuleId,
}: {
  modules: ModuleGuide[];
  teacherGroups?: TeacherGroup[];
  selectionRules?: string[];
  activeModuleId?: string;
}) {
  const activeId = modules.some((module) => module.id === activeModuleId)
    ? activeModuleId
    : modules[0]?.id;
  const active = modules.find((module) => module.id === activeId) ?? modules[0];
  const activeTeacherGroup = teacherGroups.find((group) => group.moduleId === active?.id);

  if (!active) {
    return null;
  }

  return (
    <Card id="module-workbench" className="scroll-mt-6 overflow-hidden p-0">
      <div className="label-sans flex overflow-x-auto border-b bg-[#fcfaf5] p-3">
        {modules.map((module) => (
          <Link
            href={`/xingce?module=${encodeURIComponent(module.id)}#module-workbench`}
            key={module.id}
            className={cn(
              "shrink-0 rounded-lg px-5 py-3 text-sm",
              module.id === activeId ? "bg-[#698878] text-white" : "text-[#53625a] hover:bg-[#eef1eb]",
            )}
          >
            {module.title}
          </Link>
        ))}
      </div>
      <div className="grid gap-6 p-6 lg:grid-cols-[.78fr_1.22fr]">
        <div>
          <h3 className="ink-title text-2xl">{active.title}</h3>
          <p className="muted-copy mt-3 text-sm leading-7">{active.ability}</p>
          <div className="mt-5 flex flex-wrap gap-2">
            {active.topics.map((topic) => <Badge key={topic}>{topic}</Badge>)}
          </div>
          <Panel className="mt-6" icon={AlertTriangle} title="高频失误" items={active.pitfalls} />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <Panel icon={Route} title="解题方法" items={active.methods} />
          <Panel icon={Dumbbell} title="训练动作" items={active.drills} />
          {activeTeacherGroup ? (
            <TeacherPanel group={activeTeacherGroup} selectionRules={selectionRules} />
          ) : null}
          <div className="sm:col-span-2 rounded-xl bg-[#f4f0e8] p-4">
            <p className="label-sans flex items-center gap-2 text-sm font-medium text-[#69563a]">
              <Layers3 size={16} />
              模块训练原则
            </p>
            <p className="label-sans mt-2 text-sm leading-6 text-[#75634b]">
              先识别题型和解题路径，再追求速度；限时训练必须同步记录错误原因和耗时。
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}

function TeacherPanel({
  group,
  selectionRules,
}: {
  group: TeacherGroup;
  selectionRules: string[];
}) {
  return (
    <div className="label-sans rounded-xl border bg-[#fdfbf7] p-4 sm:col-span-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="flex items-center gap-2 font-medium text-[#33473e]">
          <GraduationCap size={17} className="text-[#648371]" />
          跟课老师组
        </p>
        <Badge>{group.teachers.length} 个选择</Badge>
      </div>
      <p className="mt-3 text-sm leading-6 text-[#65736c]">{group.selectionNote}</p>
      <div className="mt-4 grid gap-3 lg:grid-cols-2">
        {group.teachers.map((teacher) => (
          <div className="rounded-lg border bg-white/70 p-4" key={`${group.moduleId}-${teacher.name}`}>
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="text-lg font-semibold text-deep-green">{teacher.name}</p>
                {teacher.institution ? (
                  <p className="mt-1 text-xs text-[#718078]">{teacher.institution}</p>
                ) : null}
              </div>
              <Badge className="bg-[#f4f0e8] text-[#6e5d42]">{teacher.role}</Badge>
            </div>
            <p className="mt-3 text-xs leading-5 text-[#718078]">阶段：{teacher.stage}</p>
            <p className="mt-3 text-sm leading-6 text-[#65736c]">适合：{teacher.suitedFor}</p>
            <div className="mt-3">
              <p className="mb-2 text-sm font-medium text-[#33473e]">怎么跟</p>
              <ul className="space-y-2 text-sm leading-6 text-[#65736c]">
                {teacher.howToUse.map((item) => <li key={item}>• {item}</li>)}
              </ul>
            </div>
            <p className="mt-3 rounded-lg bg-[#f6f3eb] p-3 text-xs leading-5 text-[#796748]">
              注意：{teacher.caution}
            </p>
            {teacher.sourceUrl ? (
              <a
                className="mt-3 inline-flex text-xs text-[#4c705e] underline-offset-4 hover:underline"
                href={teacher.sourceUrl}
                target="_blank"
                rel="noreferrer"
              >
                来源：{teacher.sourceTitle ?? teacher.name}
              </a>
            ) : null}
          </div>
        ))}
      </div>
      {selectionRules.length ? (
        <div className="mt-4 border-t pt-3">
          <p className="mb-2 text-sm font-medium text-[#33473e]">选老师原则</p>
          <div className="grid gap-2 lg:grid-cols-2">
            {selectionRules.map((rule) => (
              <p className="rounded-lg bg-[#f6f3eb] p-3 text-xs leading-5 text-[#718078]" key={rule}>
                □ {rule}
              </p>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Panel({
  icon: Icon,
  title,
  items,
  className,
}: {
  icon: typeof Route;
  title: string;
  items: string[];
  className?: string;
}) {
  return (
    <div className={cn("label-sans rounded-xl border bg-[#fdfbf7] p-4", className)}>
      <p className="mb-3 flex items-center gap-2 font-medium text-[#33473e]">
        <Icon size={17} className="text-[#648371]" />
        {title}
      </p>
      <ul className="space-y-3 text-sm leading-6 text-[#65736c]">
        {items.map((item) => <li key={item}>• {item}</li>)}
      </ul>
    </div>
  );
}
