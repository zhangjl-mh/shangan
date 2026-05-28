---
name: study-content
description: 为“上岸”补充或更新申论、行测学习内容。当用户说“补全申论”“补全行测”“整理技巧”“增加题型方法”“做学习路线”“参考考公机构丰富内容”或要求页面学习材料更完整时，务必使用此技能：结合官方大纲与可追溯公开培训资料，更新结构化学习 JSON 并验证前端展示与导出。
---

# 申论与行测内容维护

## 数据边界

更新内容文件：

```txt
content/local/shenlun/roadmap.json
content/local/xingce/roadmap.json
```

可参考已有基础库：

```txt
content/library/shenlun/roadmap.json
content/library/xingce/roadmap.json
```

前端只消费本地数据，内容整理在 Agent/Skill 阶段完成。

## 资料原则

1. 考试范围、考试时长、科目结构等事实优先以官方招考大纲或官方公告为依据。
2. 答题技巧、训练方法和常见结构可以参考公开考公机构资料，但必须保留资料标题、发布者、URL 与访问日期。
3. 不将机构经验写成官方评分规则，不编造题目来源或所谓内部标准。
4. 用户需要“齐全”时，优先补齐结构覆盖和可执行方法，而不是重复铺陈表述。

## 申论更新

读取 `agents/schema/shenlun-roadmap.schema.json`，至少维护：

```txt
考试依据与试卷能力说明
七阶段学习路线与输出成果
归纳概括、综合分析、提出对策、贯彻执行、申发论述题型方法
材料阅读、要点加工、规范表达、文章结构、训练与复盘
references 信源列表
```

## 行测更新

读取 `agents/schema/xingce-roadmap.schema.json`，至少维护：

```txt
考试说明、训练阶段
政治理论、常识判断、言语理解、数量关系、判断推理、资料分析
各模块方法、典型陷阱、速度策略、错题复盘
公式或速算卡片、考场时间方案、references 信源列表
```

## 验证

更新 JSON 后检查 Schema 结构，执行：

```bash
npm run typecheck
npm run build
```

同时核对 `/shenlun`、`/xingce` 页面和 Markdown 导出接口能够读取新增内容。
