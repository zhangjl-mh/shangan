# AGENTS.md

## 项目概述

**我要上岸** — 公务员考试备考助手，核心能力：学习路线推荐、岗位筛选、每日时政资讯。

---

## 目录结构

| 目录              | 职责                         | 详细规范                  |
| ----------------- | ---------------------------- | ------------------------- |
| `docs/`           | Harness 编排、流程与校验规则 | `docs/README.md`          |
| `.agents/skills/` | 业务技能路由与执行脚本       | `.agents/skills/SKILL.md` |
| `schemas/`        | 数据结构契约                 | `schemas/` 各文件         |
| `data/`           | 正式业务数据                 | `docs/workflow.md`        |
| `app/`            | 前端页面与组件               | `app/` 各页面 README      |
| `scripts/`        | 项目级校验与维护脚本         | `docs/checks.md`          |

---

## Agent 流水线

```
需求确认 → 数据处理 → 数据校验 → 前端调整 → 结构校验 → 测试 → 完成
```

详细执行规范见 `docs/workflow.md`，校验规则见 `docs/checks.md`。

---

## HANDOFF 协议

每个 Agent 完成后必须输出：

```
---AGENT-HANDOFF---
requirement-id:   REQ-{id}
agent:            {当前 Agent}
status:           completed | awaiting_review | has_bugs | all_passed
output:           {产物路径}
issues:           {问题描述，无则填 none}
next-agent:       {下一个 Agent}
next-step-prompt: {下一个 Agent 的启动提示词}
---END-HANDOFF---
```
