import Link from "next/link";
import {
  ArrowRight,
  BookOpenText,
  BriefcaseBusiness,
  ClipboardList,
  Globe2,
  GraduationCap,
  MapPin,
  UserRound,
} from "lucide-react";
import { ModuleCard } from "@/components/dashboard/module-card";
import { EmptyState } from "@/components/layout/empty-state";
import { PipelineStrip } from "@/components/layout/pipeline-strip";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Reveal } from "@/components/ui/reveal";
import {
  readEligibleJobs,
  readLatestNews,
  readProfile,
  readRoadmap,
} from "@/lib/content";
import { formatDisplayDate, formatShortDate } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [profile, news, jobs, shenlun, xingce] = await Promise.all([
    readProfile(),
    readLatestNews(),
    readEligibleJobs(),
    readRoadmap("shenlun"),
    readRoadmap("xingce"),
  ]);

  const regionText =
    profile?.target.targetRegions?.join("、") || "尚未填写";

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
    {
      icon: BriefcaseBusiness,
      tint: "bg-[#e3e8ef] text-[#516985]",
      title: "岗位查看",
      copy: jobs ? `已核验 ${jobs.positions.length} 个官方匹配岗位，状态以岗位页为准` : "等待 Skills 生成岗位扫描结果",
    },
  ];

  return (
    <main>
      <section className="hero-wash border-b border-[#ebe5db]">
        <div className="relative z-10 mx-auto grid max-w-[1450px] gap-7 px-5 py-11 lg:grid-cols-[1.05fr_.92fr] lg:px-10 lg:py-12">
          <Reveal className="flex flex-col justify-center lg:pl-16">
            <p className="muted-copy mb-4 text-sm">{formatDisplayDate(new Date())}</p>
            <h1 className="ink-title text-[34px] leading-[1.45] sm:text-[38px] lg:text-[34px] lg:tracking-[.04em] min-[1450px]:text-[43px] min-[1450px]:tracking-[.07em]">
              让备考慢下来，
              <br className="hidden lg:block min-[1450px]:hidden" />
              也更稳下来
            </h1>
            <p className="mt-4 max-w-lg text-lg leading-8 text-[#606d66]">
              前端仅展示 Agent / Skills 写入的本地数据，
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
          <Reveal delay={0.08} className="flex items-center">
            <Card className="ml-auto w-full max-w-[552px] px-7 py-6">
              {profile ? (
                <div className="grid gap-5 sm:grid-cols-[108px_1fr]">
                  <div className="flex items-center justify-center border-b border-[#ede7dd] pb-5 sm:border-r sm:border-b-0 sm:pb-0">
                    <span className="flex size-[84px] items-center justify-center rounded-full bg-[#e4e9e1] text-[#577568]">
                      <UserRound size={42} strokeWidth={1.3} />
                    </span>
                  </div>
                  <div className="label-sans grid grid-cols-2 gap-x-7 gap-y-5 text-sm">
                    <ProfileFact icon={GraduationCap} label="学历" value={profile.basic.education || "未填写"} />
                    <ProfileFact icon={BookOpenText} label="专业" value={profile.basic.major || "未填写"} />
                    <ProfileFact icon={MapPin} label="目标地区" value={regionText} />
                    <ProfileFact
                      icon={BriefcaseBusiness}
                      label="目标岗位"
                      value={profile.target.targetJobTypes?.join("、") || "未填写"}
                    />
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3 py-5 text-center sm:flex-row sm:text-left">
                  <span className="flex size-[72px] shrink-0 items-center justify-center rounded-full bg-[#e4e9e1] text-[#577568]">
                    <UserRound size={34} strokeWidth={1.35} />
                  </span>
                  <div className="sm:ml-4">
                    <p className="ink-title text-lg">画像尚未建立</p>
                    <p className="muted-copy mt-1 text-sm leading-6">
                      可在画像设置中填写，或由 Skills 问询后写入本地画像文件。
                    </p>
                  </div>
                  <Button asChild variant="outline" size="sm" className="sm:ml-auto">
                    <Link href="/profile">开始填写</Link>
                  </Button>
                </div>
              )}
            </Card>
          </Reveal>
        </div>
      </section>

      <div className="mx-auto max-w-[1450px] space-y-5 px-5 py-5 lg:px-10">
        <Reveal className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" delay={0.1}>
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
            href="/job"
            icon={BriefcaseBusiness}
            title="岗位"
            description="真实岗位 · 条件符合 · 信源核验"
            note={jobs ? `${jobs.positions.length} 个官方匹配参考` : "等待生成符合岗位"}
            tint="bg-[#d4a867]"
          />
          <ModuleCard
            href="/news"
            icon={Globe2}
            title="时政"
            description="每日热点 · 政策解读 · 时政积累"
            note={news ? news.date : "等待今日时政"}
            tint="bg-[#728bb4]"
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

function ProfileFact({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof GraduationCap;
  label: string;
  value: string;
}) {
  return (
    <div className="flex min-w-0 gap-3">
      <Icon className="mt-0.5 shrink-0 text-[#69746f]" size={20} strokeWidth={1.5} />
      <div className="min-w-0">
        <p className="text-[#6a756f]">{label}</p>
        <p className="mt-1 truncate font-medium text-[#293631]">{value}</p>
      </div>
    </div>
  );
}
