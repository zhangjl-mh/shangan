"use client";

import Link from "next/link";
import {
  AlertTriangle,
  ArrowUpRight,
  Dumbbell,
  GraduationCap,
  Layers3,
  Route,
  Target,
} from "lucide-react";
import type { XingceRoadmap } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type ModuleGuide = NonNullable<XingceRoadmap["moduleGuides"]>[number];
type TeacherGroup = NonNullable<XingceRoadmap["teacherGroups"]>[number];
type Teacher = TeacherGroup["teachers"][number];
type FormulaCard = NonNullable<XingceRoadmap["formulaCards"]>[number];
type PracticeChecklist = NonNullable<XingceRoadmap["practiceChecklist"]>[number];
type TeacherTier = "primary" | "alternative" | "supplement";

const moduleToolKeywords: Record<string, string[]> = {
  data: ["资料", "基础夯实", "强化刷题"],
  reasoning: ["判断", "基础夯实", "强化刷题"],
  verbal: ["言语", "基础夯实", "强化刷题"],
  common: ["常识", "模拟与冲刺"],
  quantity: ["数量", "强化刷题", "模拟与冲刺"],
  politics: ["常识", "模拟与冲刺"],
};

export function XingceModuleExplorer({
  modules,
  teacherGroups = [],
  formulaCards = [],
  practiceChecklist = [],
  activeModuleId,
}: {
  modules: ModuleGuide[];
  teacherGroups?: TeacherGroup[];
  formulaCards?: FormulaCard[];
  practiceChecklist?: PracticeChecklist[];
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

  const relatedTools = getRelatedTools(active.id, formulaCards, practiceChecklist);
  const teachers = activeTeacherGroup?.teachers ?? [];
  const primaryTeachers = teachers.filter((teacher, index) => getTeacherTier(teacher, index) === "primary");
  const alternativeTeachers = teachers.filter((teacher, index) => getTeacherTier(teacher, index) === "alternative");
  const supplementTeachers = teachers.filter((teacher, index) => getTeacherTier(teacher, index) === "supplement");
  const learningWindow = primaryTeachers[0]?.stage ?? active.methods[0];
  const moduleStandard = getModuleStandard(active);

  return (
    <Card id="module-workbench" className="scroll-mt-36 overflow-hidden p-0">
      <div className="label-sans flex overflow-x-auto border-b bg-[#fcfaf5] p-3">
        {modules.map((module) => (
          <Link
            href={`/xingce?module=${encodeURIComponent(module.id)}#modules`}
            key={module.id}
            className={cn(
              "shrink-0 rounded-lg px-5 py-3 text-sm transition-colors",
              module.id === activeId ? "bg-[#698878] text-white" : "text-[#53625a] hover:bg-[#eef1eb]",
            )}
          >
            {module.title}
          </Link>
        ))}
      </div>

      <div className="border-b p-6">
        <div className="grid gap-6 lg:grid-cols-[.76fr_1.24fr]">
          <div>
            <Badge className="bg-[#eef2ea]">当前模块</Badge>
            <h3 className="ink-title mt-4 text-2xl">{active.title}</h3>
            <div className="label-sans mt-4 space-y-3">
              <div className="rounded-lg bg-[#f7f5ef] p-4">
                <p className="text-xs font-medium tracking-[.12em] text-[#789083]">为什么学</p>
                <p className="mt-2 text-sm leading-7 text-[#65736c]">{active.ability}</p>
              </div>
              <div className="rounded-lg bg-[#eef3ee] p-4">
                <p className="text-xs font-medium tracking-[.12em] text-[#688273]">何时学</p>
                <p className="mt-2 text-sm leading-6 text-[#587064]">{learningWindow}</p>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              {active.topics.map((topic) => <Badge key={topic}>{topic}</Badge>)}
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Panel icon={Route} title="课程使用顺序" items={active.methods} />
            <Panel icon={Dumbbell} title="课后刷题动作" items={active.drills} />
            <Panel icon={AlertTriangle} title="常见误区" items={active.pitfalls} />
            <div className="label-sans rounded-xl border bg-[#f4f0e8] p-4">
              <p className="mb-3 flex items-center gap-2 font-medium text-[#69563a]">
                <Target size={17} />
                达标标准
              </p>
              <p className="text-sm leading-6 text-[#75634b]">
                {moduleStandard}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="p-6">
        <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 text-xl font-semibold text-deep-green">
              <GraduationCap size={20} className="text-[#648371]" />
              {active.title}老师与课程
            </h3>
            <p className="muted-copy mt-2 text-sm leading-6">
              {activeTeacherGroup?.selectionNote ?? "本模块暂无固定老师组，按课程目标和试听结果选择一套主线方法。"}
            </p>
          </div>
          <Badge className="bg-[#f4f0e8] text-[#6e5d42]">主线课程只能选一套</Badge>
        </div>

        {teachers.length ? (
          <div className="space-y-6">
            <TeacherSection title="主线老师" description="用于完整建立方法体系，优先从这里选择一位。" teachers={primaryTeachers} tier="primary" />
            {alternativeTeachers.length ? (
              <TeacherSection title="备选老师" description="讲义或授课风格不适配时，用作主线替代，不与主线叠加。" teachers={alternativeTeachers} tier="alternative" />
            ) : null}
            {supplementTeachers.length ? (
              <TeacherSection title="专项补充与冲刺" description="只在明确短板或进入冲刺阶段后使用。" teachers={supplementTeachers} tier="supplement" />
            ) : null}
          </div>
        ) : (
          <div className="label-sans rounded-xl border border-dashed bg-[#fdfbf7] p-6 text-sm leading-6 text-[#68766e]">
            暂无老师资料。先按上方课程顺序完成模块训练，后续补充公开课程时仍遵守“一套主线”的原则。
          </div>
        )}

        {relatedTools.length ? (
          <div className="mt-7 border-t pt-6">
            <h4 className="mb-4 flex items-center gap-2 font-semibold text-[#33473e]">
              <Layers3 size={18} className="text-[#648371]" />
              本模块配套工具
            </h4>
            <div className="label-sans grid gap-4 md:grid-cols-2">
              {relatedTools.map((tool) => (
                <div className="rounded-xl border bg-[#fdfbf7] p-4" key={tool.title}>
                  <p className="font-medium text-[#405c4d]">{tool.title}</p>
                  <ul className="mt-3 space-y-2 text-sm leading-6 text-[#68766e]">
                    {tool.items.map((item) => <li key={item}>• {item}</li>)}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}

function TeacherSection({
  title,
  description,
  teachers,
  tier,
}: {
  title: string;
  description: string;
  teachers: Teacher[];
  tier: TeacherTier;
}) {
  if (!teachers.length) {
    return null;
  }

  return (
    <section>
      <div className="mb-3">
        <h4 className="font-semibold text-[#33473e]">{title}</h4>
        <p className="label-sans mt-1 text-xs text-[#78857e]">{description}</p>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {teachers.map((teacher) => (
          <TeacherCard teacher={teacher} tier={tier} key={`${teacher.name}-${teacher.role}`} />
        ))}
      </div>
    </section>
  );
}

function TeacherCard({ teacher, tier }: { teacher: Teacher; tier: TeacherTier }) {
  const tierStyle = {
    primary: {
      label: "主线",
      card: "border-[#aebfaf] bg-[#f7faf6]",
      badge: "bg-[#e2ece4] text-[#486958]",
    },
    alternative: {
      label: "备选",
      card: "bg-[#fdfbf7]",
      badge: "bg-[#e8eef6] text-[#557bb0]",
    },
    supplement: {
      label: "补充",
      card: "bg-[#fdfbf7]",
      badge: "bg-[#f3ece1] text-[#8b6a3e]",
    },
  }[tier];

  return (
    <div className={cn("label-sans rounded-xl border p-5", tierStyle.card)}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-lg font-semibold text-deep-green">{teacher.name}</p>
            <Badge className={tierStyle.badge}>{tierStyle.label}</Badge>
          </div>
          {teacher.institution ? <p className="mt-1 text-xs text-[#718078]">{teacher.institution}</p> : null}
        </div>
        <Badge className="bg-[#f4f0e8] text-[#6e5d42]">{teacher.role}</Badge>
      </div>
      <p className="mt-4 text-xs leading-5 text-[#718078]">适用阶段：{teacher.stage}</p>
      <p className="mt-3 text-sm leading-6 text-[#65736c]">适合：{teacher.suitedFor}</p>
      <div className="mt-4">
        <p className="mb-2 text-sm font-medium text-[#33473e]">怎么跟</p>
        <ul className="space-y-2 text-sm leading-6 text-[#65736c]">
          {teacher.howToUse.map((item) => <li key={item}>• {item}</li>)}
        </ul>
      </div>
      <p className="mt-4 rounded-lg bg-[#f6f3eb] p-3 text-xs leading-5 text-[#796748]">
        注意：{teacher.caution}
      </p>
      {teacher.sourceUrl ? (
        <a
          className="mt-3 inline-flex items-center gap-1 text-xs text-[#6c7d74] underline-offset-4 hover:underline"
          href={teacher.sourceUrl}
          target="_blank"
          rel="noreferrer"
        >
          公开来源：{teacher.sourceTitle ?? teacher.name} <ArrowUpRight size={12} />
        </a>
      ) : null}
    </div>
  );
}

function Panel({
  icon: Icon,
  title,
  items,
}: {
  icon: typeof Route;
  title: string;
  items: string[];
}) {
  return (
    <div className="label-sans rounded-xl border bg-[#fdfbf7] p-4">
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

function getTeacherTier(teacher: Teacher, index: number): TeacherTier {
  if (index === 0 || teacher.role.includes("主线")) {
    return "primary";
  }

  if (
    teacher.role.includes("冲刺")
    || teacher.role.includes("补充")
    || teacher.role.includes("提速")
    || teacher.role.includes("套卷")
  ) {
    return "supplement";
  }

  return "alternative";
}

function getRelatedTools(
  moduleId: string,
  formulaCards: FormulaCard[],
  practiceChecklist: PracticeChecklist[],
) {
  const keywords = moduleToolKeywords[moduleId] ?? [];
  const tools: Array<{ title: string; items: string[] }> = [];

  formulaCards.forEach((card) => {
    if (keywords.some((keyword) => card.title.includes(keyword) || card.rules.some((rule) => rule.includes(keyword)))) {
      tools.push({ title: card.title, items: card.rules });
    }
  });

  practiceChecklist.forEach((checklist) => {
    const matchingItems = checklist.items.filter((item) => keywords.some((keyword) => item.includes(keyword)));
    if (matchingItems.length) {
      tools.push({ title: checklist.title, items: matchingItems });
    }
  });

  return tools.slice(0, 4);
}

function getModuleStandard(module: ModuleGuide) {
  const measurableDrill = module.drills.find((drill) => drill.includes("正确率"))
    ?? module.drills.find((drill) => drill.includes("分钟"))
    ?? module.drills[module.drills.length - 1];

  return `${measurableDrill} 同时能复述固定解题步骤，并说明主要错因和取舍标准。`;
}
