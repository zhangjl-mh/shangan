import {
  Bot,
  CodeXml,
  Database,
  FileText,
  Monitor,
  MoveRight,
} from "lucide-react";
import { Card } from "@/components/ui/card";

const steps = [
  { number: "01", title: "数据源", copy: "权威文件数据", icon: Database, tint: "bg-[#e6ede5] text-[#416c58]" },
  { number: "02", title: "Skills 处理", copy: "结构化与清洗", icon: CodeXml, tint: "bg-[#e7edf7] text-[#4779bc]" },
  { number: "03", title: "Agent 分析", copy: "理解与提炼", icon: Bot, tint: "bg-[#f2ebdf] text-[#986f37]" },
  { number: "04", title: "生成内容", copy: "知识沉淀与输出", icon: FileText, tint: "bg-[#e5ece4] text-[#53715d]" },
  { number: "05", title: "前端展示", copy: "仅读取与展示", icon: Monitor, tint: "bg-[#e7edf7] text-[#3d70be]" },
];

export function PipelineStrip() {
  return (
    <>
      <Card className="px-6 py-5 lg:px-9">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-center">
          <div className="min-w-40">
            <p className="ink-title text-lg">文件数据流转</p>
            <p className="muted-copy mt-1 text-xs">Agent Pipeline</p>
          </div>
          <div className="flex flex-1 flex-wrap items-center justify-between gap-3">
            {steps.map((step, index) => {
              const Icon = step.icon;
              return (
                <div className="contents" key={step.title}>
                  <div className="flex items-center gap-4">
                    <span className={`flex size-14 items-center justify-center rounded-full ${step.tint}`}>
                      <Icon size={28} strokeWidth={1.7} />
                    </span>
                    <div>
                      <p className="label-sans text-[11px] text-[#68746e]">{step.number}</p>
                      <p className="mt-0.5 font-semibold text-[#293631]">{step.title}</p>
                      <p className="muted-copy mt-1 text-xs">{step.copy}</p>
                    </div>
                  </div>
                  {index < steps.length - 1 ? (
                    <MoveRight className="hidden text-[#858e89] lg:block" size={26} strokeWidth={1.3} />
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      </Card>
      <p className="pipeline-footnote label-sans flex items-center justify-center gap-2 py-4 text-sm text-[#737f79]">
        <span className="text-[#69776f]">◆</span>
        内容来自应用文件目录，页面仅作读取与展示，不直接调用采集或模型服务。
      </p>
    </>
  );
}
