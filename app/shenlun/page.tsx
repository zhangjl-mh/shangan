import Link from "next/link";
import {
  ArrowUpRight,
  BookMarked,
  BookOpenCheck,
  CalendarRange,
  CheckCheck,
  Clock3,
  FilePenLine,
  Flag,
  GraduationCap,
  Layers3,
  LibraryBig,
  ListChecks,
  PenLine,
  Scale,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { PrintButton } from "@/components/export/print-button";
import { EmptyState } from "@/components/layout/empty-state";
import { PipelineStrip } from "@/components/layout/pipeline-strip";
import { ShenlunMarkdownDownloadButton } from "@/components/shenlun/markdown-download-button";
import { QuestionTypeExplorer } from "@/components/shenlun/question-type-explorer";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Reveal } from "@/components/ui/reveal";
import { readRoadmap } from "@/lib/content";
import type { RoadmapStage } from "@/lib/types";

export const dynamic = "force-dynamic";

const sectionNav = [
  { label: "考试依据", href: "#guide" },
  { label: "学习路线", href: "#roadmap" },
  { label: "题型技法", href: "#techniques" },
  { label: "材料阅读", href: "#reading" },
  { label: "应用文", href: "#documents" },
  { label: "大作文", href: "#essay" },
  { label: "训练复盘", href: "#training" },
  { label: "参考来源", href: "#sources" },
];

const stageTone = [
  "bg-[#e7eee8] text-[#557564]",
  "bg-[#e8edf6] text-[#557db2]",
  "bg-[#f3ecdf] text-[#997341]",
  "bg-[#e7eee8] text-[#557564]",
  "bg-[#e8edf6] text-[#557db2]",
  "bg-[#f3ecdf] text-[#997341]",
  "bg-[#e7eee8] text-[#557564]",
];

