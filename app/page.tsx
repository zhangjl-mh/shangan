import Link from "next/link";
import {
  ArrowRight,
  BookOpenText,
  ClipboardList,
  BriefcaseBusiness,
  Globe2,
} from "lucide-react";
import { ModuleCard } from "@/app/components/home/module-card";
import { EmptyState } from "@/app/components/layout/empty-state";
import { PipelineStrip } from "@/app/components/layout/pipeline-strip";
import { Button } from "@/app/components/ui/button";
import { Card } from "@/app/components/ui/card";
import { Reveal } from "@/app/components/ui/reveal";
import {
  readLatestNews,
  readRoadmap,
} from "@/app/services/content";
import { formatDisplayDate, formatShortDate } from "@/app/utils";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [news, shenlun, xingce] = await Promise.all([
    readLatestNews(),
    readRoadmap("shenlun"),
    readRoadmap("xingce"),
  ]);

  const todayPlan = [
    {
      icon: Globe2,
      tint: "bg-[#e2e9df] text-[#4d745d]",
      title: "时政阅读",
      copy: news ? `${news.date} 已核验 ${news.items.length} 条，可进入阅读` : "等待 Skills 生成已核验热点内容",
    },
    {
      icon: BookOpenText,
      tint: "bg-[#e4edf8] text-[#477abd]",
      title: "申论研读",
      copy: shenlun ? `继续学习：${shenlun.stages[0]?.title ?? shenlun.title}` : "尚未写入申论学习路线",
    },
    {
      icon: ClipboardList,
      tint: "bg-[#f2e9da] text-[#aa7a39]",
      title: "行测整理",
      copy: xingce ? `查看 ${xingce.stages.length} 个训练阶段` : "尚未写入行测学习路线",
    },
  ];

  return (
    <main>
      <section className="hero-wash border-b border-[#ebe5db]">
        <div className="relative z-10 mx-auto max-w-[1450px] px-5 py-11 lg:px-10 lg:py-12">
          <Reveal className="flex flex-col justify-center lg:pl-16">
            <p className="muted-copy mb-4 text-sm">{formatDisplayDate(new Date())}</p>
            <h1 className="ink-title text-[34px] leading-[1.45] sm:text-[38px] lg:text-[34px] lg:tracking-[.04em] min-[1450px]:text-[43px] min-[1450px]:tracking-[.07em]">
              让备考慢下来，
              <br className="hidden lg:block min-[1450px]:hidden" />
              也更稳下来
            </h1>
            <p className="mt-4 max-w-lg text-lg leading-8 text-[#606d66]">
              把时政、申论和行测收在一处，
              <br className="hidden sm:block" />
              专注当下，积累每一次进步。
            </p>
            <Button asChild className="mt-6 w-fit">
              <Link href="/shenlun">
                进入今日学习
                <ArrowRight size={17} />
              </Link>
            </Button>
          </Reveal>
        </div>
      </section>

      <div className="mx-auto max-w-[1450px] space-y-5 px-5 py-5 lg:px-10">
        <Reveal className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" delay={0.1}>
          <ModuleCard
            href="/shenlun"
            icon={BookOpenText}
            title="申论"
            description="阅读理解 · 综合分析 · 提出对策"
            note={shenlun ? "本地学习路线已载入" : "等待本地学习路线"}
            tint="bg-[#8ca690]"
          />
          <ModuleCard
            href="/xingce"
            icon={ClipboardList}
            title="行测"
            description="言语理解 · 判断推理 · 资料分析"
            note={xingce ? "本地训练计划已载入" : "等待本地训练计划"}
            tint="bg-[#5688c5]"
          />
          <ModuleCard
            href="/news"
            icon={Globe2}
            title="时政"
            description="每日热点 · 政策解读 · 时政积累"
            note={news ? news.date : "等待今日时政"}
            tint="bg-[#728bb4]"
          />
          <ModuleCard
            href="/jobs"
            icon={BriefcaseBusiness}
            title="岗位"
            description="国考 · 京津冀省考 · 条件筛选"
            note="官方附件本地归档"
            tint="bg-[#9a7855]"
          />
        </Reveal>

        <div className="grid gap-5 lg:grid-cols-[1.08fr_.92fr]">
          <Reveal delay={0.16}>
            <Card className="h-full p-6">
              <div className="mb-5 flex items-center justify-between">
                <h2 className="section-title">最新已核验时政</h2>
                <Link href="/news" className="label-sans text-sm text-[#718078] hover:text-deep-green">
                  查看更多 &gt;
                </Link>
              </div>
              {news?.items.length ? (
                <ul className="space-y-4">
                  {news.items.slice(0, 5).map((item) => (
                    <li key={item.id} className="grid grid-cols-[12px_1fr_auto_auto] items-center gap-4 text-[15px]">
                      <span className="size-1.5 rounded-full bg-[#729780]" />
                      <span className="truncate">{item.title}</span>
                      <span className="muted-copy hidden text-sm sm:block">{item.source}</span>
                      <span className="muted-copy text-sm">{formatShortDate(item.publishTime)}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState
                  className="min-h-[173px]"
                  title="尚未生成已核验时政数据"
                  description="通过 Skills 获取权威来源内容后，热点与原文信源将在这里展示。"
                />
              )}
            </Card>
          </Reveal>
          <Reveal delay={0.2}>
            <Card className="h-full p-6">
              <h2 className="section-title mb-5">今日学习安排</h2>
              <div className="space-y-4">
                {todayPlan.map((plan) => {
                  const Icon = plan.icon;
                  return (
                    <div key={plan.title} className="flex items-center gap-4">
                      <span className={`flex size-10 shrink-0 items-center justify-center rounded-full ${plan.tint}`}>
                        <Icon size={20} strokeWidth={1.7} />
                      </span>
                      <div className="min-w-0">
                        <p className="text-lg font-semibold tracking-[.07em]">{plan.title}</p>
                        <p className="muted-copy truncate text-sm">{plan.copy}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>
          </Reveal>
        </div>
        <Reveal delay={0.24}>
          <PipelineStrip />
        </Reveal>
      </div>
    </main>
  );
}
