"use client";

import { useState } from "react";
import { AlertTriangle, Dumbbell, Layers3, Route } from "lucide-react";
import type { XingceRoadmap } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type ModuleGuide = NonNullable<XingceRoadmap["moduleGuides"]>[number];

export function XingceModuleExplorer({ modules }: { modules: ModuleGuide[] }) {
  const [activeId, setActiveId] = useState(modules[0]?.id ?? "");
  const active = modules.find((module) => module.id === activeId) ?? modules[0];

  if (!active) {
    return null;
  }

  return (
    <Card className="overflow-hidden p-0">
      <div className="label-sans flex overflow-x-auto border-b bg-[#fcfaf5] p-3">
        {modules.map((module) => (
          <button
            type="button"
            key={module.id}
            onClick={() => setActiveId(module.id)}
            className={cn(
              "shrink-0 rounded-lg px-5 py-3 text-sm",
              module.id === activeId ? "bg-[#698878] text-white" : "text-[#53625a] hover:bg-[#eef1eb]",
            )}
          >
            {module.title}
          </button>
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
