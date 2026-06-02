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

  if (roadmap.studyPrinciples) {
    lines.push("## 学习总原则", "");
    roadmap.studyPrinciples.forEach((principle) => {
      lines.push(`- ${principle.title}：${principle.detail}`);
    });
    lines.push("");
  }

  lines.push(`## ${formatStageHeading(roadmap.stages.length)}`, "");
  roadmap.stages.forEach((stage) => {
    lines.push(`### ${stage.title}`, "", `- 目标：${stage.goal}`, `- 周期：${stage.duration ?? "按需安排"}`, "");
    stage.tasks.forEach((task) => lines.push(`- ${task}`));
    if (stage.milestone) {
      lines.push("", `验收标志：${stage.milestone}`);
    }
    lines.push("");
  });

  if (roadmap.moduleGuides) {
    lines.push("## 模块训练工作台", "");
    roadmap.moduleGuides.forEach((module) => {
      lines.push(`### ${module.title}`, "", module.ability, "", `主题：${module.topics.join("、")}`, "", "方法：");
      module.methods.forEach((method) => lines.push(`- ${method}`));
      lines.push("", "易错点：");
      module.pitfalls.forEach((pitfall) => lines.push(`- ${pitfall}`));
      const teacherGroup = roadmap.teacherGroups?.find((group) => group.moduleId === module.id);
      if (teacherGroup) {
        lines.push("", "跟课老师：", "", teacherGroup.selectionNote, "");
        teacherGroup.teachers.forEach((teacher) => {
          lines.push(
            `#### ${teacher.name}`,
            "",
            `- 机构/来源：${teacher.institution ?? "按可获得课程资源选择"}`,
            `- 角色：${teacher.role}`,
            `- 阶段：${teacher.stage}`,
            `- 适合：${teacher.suitedFor}`,
            "",
            "怎么跟：",
          );
          teacher.howToUse.forEach((item) => lines.push(`- ${item}`));
          lines.push("", `注意：${teacher.caution}`);
          if (teacher.sourceUrl) {
            lines.push(`来源：[${teacher.sourceTitle ?? teacher.name}](${teacher.sourceUrl})`);
          }
          lines.push("");
        });
      }
      lines.push("");
    });
  }

  if (roadmap.teacherSelectionRules) {
    lines.push("## 选老师原则", "");
    roadmap.teacherSelectionRules.forEach((rule) => lines.push(`- [ ] ${rule}`));
    lines.push("");
  }

  if (roadmap.dailyExecution) {
    lines.push("## 每日执行模板", "");
    roadmap.dailyExecution.forEach((item) => {
      lines.push(`### ${item.period}：${item.focus}`, "");
      item.actions.forEach((action) => lines.push(`- [ ] ${action}`));
      lines.push("", `当日验收：${item.standard}`, "");
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

function formatStageHeading(count: number) {
  const labels: Record<number, string> = {
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
    10: "十",
  };

  return `${labels[count] ?? count}阶段训练路线`;
}
