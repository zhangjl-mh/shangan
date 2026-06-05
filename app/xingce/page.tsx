import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  BookMarked,
  BookOpenCheck,
  CalendarRange,
  CheckCheck,
  Clock3,
  Compass,
  GraduationCap,
  Route,
  ShieldCheck,
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

type XingcePageProps = {
  searchParams?: Promise<{
    module?: string | string[];
  }>;
};

const sectionNav = [
  { label: "学习顺序", href: "#roadmap" },
  { label: "模块选课", href: "#modules" },
  { label: "老师选择", href: "#teachers" },
  { label: "每日安排", href: "#daily" },
  { label: "考场节奏", href: "#timing" },
  { label: "参考来源", href: "#sources" },
];

const routeModules = ["资料分析", "判断推理", "言语理解", "数量关系"];
const companionModules = ["常识判断", "政治理论"];

export default async function XingcePage({ searchParams }: XingcePageProps) {
  const roadmap = await readRoadmap<XingceRoadmap>("xingce");

  if (!roadmap) {
    return null;
  }

  const params = await searchParams;
  const requestedModule = Array.isArray(params?.module) ? params.module[0] : params?.module;
  const activeModuleId = roadmap.moduleGuides?.some((module) => module.id === requestedModule)
    ? requestedModule
    : roadmap.moduleGuides?.[0]?.id;
  const profile = roadmap.examProfile;

  return (
    <main>
      <section className="hero-wash border-b border-[#e7e0d6]">
        <div className="relative z-10 mx-auto grid max-w-[1310px] gap-8 px-5 py-10 lg:grid-cols-[1fr_470px] lg:px-6 lg:py-12">
          <Reveal>
            <Badge className="mb-4 border-[#b5c4b7] bg-[#eff3ee] text-[#486958]">
              行测课程导航 · {roadmap.meta?.version ?? "知识库"}
            </Badge>
            <h1 className="ink-title text-[38px] lg:text-[44px]">{roadmap.title}</h1>
            <p className="mt-4 max-w-[720px] text-lg leading-8 text-[#55655d]">{roadmap.description}</p>
            <div className="no-print mt-7 flex flex-wrap gap-3">
              <Button asChild variant="outline" size="sm">
                <Link href="/api/export/xingce">导出 Markdown</Link>
              </Button>
              <PrintButton />
            </div>
          </Reveal>

          <Reveal delay={0.06}>
            <Card className="ornament-pavilion relative overflow-hidden p-6">
              <p className="label-sans text-xs tracking-[.18em] text-[#6f8376]">推荐课程顺序</p>
              <div className="label-sans relative z-10 mt-5 flex flex-wrap items-center gap-2">
                {routeModules.map((module, index) => (
                  <div className="flex items-center gap-2" key={module}>
                    <span className="rounded-lg border bg-[#faf8f2] px-3 py-2 text-sm font-medium text-[#355046]">
                      {module}
                    </span>
                    {index < routeModules.length - 1 ? (
                      <ArrowRight size={15} className="text-[#87a091]" />
                    ) : null}
                  </div>
                ))}
              </div>
              <div className="label-sans relative z-10 mt-5 flex flex-wrap items-center gap-2 text-sm">
                <span className="text-[#6d7b74]">全程低占用穿插：</span>
                {companionModules.map((module) => <Badge key={module}>{module}</Badge>)}
              </div>
              {profile ? (
                <div className="label-sans relative z-10 mt-6 grid grid-cols-3 gap-3">
                  <Stat value={`${profile.durationMinutes}`} label="分钟" />
                  <Stat value={`${profile.score}`} label="满分" />
                  <Stat value={`${profile.officialModules.length}`} label="板块" />
                </div>
              ) : null}
            </Card>
          </Reveal>
        </div>
      </section>

      <div className="no-print sticky top-[74px] z-10 border-b border-[#e7e0d6] bg-[#f8f6f1]/94 backdrop-blur-sm">
        <nav className="label-sans mx-auto flex max-w-[1310px] gap-2 overflow-x-auto px-5 py-3 lg:px-6">
          {sectionNav.map((item) => (
            <Link
              className="shrink-0 rounded-full border border-[#e0d9cc] bg-white/58 px-4 py-2 text-sm text-[#576860] transition-colors hover:border-[#9aac9f] hover:bg-[#edf2ec] hover:text-deep-green"
              href={item.href}
              key={item.href}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>

      <div className="mx-auto max-w-[1310px] space-y-8 px-5 py-8 lg:px-6">
        <Reveal>
          <section className="scroll-mt-36" id="roadmap">
            <SectionHeading
              icon={Route}
              title="课程学习顺序"
              description="先确定当前阶段的主攻模块，再选一套主线课程完成输入、刷题和验收。"
            />
            <div className="grid gap-4 lg:grid-cols-4">
              {roadmap.stages.map((stage, index) => (
                <Card className="hover-lift flex flex-col p-5" key={stage.id}>
                  <div className="mb-4 flex items-start justify-between gap-3">
                    <span className="label-sans flex size-9 shrink-0 items-center justify-center rounded-full bg-[#e7eee8] text-sm text-[#557565]">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <Badge>{stage.duration}</Badge>
                  </div>
                  <h3 className="text-lg font-semibold leading-7">{stage.title}</h3>
                  <p className="muted-copy mt-3 flex-1 text-sm leading-6">{stage.goal}</p>
                  {stage.milestone ? (
                    <p className="label-sans mt-4 rounded-lg bg-[#f6f3eb] p-3 text-xs leading-6 text-[#796748]">
                      验收：{stage.milestone}
                    </p>
                  ) : null}
                  <details className="print-expand label-sans mt-4 border-t pt-3 text-sm text-[#617068]">
                    <summary className="cursor-pointer font-medium text-[#4e6e5e]">查看课程与训练动作</summary>
                    <ul className="mt-3 space-y-2 leading-6">
                      {stage.tasks.map((task) => <li key={task}>• {task}</li>)}
                    </ul>
                  </details>
                </Card>
              ))}
            </div>
          </section>
        </Reveal>

        {roadmap.moduleGuides?.length ? (
          <Reveal delay={0.04}>
            <section className="scroll-mt-36" id="modules">
              <SectionHeading
                icon={BookOpenCheck}
                title="模块课程导航"
                description="从模块目的进入课程选择：确定一位主线老师，再配套专项刷题和验收标准。"
              />
              <div className="no-print">
                <XingceModuleExplorer
                  modules={roadmap.moduleGuides}
                  teacherGroups={roadmap.teacherGroups}
                  formulaCards={roadmap.formulaCards}
                  practiceChecklist={roadmap.practiceChecklist}
                  activeModuleId={activeModuleId}
                />
              </div>
              <PrintableModuleGuide roadmap={roadmap} />
            </section>
          </Reveal>
        ) : null}

        <Reveal delay={0.04}>
          <section className="scroll-mt-36" id="teachers">
            <SectionHeading
              icon={GraduationCap}
              title="老师与课程选择"
              description="课程的作用是建立一套稳定方法。主线只选一套，补漏和冲刺只在明确短板时加入。"
            />
            <div className="grid gap-5 lg:grid-cols-[.9fr_1.1fr]">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-deep-green">三层课程模型</h3>
                <div className="label-sans mt-5 space-y-4">
                  <CourseLayer index="01" title="主线课" description="完整建立模块方法，选定后至少练两周，不随意换体系。" />
                  <CourseLayer index="02" title="专项补漏" description="只处理错题统计暴露出的具体短板，不重复听整套基础课。" />
                  <CourseLayer index="03" title="冲刺课" description="考前收束高频题型、时政或套卷策略，不承担基础教学。" />
                </div>
              </Card>
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-deep-green">选课底线</h3>
                <div className="label-sans mt-5 grid gap-3 sm:grid-cols-2">
                  {(roadmap.teacherSelectionRules ?? []).map((rule) => (
                    <p className="rounded-lg border bg-[#fdfbf7] p-4 text-sm leading-6 text-[#617068]" key={rule}>
                      <CheckCheck size={16} className="mb-2 text-[#688876]" />
                      {rule}
                    </p>
                  ))}
                </div>
              </Card>
            </div>
          </section>
        </Reveal>

        {roadmap.dailyExecution?.length ? (
          <Reveal delay={0.04}>
            <section className="scroll-mt-36" id="daily">
              <SectionHeading
                icon={CalendarRange}
                title="每日课程执行"
                description="一天只保留三个动作：输入方法、限时刷题、错题复盘。"
              />
              <div className="grid gap-4 md:grid-cols-3">
                {roadmap.dailyExecution.map((item, index) => (
                  <Card className="p-5" key={item.period}>
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <span className="label-sans text-xs tracking-[.16em] text-[#789083]">
                        STEP {String(index + 1).padStart(2, "0")}
                      </span>
                      <Badge>{item.focus}</Badge>
                    </div>
                    <h3 className="text-xl font-semibold text-deep-green">{item.period}</h3>
                    <ul className="label-sans mt-4 space-y-2 text-sm leading-6 text-[#65736c]">
                      {item.actions.map((action) => <li key={action}>• {action}</li>)}
                    </ul>
                    <p className="label-sans mt-4 border-t pt-3 text-xs leading-6 text-[#796748]">
                      当日验收：{item.standard}
                    </p>
                  </Card>
                ))}
              </div>
            </section>
          </Reveal>
        ) : null}

        {roadmap.timePlan?.length ? (
          <Reveal delay={0.04}>
            <section className="scroll-mt-36" id="timing">
              <SectionHeading
                icon={Clock3}
                title="考场节奏"
                description="套卷期开始使用，并通过真题模拟固定个人顺序、跳题和涂卡方式。"
              />
              <Card className="p-6">
                <div className="label-sans grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {roadmap.timePlan.map((phase, index) => (
                    <div className="rounded-xl border bg-[#fdfbf7] p-4" key={phase.phase}>
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-xs text-[#819188]">{String(index + 1).padStart(2, "0")}</span>
                        <Badge>{phase.target}</Badge>
                      </div>
                      <p className="mt-3 font-medium text-[#32463d]">{phase.phase}</p>
                      <p className="mt-2 text-sm leading-6 text-[#68766e]">{phase.method}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </section>
          </Reveal>
        ) : null}

        <Reveal delay={0.04}>
          <section className="scroll-mt-36" id="sources">
            <SectionHeading
              icon={ShieldCheck}
              title="考试依据与公开来源"
              description="官方大纲用于确认考试事实；机构课程仅作为学习方法和选课参考。"
            />
            {profile ? (
              <Card className="mb-5 border-[#d7e0d8] bg-[#f5f7f1] p-5">
                <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
                  <div>
                    <Badge className="bg-[#e7eee8] text-[#50715e]">官方大纲</Badge>
                    <h3 className="mt-3 text-lg font-semibold text-deep-green">{profile.syllabusTitle}</h3>
                    <p className="label-sans mt-2 text-sm leading-7 text-[#52655b]">{roadmap.basisNote}</p>
                    <p className="label-sans mt-2 text-xs text-[#718078]">
                      发布日期：{profile.syllabusDate} · {profile.notice}
                    </p>
                  </div>
                  <a
                    className="label-sans inline-flex shrink-0 items-center gap-1 text-sm text-[#4c705e] hover:underline"
                    href={profile.syllabusUrl}
                    target="_blank"
                    rel="noreferrer"
                  >
                    查看原文 <ArrowUpRight size={14} />
                  </a>
                </div>
              </Card>
            ) : null}
            {roadmap.references?.length ? (
              <Card className="p-6">
                <h3 className="mb-5 flex items-center gap-2 text-lg font-semibold text-deep-green">
                  <BookMarked size={19} />
                  公开参考资料
                </h3>
                <div className="label-sans space-y-4">
                  {roadmap.references.map((reference) => (
                    <div className="flex flex-col justify-between gap-3 border-b border-[#ede6da] pb-4 last:border-0 last:pb-0 md:flex-row" key={reference.url}>
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge className={reference.kind === "官方大纲" ? "bg-[#e8efea] text-[#50715e]" : ""}>
                            {reference.kind}
                          </Badge>
                          <p className="font-medium text-[#2d4137]">{reference.title}</p>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-[#64736b]">
                          {reference.publisher} · 用途：{reference.note}
                        </p>
                        <p className="mt-1 text-xs text-[#87928c]">访问日期：{reference.accessedAt}</p>
                      </div>
                      <a
                        href={reference.url}
                        rel="noreferrer"
                        target="_blank"
                        className="flex shrink-0 items-center gap-1 text-sm text-[#4e705f] hover:underline"
                      >
                        查看原文 <ArrowUpRight size={14} />
                      </a>
                    </div>
                  ))}
                </div>
              </Card>
            ) : null}
          </section>
        </Reveal>

        <Reveal delay={0.06}>
          <PipelineStrip />
        </Reveal>
      </div>
    </main>
  );
}

function SectionHeading({
  icon: Icon,
  title,
  description,
}: {
  icon: typeof Compass;
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
    <div className="rounded-lg border bg-[#faf8f2] px-3 py-3 text-center">
      <p className="text-2xl font-semibold text-deep-green">{value}</p>
      <p className="mt-1 text-xs text-[#69766f]">{label}</p>
    </div>
  );
}

function CourseLayer({
  index,
  title,
  description,
}: {
  index: string;
  title: string;
  description: string;
}) {
  return (
    <div className="grid grid-cols-[42px_1fr] gap-3 rounded-lg border bg-[#fdfbf7] p-4">
      <span className="flex size-9 items-center justify-center rounded-full bg-[#e7eee8] text-xs text-[#557565]">
        {index}
      </span>
      <div>
        <p className="font-medium text-[#33483e]">{title}</p>
        <p className="mt-1 text-sm leading-6 text-[#69766f]">{description}</p>
      </div>
    </div>
  );
}

function PrintableModuleGuide({ roadmap }: { roadmap: XingceRoadmap }) {
  return (
    <div className="print-only space-y-6">
      {roadmap.moduleGuides?.map((module) => {
        const teacherGroup = roadmap.teacherGroups?.find((group) => group.moduleId === module.id);

        return (
          <Card className="break-inside-avoid p-5" key={module.id}>
            <h3 className="text-xl font-semibold text-deep-green">{module.title}</h3>
            <p className="muted-copy mt-2 text-sm leading-6">{module.ability}</p>
            <p className="label-sans mt-3 text-sm">题型范围：{module.topics.join("、")}</p>
            <div className="label-sans mt-4 grid gap-4 md:grid-cols-3">
              <PrintList title="课程使用顺序" items={module.methods} />
              <PrintList title="课后刷题动作" items={module.drills} />
              <PrintList title="常见误区" items={module.pitfalls} />
            </div>
            {teacherGroup?.teachers.length ? (
              <div className="label-sans mt-5 border-t pt-4">
                <p className="font-medium text-[#33473e]">老师与课程</p>
                <p className="mt-1 text-xs text-[#718078]">{teacherGroup.selectionNote}</p>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  {teacherGroup.teachers.map((teacher, index) => (
                    <div className="rounded-lg border p-3" key={`${module.id}-${teacher.name}`}>
                      <p className="font-medium text-deep-green">
                        {teacher.name} · {index === 0 || teacher.role.includes("主线") ? "主线" : "备选/补充"}
                      </p>
                      <p className="mt-1 text-xs text-[#68766e]">{teacher.role} · {teacher.stage}</p>
                      <ul className="mt-2 space-y-1 text-xs leading-5 text-[#68766e]">
                        {teacher.howToUse.map((item) => <li key={item}>• {item}</li>)}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </Card>
        );
      })}
      {roadmap.formulaCards?.length ? (
        <Card className="p-5">
          <h3 className="text-xl font-semibold text-deep-green">模块配套公式与规则</h3>
          <div className="label-sans mt-4 grid gap-4 md:grid-cols-2">
            {roadmap.formulaCards.map((card) => (
              <PrintList title={card.title} items={card.rules} key={card.title} />
            ))}
          </div>
        </Card>
      ) : null}
      {roadmap.practiceChecklist?.length ? (
        <Card className="p-5">
          <h3 className="text-xl font-semibold text-deep-green">训练检查项</h3>
          <div className="label-sans mt-4 grid gap-4 md:grid-cols-3">
            {roadmap.practiceChecklist.map((checklist) => (
              <PrintList title={checklist.title} items={checklist.items} key={checklist.title} />
            ))}
          </div>
        </Card>
      ) : null}
    </div>
  );
}

function PrintList({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <p className="font-medium text-[#33473e]">{title}</p>
      <ul className="mt-2 space-y-1 text-xs leading-5 text-[#68766e]">
        {items.map((item) => <li key={item}>• {item}</li>)}
      </ul>
    </div>
  );
}