export default async function ShenlunPage() {
  const roadmap = await readRoadmap("shenlun");

  if (!roadmap) {
    return (
      <main className="mx-auto max-w-[1310px] px-5 py-12 lg:px-6">
        <Card className="p-6">
          <EmptyState
            className="min-h-[500px]"
            title="申论学习内容尚未载入"
            description="将经过核验的申论知识库或 Skills 生成内容写入本地文件后，可在此阅读。"
          />
        </Card>
      </main>
    );
  }

  const guide = roadmap.examGuide;

  return (
    <main>
      <section className="hero-wash border-b border-[#e7e0d6]">
        <div className="relative z-10 mx-auto grid max-w-[1310px] gap-8 px-5 py-10 lg:grid-cols-[1fr_480px] lg:px-6 lg:py-12">
          <Reveal>
            <Badge className="mb-4 border-[#b5c4b7] bg-[#eff3ee] text-[#486958]">
              系统学习中心 · {roadmap.meta?.version ?? "知识库"}
            </Badge>
            <h1 className="ink-title text-[38px] lg:text-[44px]">{roadmap.title}</h1>
            <p className="mt-4 max-w-[690px] text-lg leading-8 text-[#55655d]">{roadmap.description}</p>
            <div className="no-print mt-7 flex flex-wrap gap-3">
              <ShenlunMarkdownDownloadButton />
              <PrintButton label="导出 PDF" />
            </div>
          </Reveal>
          {guide ? (
            <Reveal delay={0.06}>
              <Card className="ornament-pavilion relative h-full overflow-hidden p-6">
                <p className="label-sans text-xs tracking-[.18em] text-[#6f8376]">当前考试依据</p>
                <h2 className="mt-3 text-lg font-semibold leading-7 text-[#20352d]">
                  {guide.syllabusTitle}
                </h2>
                <div className="label-sans mt-5 grid grid-cols-3 gap-3">
                  <Stat value={`${guide.durationMinutes}`} label="分钟" />
                  <Stat value={`${guide.score}`} label="满分" />
                  <Stat value={`${guide.paperTypes.length}`} label="试卷类别" />
                </div>
                <p className="muted-copy relative z-10 mt-5 text-xs leading-6">
                  发布日期：{guide.syllabusDate}。后续新招录周期公布大纲后需重新核对。
                </p>
              </Card>
            </Reveal>
          ) : null}
        </div>
      </section>

      <div className="sticky top-[74px] z-10 border-b border-[#e7e0d6] bg-[#f8f6f1]/94 backdrop-blur-sm">
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

      <div className="mx-auto max-w-[1310px] space-y-7 px-5 py-7 lg:px-6">
        {guide ? (
          <Reveal>
            <section className="scroll-mt-36" id="guide">
              <SectionHeading
                icon={ShieldCheck}
                title="考试依据与能力地图"
                description="先以官方大纲明确考试边界，再用专项训练落实能力要求。"
              />
              <Card className="mb-5 border-[#d7e0d8] bg-[#f5f7f1] p-5">
                <p className="label-sans text-sm leading-7 text-[#51645a]">{roadmap.basisNote}</p>
                <a
                  href={guide.syllabusUrl}
                  rel="noreferrer"
                  target="_blank"
                  className="label-sans mt-3 inline-flex items-center gap-1 text-sm text-[#456b5a] hover:underline"
                >
                  查看大纲原文 <ArrowUpRight size={14} />
                </a>
              </Card>
              <div className="grid gap-4 lg:grid-cols-3">
                {guide.paperTypes.map((paper, index) => (
                  <Card className="hover-lift p-5" key={paper.title}>
                    <div className="mb-4 flex items-center gap-3">
                      <span className={`label-sans flex size-9 items-center justify-center rounded-full text-sm ${stageTone[index]}`}>
                        0{index + 1}
                      </span>
                      <h3 className="text-[17px] font-semibold leading-7">{paper.title}</h3>
                    </div>
                    <p className="muted-copy mb-4 text-sm leading-6">{paper.focus}</p>
                    <ul className="label-sans space-y-3 text-sm leading-6 text-[#64736b]">
                      {paper.abilities.map((ability) => (
                        <li className="flex gap-2" key={ability}>
                          <CheckCheck size={15} className="mt-1 shrink-0 text-[#6b8c78]" />
                          <span>{ability}</span>
                        </li>
                      ))}
                    </ul>
                  </Card>
                ))}
              </div>
              <Card className="mt-5 p-5">
                <h3 className="mb-4 flex items-center gap-2 text-lg font-semibold text-deep-green">
                  <Scale size={20} className="text-[#668674]" />
                  作答底线规则
                </h3>
                <div className="label-sans grid gap-3 md:grid-cols-2">
                  {guide.answerRules.map((rule) => (
                    <p className="rounded-lg bg-[#f8f7f2] px-4 py-3 text-sm leading-6 text-[#5e6d65]" key={rule}>
                      {rule}
                    </p>
                  ))}
                </div>
              </Card>
            </section>
          </Reveal>
        ) : null}

        <Reveal delay={0.03}>
          <section className="scroll-mt-36" id="roadmap">
            <SectionHeading
              icon={CalendarRange}
              title="七阶段系统学习路线"
              description="从认识题本到套卷复盘，按能力形成的先后顺序推进。"
            />
            <div className="grid gap-4 lg:grid-cols-2">
              {roadmap.stages.map((stage, index) => (
                <StageCard stage={stage} index={index} key={stage.id} />
              ))}
            </div>
          </section>
        </Reveal>

        {roadmap.coreWorkflow?.length ? (
          <Reveal delay={0.05}>
            <section>
              <SectionHeading
                icon={Layers3}
                title="每一道题的六步作答流程"
                description="不论题型如何变化，稳定执行审题、找点、加工、书写和复盘。"
              />
              <Card className="p-5">
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {roadmap.coreWorkflow.map((step, index) => (
                    <div className="rounded-xl border bg-white/52 p-4" key={step.id}>
                      <div className="mb-3 flex items-center gap-3">
                        <span className="label-sans flex size-8 items-center justify-center rounded-full bg-[#e8efea] text-xs font-medium text-[#577365]">
                          0{index + 1}
                        </span>
                        <h3 className="font-semibold tracking-[.08em]">{step.title}</h3>
                      </div>
                      <p className="muted-copy text-sm leading-6">{step.purpose}</p>
                      <p className="label-sans mt-3 text-xs text-[#547061]">产出：{step.output}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </section>
          </Reveal>
        ) : null}

        {roadmap.questionTypes?.length ? (
          <Reveal delay={0.05}>
            <section className="scroll-mt-36" id="techniques">
              <SectionHeading
                icon={GraduationCap}
                title="五大题型技法库"
                description="点击切换题型，查看识别信号、作答结构、找点方法、失误警报与训练动作。"
              />
              <QuestionTypeExplorer questionTypes={roadmap.questionTypes} />
            </section>
          </Reveal>
        ) : null}

        {roadmap.readingMethod ? (
          <Reveal delay={0.05}>
            <section className="scroll-mt-36" id="reading">
              <SectionHeading
                icon={BookOpenCheck}
                title="材料阅读与要点加工"
                description="阅读不是通读后凭印象写答案，而是带着任务逐层提炼。"
              />
              <div className="grid gap-5 lg:grid-cols-[1.15fr_.85fr]">
                <Card className="p-6">
                  <h3 className="mb-5 text-lg font-semibold tracking-[.08em] text-deep-green">三遍阅读法</h3>
                  <div className="space-y-4">
                    {roadmap.readingMethod.passes.map((pass, index) => (
                      <div className="relative rounded-xl border bg-[#fdfbf7] p-5 pl-16" key={pass.title}>
                        <span className="label-sans absolute left-5 top-5 flex size-8 items-center justify-center rounded-full bg-[#e7eee8] text-sm text-[#557565]">
                          {index + 1}
                        </span>
                        <div className="flex flex-wrap items-center gap-3">
                          <h4 className="font-semibold text-[#283a32]">{pass.title}</h4>
                          <Badge>{pass.time}</Badge>
                        </div>
                        <ul className="label-sans mt-3 space-y-2 text-sm leading-6 text-[#637169]">
                          {pass.actions.map((action) => <li key={action}>• {action}</li>)}
                        </ul>
                      </div>
                    ))}
                  </div>
                </Card>
                <div className="space-y-5">
                  <Card className="p-5">
                    <h3 className="mb-4 text-lg font-semibold tracking-[.08em] text-deep-green">符号标记表</h3>
                    <div className="label-sans space-y-3">
                      {roadmap.readingMethod.markerLegend.map((marker) => (
                        <div className="flex gap-3 rounded-lg bg-[#faf8f2] p-3" key={marker.symbol}>
                          <span className="flex size-8 shrink-0 items-center justify-center rounded bg-[#e8efea] font-medium text-[#557565]">
                            {marker.symbol}
                          </span>
                          <div className="text-sm">
                            <p className="font-medium text-[#34463e]">{marker.meaning}</p>
                            <p className="mt-1 text-[#738078]">{marker.examples}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                  <Card className="p-5">
                    <h3 className="mb-3 text-lg font-semibold tracking-[.08em] text-deep-green">加工四原则</h3>
                    <ul className="label-sans space-y-3 text-sm leading-6 text-[#637169]">
                      {roadmap.readingMethod.processingRules.map((rule) => (
                        <li className="flex gap-2" key={rule}>
                          <Target size={15} className="mt-1 shrink-0 text-[#678574]" />
                          {rule}
                        </li>
                      ))}
                    </ul>
                  </Card>
                </div>
              </div>
            </section>
          </Reveal>
        ) : null}

        {roadmap.documentTypes?.length ? (
          <Reveal delay={0.05}>
            <section className="scroll-mt-36" id="documents">
              <SectionHeading
                icon={FilePenLine}
                title="贯彻执行与应用文文种库"
                description="先判断身份、对象、目的与形式，再决定格式和信息重点。"
              />
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {roadmap.documentTypes.map((document) => (
                  <Card className="hover-lift p-5" key={document.title}>
                    <h3 className="text-lg font-semibold tracking-[.07em]">{document.title}</h3>
                    <p className="label-sans mt-2 text-sm text-[#6b7871]">对象：{document.audience}</p>
                    <ol className="label-sans mt-4 space-y-2 text-sm text-[#5d6e65]">
                      {document.structure.map((step, index) => (
                        <li className="flex gap-2" key={step}>
                          <span className="text-[#789486]">{index + 1}.</span>
                          {step}
                        </li>
                      ))}
                    </ol>
                    <p className="muted-copy mt-4 border-t pt-3 text-xs leading-6">{document.focus}</p>
                  </Card>
                ))}
              </div>
            </section>
          </Reveal>
        ) : null}

        {roadmap.essayMethod ? (
          <Reveal delay={0.05}>
            <section className="scroll-mt-36" id="essay">
              <SectionHeading
                icon={PenLine}
                title="申发论述与大作文"
                description="以材料主旨确定立意，以清晰论点和分析论证撑起文章。"
              />
              <div className="grid gap-5 lg:grid-cols-[.76fr_1.24fr]">
                <Card className="p-6">
                  <h3 className="mb-4 text-lg font-semibold text-deep-green">立意校准</h3>
                  <ul className="label-sans space-y-4 text-sm leading-7 text-[#617068]">
                    {roadmap.essayMethod.positioning.map((item) => (
                      <li className="flex gap-3" key={item}>
                        <Sparkles size={16} className="mt-1.5 shrink-0 text-[#987642]" />
                        {item}
                      </li>
                    ))}
                  </ul>
                  <h3 className="mb-3 mt-7 text-lg font-semibold text-deep-green">避免失分</h3>
                  <ul className="label-sans space-y-3 text-sm leading-6 text-[#68746e]">
                    {roadmap.essayMethod.pitfalls.map((pitfall) => <li key={pitfall}>• {pitfall}</li>)}
                  </ul>
                </Card>
                <Card className="p-6">
                  <h3 className="mb-5 text-lg font-semibold text-deep-green">文章结构路径</h3>
                  <div className="space-y-3">
                    {roadmap.essayMethod.structure.map((section, index) => (
                      <div className="label-sans grid gap-3 rounded-xl border bg-[#fdfbf7] p-4 sm:grid-cols-[90px_1fr]" key={section.part}>
                        <span className="font-medium text-[#537061]">
                          {String(index + 1).padStart(2, "0")} · {section.part}
                        </span>
                        <p className="text-sm leading-6 text-[#65736c]">{section.method}</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-5 rounded-xl bg-[#f4f0e8] p-5">
                    <p className="mb-3 font-semibold text-[#5a4931]">可用论证工具</p>
                    <div className="label-sans grid gap-2 text-sm leading-6 text-[#74634c] sm:grid-cols-2">
                      {roadmap.essayMethod.argumentTools.map((tool) => <p key={tool}>• {tool}</p>)}
                    </div>
                  </div>
                </Card>
              </div>
            </section>
          </Reveal>
        ) : null}

        {roadmap.topicToolkit?.length ? (
          <Reveal delay={0.05}>
            <section>
              <SectionHeading
                icon={LibraryBig}
                title="主题素材与规范表达"
                description="素材用于理解和表达训练；正式答题仍须围绕给定资料。"
              />
              <div className="grid gap-4 md:grid-cols-2">
                {roadmap.topicToolkit.map((topic) => (
                  <Card className="p-5" key={topic.topic}>
                    <h3 className="text-lg font-semibold text-deep-green">{topic.topic}</h3>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {topic.angles.map((angle) => <Badge key={angle}>{angle}</Badge>)}
                    </div>
                    <ul className="label-sans mt-4 space-y-2 text-sm leading-6 text-[#64736b]">
                      {topic.usableExpressions.map((expression) => <li key={expression}>“{expression}”</li>)}
                    </ul>
                  </Card>
                ))}
              </div>
            </section>
          </Reveal>
        ) : null}

        <Reveal delay={0.05}>
          <section className="scroll-mt-36" id="training">
            <SectionHeading
              icon={ListChecks}
              title="训练计划、考场时间与复盘"
              description="方法必须通过限时作答和复盘固化，才能转化为稳定得分。"
            />
            {roadmap.trainingPlans?.length ? (
              <div className="mb-5 grid gap-5 lg:grid-cols-2">
                {roadmap.trainingPlans.map((plan) => (
                  <Card className="p-6" key={plan.title}>
                    <h3 className="text-xl font-semibold text-deep-green">{plan.title}</h3>
                    <p className="muted-copy mt-2 text-sm leading-6">{plan.suitedFor}</p>
                    <div className="label-sans mt-5 space-y-3">
                      {plan.weeks.map((week) => (
                        <div className="grid gap-2 rounded-lg border bg-[#fdfbf7] p-4 sm:grid-cols-[92px_1fr]" key={week.period}>
                          <p className="font-medium text-[#567363]">{week.period}</p>
                          <div className="text-sm leading-6 text-[#66746d]">
                            <p>{week.focus}</p>
                            <p className="text-xs text-[#937647]">产出：{week.deliverable}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                ))}
              </div>
            ) : null}
            <div className="grid gap-5 lg:grid-cols-[.9fr_1.1fr]">
              {roadmap.examTiming?.length ? (
                <Card className="p-6">
                  <h3 className="mb-5 flex items-center gap-2 text-lg font-semibold text-deep-green">
                    <Clock3 size={19} />
                    180 分钟时间分配参考
                  </h3>
                  <div className="label-sans space-y-4">
                    {roadmap.examTiming.map((item) => (
                      <div key={item.phase}>
                        <div className="flex items-center justify-between text-sm">
                          <p className="font-medium text-[#34483e]">{item.phase}</p>
                          <Badge>{item.minutes}</Badge>
                        </div>
                        <p className="mt-2 text-xs leading-6 text-[#6b7971]">{item.action}</p>
                      </div>
                    ))}
                  </div>
                </Card>
              ) : null}
              {roadmap.reviewChecklist?.length ? (
                <Card className="p-6">
                  <h3 className="mb-5 flex items-center gap-2 text-lg font-semibold text-deep-green">
                    <Flag size={19} />
                    每次练习后检查
                  </h3>
                  <div className="label-sans grid gap-4 sm:grid-cols-2">
                    {roadmap.reviewChecklist.map((group) => (
                      <div className="rounded-lg border bg-[#fdfbf7] p-4" key={group.category}>
                        <p className="mb-3 font-medium text-[#4e6c5c]">{group.category}</p>
                        <ul className="space-y-2 text-xs leading-6 text-[#68766e]">
                          {group.items.map((item) => <li key={item}>□ {item}</li>)}
                        </ul>
                      </div>
                    ))}
                  </div>
                </Card>
              ) : null}
            </div>
          </section>
        </Reveal>

        {roadmap.references?.length ? (
          <Reveal delay={0.05}>
            <section className="scroll-mt-36" id="sources">
              <SectionHeading
                icon={BookMarked}
                title="公开参考来源"
                description="官方大纲用于事实依据；培训机构公开内容仅用于通用方法整理与交叉参考。"
              />
              <Card className="p-6">
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
                        <p className="mt-2 text-sm text-[#64736b]">
                          {reference.publisher} · {reference.note}
                        </p>
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
            </section>
          </Reveal>
        ) : null}

        <Reveal delay={0.08}>
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
  icon: typeof ShieldCheck;
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

function StageCard({ stage, index }: { stage: RoadmapStage; index: number }) {
  return (
    <Card className="hover-lift relative overflow-hidden p-5">
      <div className="flex gap-4">
        <span className={`label-sans flex size-11 shrink-0 items-center justify-center rounded-xl text-sm font-medium ${stageTone[index % stageTone.length]}`}>
          {String(index + 1).padStart(2, "0")}
        </span>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold tracking-[.05em]">{stage.title}</h3>
            {stage.duration ? <Badge>{stage.duration}</Badge> : null}
          </div>
          <p className="muted-copy mt-2 text-sm leading-6">{stage.goal}</p>
        </div>
      </div>
      <ul className="label-sans mt-4 space-y-2 text-sm leading-6 text-[#62716a]">
        {stage.tasks.map((task) => (
          <li className="flex gap-2" key={task}>
            <span className="text-[#72917e]">•</span>
            {task}
          </li>
        ))}
      </ul>
      {stage.milestone ? (
        <p className="label-sans mt-4 rounded-lg bg-[#f6f3eb] px-3 py-2 text-xs leading-6 text-[#7b6849]">
          验收标志：{stage.milestone}
        </p>
      ) : null}
    </Card>
  );
}
