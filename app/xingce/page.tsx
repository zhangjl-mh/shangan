import Link from "next/link";
import {
  ArrowUpRight,
  BookOpenCheck,
  BrainCircuit,
  CalendarRange,
  ChartNoAxesColumn,
  Clock3,
  Languages,
  Scale,
  Shapes,
  Sigma,
  Target,
} from "lucide-react";
import { PrintButton } from "@/components/export/print-button";
import { PipelineStrip } from "@/components/layout/pipeline-strip";
import { XingceModuleExplorer } from "@/components/xingce/module-explorer";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Reveal } from "@/components/ui/reveal";
import { readRoadmap } from "@/lib/content";
import type { XingceRoadmap } from "@/lib/types";

export const dynamic = "force-dynamic";

const moduleIcons = [Scale, BrainCircuit, Languages, Sigma, Shapes, ChartNoAxesColumn];
const moduleTones = [
  "bg-[#789485]",
  "bg-[#839f89]",
  "bg-[#5785bd]",
  "bg-[#cda362]",
  "bg-[#698571]",
  "bg-[#718bb5]",
];

export default async function XingcePage() {
  const roadmap = await readRoadmap<XingceRoadmap>("xingce");

  if (!roadmap) {
    return null;
  }

  const profile = roadmap.examProfile;

  return (
    <main className="mx-auto max-w-[1310px] space-y-7 px-5 py-9 lg:px-6">
      <Reveal className="grid gap-6 lg:grid-cols-[1fr_460px]">
        <div>
          <Badge className="mb-4 border-[#b5c4b7] bg-[#eff3ee] text-[#486958]">
            系统训练中心 · {roadmap.meta?.version}
          </Badge>
          <h1 className="ink-title text-[38px] lg:text-[44px]">{roadmap.title}</h1>
          <p className="mt-4 text-lg leading-8 text-[#56665e]">{roadmap.description}</p>
          <div className="no-print mt-6 flex gap-3">
            <Button asChild variant="outline" size="sm">
              <Link href="/api/export/xingce">导出 Markdown</Link>
            </Button>
            <PrintButton />
          </div>
        </div>
        {profile ? (
          <Card className="p-6">
            <p className="label-sans text-xs tracking-[.16em] text-[#6d8174]">官方大纲口径</p>
            <h2 className="mt-3 text-lg font-semibold leading-7">{profile.questionNature} · 行政职业能力测验</h2>
            <div className="label-sans mt-5 grid grid-cols-3 gap-3">
              <Stat value={`${profile.durationMinutes}`} label="分钟" />
              <Stat value={`${profile.score}`} label="满分" />
              <Stat value={`${profile.officialModules.length}`} label="板块" />
            </div>
            <a className="label-sans mt-4 inline-flex items-center gap-1 text-sm text-[#4c705e]" href={profile.syllabusUrl} target="_blank" rel="noreferrer">
              查看大纲原文 <ArrowUpRight size={14} />
            </a>
          </Card>
        ) : null}
      </Reveal>

      {profile ? (
        <Reveal delay={0.04}>
          <Card className="border-[#d7e0d8] bg-[#f5f7f1] p-5">
            <p className="label-sans text-sm leading-7 text-[#52655b]">{roadmap.basisNote}</p>
            <p className="label-sans mt-2 text-xs text-[#718078]">{profile.notice}</p>
          </Card>
        </Reveal>
      ) : null}

      {roadmap.moduleGuides?.length ? (
        <Reveal delay={0.05}>
          <section>
            <Heading icon={BookOpenCheck} title="官方板块与专项方法" description="六大模块均提供能力目标、题型主题、方法、避坑和训练动作。" />
            <div className="mb-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
              {roadmap.moduleGuides.map((module, index) => {
                const Icon = moduleIcons[index] ?? Target;
                return (
                  <Card className="flex flex-col items-center gap-3 p-4 text-center" key={module.id}>
                    <span className={`flex size-11 items-center justify-center rounded-xl text-white ${moduleTones[index]}`}>
                      <Icon size={22} />
                    </span>
                    <p className="font-semibold tracking-[.06em]">{module.title}</p>
                  </Card>
                );
              })}
            </div>
            <XingceModuleExplorer modules={roadmap.moduleGuides} />
          </section>
        </Reveal>
      ) : null}

      <Reveal delay={0.05}>
        <section>
          <Heading icon={CalendarRange} title="六阶段训练路线" description="从摸底识别短板，到专项强化与整卷稳定输出。" />
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {roadmap.stages.map((stage) => (
              <Card className="hover-lift p-5" key={stage.id}>
                <div className="mb-3 flex items-center justify-between gap-2">
                  <p className="text-lg font-semibold">{stage.title}</p>
                  <Badge>{stage.duration}</Badge>
                </div>
                <p className="muted-copy text-sm leading-6">{stage.goal}</p>
                <ul className="label-sans mt-4 space-y-2 text-sm leading-6 text-[#62716a]">
                  {stage.tasks.map((task) => <li key={task}>• {task}</li>)}
                </ul>
                {stage.milestone ? (
                  <p className="label-sans mt-4 rounded-lg bg-[#f6f3eb] p-3 text-xs leading-6 text-[#796748]">
                    验收标志：{stage.milestone}
                  </p>
                ) : null}
              </Card>
            ))}
          </div>
        </section>
      </Reveal>

      <Reveal delay={0.05}>
        <section className="grid gap-5 lg:grid-cols-[1.06fr_.94fr]">
          <div>
            <Heading icon={Sigma} title="速算与关系卡" description="用于资料分析和数量关系的基础关系复习。" />
            <div className="grid gap-4 sm:grid-cols-2">
              {roadmap.formulaCards?.map((card) => (
                <Card className="p-5" key={card.title}>
                  <p className="mb-3 text-lg font-semibold text-deep-green">{card.title}</p>
                  <ul className="label-sans space-y-2 text-sm leading-6 text-[#65736c]">
                    {card.rules.map((rule) => <li key={rule}>• {rule}</li>)}
                  </ul>
                </Card>
              ))}
            </div>
          </div>
          <div>
            <Heading icon={Clock3} title="考场节奏" description="实际分配须通过套卷训练确定并固定。" />
            <Card className="p-5">
              <div className="label-sans space-y-4">
                {roadmap.timePlan?.map((phase) => (
                  <div className="rounded-lg border bg-[#fdfbf7] p-4" key={phase.phase}>
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium text-[#32463d]">{phase.phase}</p>
                      <Badge>{phase.target}</Badge>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-[#68766e]">{phase.method}</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </section>
      </Reveal>

      {roadmap.practiceChecklist?.length ? (
        <Reveal delay={0.05}>
          <section>
            <Heading icon={Target} title="训练检查表" description="用固定记录方式把刷题转化为可验证的提升。" />
            <div className="grid gap-4 md:grid-cols-3">
              {roadmap.practiceChecklist.map((checklist) => (
                <Card className="p-5" key={checklist.title}>
                  <h3 className="mb-4 text-lg font-semibold text-deep-green">{checklist.title}</h3>
                  <ul className="label-sans space-y-3 text-sm leading-6 text-[#65736c]">
                    {checklist.items.map((item) => <li key={item}>□ {item}</li>)}
                  </ul>
                </Card>
              ))}
            </div>
          </section>
        </Reveal>
      ) : null}

      <PipelineStrip />
    </main>
  );
}

function Heading({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof Target;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-5">
      <h2 className="section-title flex items-center gap-3 text-[21px]">
        <Icon size={21} className="text-[#658371]" />
        {title}
      </h2>
      <p className="muted-copy mt-2 pl-[53px] text-sm">{description}</p>
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <div className="label-sans rounded-lg border bg-[#faf8f2] px-3 py-3 text-center">
      <p className="text-2xl font-semibold text-deep-green">{value}</p>
      <p className="mt-1 text-xs text-[#69766f]">{label}</p>
    </div>
  );
}
