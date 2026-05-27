import type { StudyRoadmap, XingceRoadmap } from "@/lib/types";

export function renderShenlunMarkdown(roadmap: StudyRoadmap) {
  const lines: string[] = [
    `# ${roadmap.title}`,
    "",
    roadmap.description,
    "",
  ];

  if (roadmap.basisNote) {
    lines.push("## 使用说明", "", roadmap.basisNote, "");
  }

  if (roadmap.examGuide) {
    lines.push(
      "## 考试依据与能力地图",
      "",
      `- 依据：${roadmap.examGuide.syllabusTitle}`,
      `- 发布日期：${roadmap.examGuide.syllabusDate}`,
      `- 时限：${roadmap.examGuide.durationMinutes} 分钟`,
      `- 满分：${roadmap.examGuide.score} 分`,
      `- 原文：${roadmap.examGuide.syllabusUrl}`,
      "",
      roadmap.examGuide.notice,
      "",
    );

    for (const paper of roadmap.examGuide.paperTypes) {
      lines.push(`### ${paper.title}`, "", paper.focus, "");
      for (const ability of paper.abilities) {
        lines.push(`- ${ability}`);
      }
      lines.push("");
    }
  }

  lines.push("## 七阶段学习路线", "");
  for (const stage of roadmap.stages) {
    lines.push(`### ${stage.title}`, "", `- 目标：${stage.goal}`, `- 周期：${stage.duration ?? "按需安排"}`, "");
    for (const task of stage.tasks) {
      lines.push(`- ${task}`);
    }
    if (stage.milestone) {
      lines.push("", `验收标志：${stage.milestone}`);
    }
    lines.push("");
  }

  if (roadmap.coreWorkflow) {
    lines.push("## 通用六步作答流程", "");
    for (const step of roadmap.coreWorkflow) {
      lines.push(`### ${step.title}`, "", step.purpose, "");
      for (const action of step.actions) {
        lines.push(`- ${action}`);
      }
      lines.push("", `产出：${step.output}`, "");
    }
  }

  if (roadmap.questionTypes) {
    lines.push("## 五大题型技法", "");
    for (const question of roadmap.questionTypes) {
      lines.push(`### ${question.title}：${question.subtitle}`, "", question.coreGoal, "", "作答结构：");
      question.answerFramework.forEach((item) => lines.push(`- ${item}`));
      lines.push("", "找点与加工：");
      question.pointMethods.forEach((item) => lines.push(`- ${item}`));
      lines.push("", "易错点：");
      question.pitfalls.forEach((item) => lines.push(`- ${item}`));
      lines.push("");
    }
  }

  if (roadmap.documentTypes) {
    lines.push("## 应用文文种库", "");
    for (const item of roadmap.documentTypes) {
      lines.push(`### ${item.title}`, "", `- 对象：${item.audience}`, `- 重点：${item.focus}`, "- 结构：");
      item.structure.forEach((structure) => lines.push(`  - ${structure}`));
      lines.push("");
    }
  }

  if (roadmap.examTiming) {
    lines.push("## 考场时间分配参考", "");
    roadmap.examTiming.forEach((item) => {
      lines.push(`- ${item.phase}（${item.minutes}）：${item.action}`);
    });
    lines.push("");
  }

  if (roadmap.reviewChecklist) {
    lines.push("## 复盘清单", "");
    roadmap.reviewChecklist.forEach((group) => {
      lines.push(`### ${group.category}`, "");
      group.items.forEach((item) => lines.push(`- [ ] ${item}`));
      lines.push("");
    });
  }

  if (roadmap.references) {
    lines.push("## 参考来源", "");
    roadmap.references.forEach((reference) => {
      lines.push(`- [${reference.title}](${reference.url}) - ${reference.publisher}（访问日期：${reference.accessedAt}）`);
    });
    lines.push("");
  }

  return lines.join("\n");
}

export function renderXingceMarkdown(roadmap: XingceRoadmap) {
  const lines: string[] = [`# ${roadmap.title}`, "", roadmap.description, ""];

  if (roadmap.basisNote) {
    lines.push("## 使用说明", "", roadmap.basisNote, "");
  }

  if (roadmap.examProfile) {
    const profile = roadmap.examProfile;
    lines.push(
      "## 官方大纲口径",
      "",
      `- 依据：${profile.syllabusTitle}`,
      `- 发布日期：${profile.syllabusDate}`,
      `- 题型属性：${profile.questionNature}`,
      `- 时限：${profile.durationMinutes} 分钟`,
      `- 满分：${profile.score} 分`,
      `- 原文：${profile.syllabusUrl}`,
      "",
      `官方测查板块：${profile.officialModules.join("、")}`,
      "",
    );
  }

  lines.push("## 六阶段训练路线", "");
  roadmap.stages.forEach((stage) => {
    lines.push(`### ${stage.title}`, "", `- 目标：${stage.goal}`, `- 周期：${stage.duration ?? "按需安排"}`, "");
    stage.tasks.forEach((task) => lines.push(`- ${task}`));
    if (stage.milestone) {
      lines.push("", `验收标志：${stage.milestone}`);
    }
    lines.push("");
  });

  if (roadmap.moduleGuides) {
    lines.push("## 专项模块方法", "");
    roadmap.moduleGuides.forEach((module) => {
      lines.push(`### ${module.title}`, "", module.ability, "", `主题：${module.topics.join("、")}`, "", "方法：");
      module.methods.forEach((method) => lines.push(`- ${method}`));
      lines.push("", "易错点：");
      module.pitfalls.forEach((pitfall) => lines.push(`- ${pitfall}`));
      lines.push("");
    });
  }

  if (roadmap.formulaCards) {
    lines.push("## 速算与关系卡", "");
    roadmap.formulaCards.forEach((card) => {
      lines.push(`### ${card.title}`, "");
      card.rules.forEach((rule) => lines.push(`- ${rule}`));
      lines.push("");
    });
  }

  if (roadmap.timePlan) {
    lines.push("## 考场节奏", "");
    roadmap.timePlan.forEach((phase) => lines.push(`- ${phase.phase}（${phase.target}）：${phase.method}`));
    lines.push("");
  }

  if (roadmap.references) {
    lines.push("## 参考来源", "");
    roadmap.references.forEach((reference) => {
      lines.push(`- [${reference.title}](${reference.url}) - ${reference.publisher}（访问日期：${reference.accessedAt}）`);
    });
    lines.push("");
  }

  return lines.join("\n");
}
