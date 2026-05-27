"use client";

import { useState } from "react";
import { AlertTriangle, CheckCircle2, Compass, Dumbbell, SearchCheck } from "lucide-react";
import type { StudyRoadmap } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type QuestionType = NonNullable<StudyRoadmap["questionTypes"]>[number];

export function QuestionTypeExplorer({ questionTypes }: { questionTypes: QuestionType[] }) {
  const [activeId, setActiveId] = useState(questionTypes[0]?.id ?? "");
  const active = questionTypes.find((item) => item.id === activeId) ?? questionTypes[0];

  if (!active) {
    return null;
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="label-sans flex overflow-x-auto border-b border-[#ebe4d9] bg-[#fcfaf5] p-3">
        {questionTypes.map((item) => (
          <button
            type="button"
            key={item.id}
            onClick={() => setActiveId(item.id)}
            className={cn(
              "shrink-0 rounded-lg px-5 py-3 text-sm transition-colors",
              activeId === item.id
                ? "bg-[#698878] text-white"
                : "text-[#53625a] hover:bg-[#eef1eb]",
            )}
          >
            {item.title}
          </button>
        ))}
      </div>
      <div className="grid gap-6 p-6 lg:grid-cols-[.78fr_1.22fr]">
        <div>
          <Badge className="bg-[#eef2ea]">{active.subtitle}</Badge>
          <h3 className="ink-title mt-4 text-2xl">{active.title}</h3>
          <p className="muted-copy mt-3 text-sm leading-7">{active.coreGoal}</p>
          <TechniqueBlock icon={Compass} title="识别信号">
            <div className="flex flex-wrap gap-2">
              {active.taskSignals.map((signal) => (
                <Badge className="bg-white" key={signal}>{signal}</Badge>
              ))}
            </div>
          </TechniqueBlock>
          <TechniqueBlock icon={AlertTriangle} title="高频失误">
            <ul className="space-y-2">
              {active.pitfalls.map((pitfall) => (
                <li key={pitfall}>• {pitfall}</li>
              ))}
            </ul>
          </TechniqueBlock>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <TechniquePanel icon={CheckCircle2} title="作答结构" items={active.answerFramework} tone="green" />
          <TechniquePanel icon={SearchCheck} title="找点与加工" items={active.pointMethods} tone="blue" />
          <div className="sm:col-span-2">
            <TechniquePanel icon={Dumbbell} title="专项训练动作" items={active.drills} tone="sand" />
          </div>
        </div>
      </div>
    </Card>
  );
}

function TechniqueBlock({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof Compass;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="label-sans mt-6">
      <h4 className="mb-3 flex items-center gap-2 text-sm font-medium text-[#33473e]">
        <Icon size={17} className="text-[#648371]" />
        {title}
      </h4>
      <div className="text-sm leading-6 text-[#66746d]">{children}</div>
    </div>
  );
}

function TechniquePanel({
  icon: Icon,
  title,
  items,
  tone,
}: {
  icon: typeof CheckCircle2;
  title: string;
  items: string[];
  tone: "green" | "blue" | "sand";
}) {
  const tint = {
    green: "bg-[#e8efea] text-[#567464]",
    blue: "bg-[#e8eef6] text-[#557bb0]",
    sand: "bg-[#f3ece1] text-[#977341]",
  }[tone];

  return (
    <div className="label-sans h-full rounded-xl border border-[#ece5da] bg-[#fdfbf7] p-5">
      <h4 className="mb-4 flex items-center gap-3 font-medium text-[#2c3d35]">
        <span className={`flex size-8 items-center justify-center rounded-full ${tint}`}>
          <Icon size={17} />
        </span>
        {title}
      </h4>
      <ul className="space-y-3 text-sm leading-6 text-[#66746d]">
        {items.map((item) => (
          <li className="flex gap-2" key={item}>
            <span className="mt-[9px] size-1.5 shrink-0 rounded-full bg-[#8ba293]" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
