# AGENTS.md

## 项目概述

**我要上岸** — 公务员考试备考助手，核心能力：学习路线推荐、岗位筛选、每日时政资讯。

---

## 目录结构

├── AGENTS.md                     # 管规则：项目总规范、协作边界、执行流程
│
├── docs /                      # *项目文档与需求产物*
│   ├── README.md                 # Harness 总说明
│   ├── workflow.md               # 标准执行流程
│   ├── checks.md                 # 校验规则
│   └── templates/                # 系统架构说明
│
├── .agents/                      # Agent 配置
│   └── skills/                   # 管能力：业务技能层
│       ├── SKILL.md              # 技能路由入口
│       ├── daily-news/           # 每日时政
│       │   ├── SKILL.md
│       │   ├── examples.md
│       │   └── scripts/
│       ├── study-route/          # 行测 / 申论学习路线
│       │   ├── SKILL.md
│       │   ├── examples.md
│       │   └── scripts/
│       ├── study-content/        # 知识点、技巧、课程内容整理
│       │   ├── SKILL.md
│       │   ├── examples.md
│       │   └── scripts/
│       └── job-filter/           # 岗位筛选
│           ├── SKILL.md
│           ├── examples.md
│           └── scripts/

│
├── schemas/                      # 管格式：数据结构契约
│   ├── user-profile.schema.json
│   ├── xingce-route.schema.json
│   ├── shenlun-route.schema.json
│   ├── daily-news.schema.json
│   └── job-filter.schema.json
│
├── data/                         # 管内容：正式业务数据
│   ├── user-profile/             # 用户画像
│   ├── xingce/                   # 行测数据
│   ├── shenlun/                  # 申论数据
│   ├── daily-news/               # 每日时政
│   └── jobs/                     # 岗位数据
│
└── app/                          # 管展示：前端页面和组件
    ├── pages/
    ├── components/               # 公共组件
    ├── services/                 # 数据读取服务
    ├── hooks/                    # 通用逻辑
    └── types/                    # 前端类型

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
