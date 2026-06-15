# AGENTS.md

## 项目概述

**我要上岸**是一个公务员考试备考助手。Agent 负责生成和维护业务数据，
Next.js 应用负责读取本地数据并展示。

核心能力：

- 行测、申论学习路线与老师推荐
- 公务员、事业单位和国企岗位采集与筛选
- 每日时政资讯整理
- 行测、申论知识点与训练内容维护

## 权威入口

| 内容 | 权威文件 |
| --- | --- |
| Harness 机器配置 | `docs/manifest.json` |
| 执行流程 | `docs/workflow.md` |
| 校验规则 | `docs/checks.md` |
| 架构与职责边界 | `docs/architecture.md` |
| 业务 Skill 路由 | `.agents/skills/SKILL.md` |
| 前端规范 | `app/README.md` |
| 数据结构 | `schemas/*.schema.json` |

规则冲突时，优先遵循更具体目录中的说明和对应 Schema。

## 目录结构

```text
├── AGENTS.md                         # 项目总规范、协作边界与执行流程
├── README.md                         # 项目简介与常用命令
│
├── docs/                             # Harness 编排、流程与校验规则
│   ├── README.md                     # Harness 使用说明
│   ├── manifest.json                 # 八阶段机器配置入口
│   ├── architecture.md               # 项目分层与职责边界
│   ├── workflow.md                   # 八阶段标准流程
│   ├── checks.md                     # 项目校验规则与命令
│   ├── prompts/                      # 各阶段执行提示词
│   ├── policies/                     # 写入所有权等执行策略
│   ├── templates/                    # 需求、交接与验收模板
│   └── runs/                         # Harness 运行记录，不属于正式数据
│
├── .agents/
│   └── skills/                       # 业务 Skill 路由与执行脚本
│       ├── SKILL.md                  # 业务 Skill 总路由
│       ├── daily-news/               # 每日时政采集、整理与补录
│       │   ├── SKILL.md
│       │   └── scripts/
│       ├── study-route/              # 行测、申论学习路线与老师推荐
│       │   ├── SKILL.md
│       │   └── scripts/
│       ├── study-content/            # 知识点、题型方法与训练技巧
│       │   ├── SKILL.md
│       │   └── scripts/
│       └── job-filter/               # 岗位采集、更新与筛选
│           ├── SKILL.md
│           └── scripts/
│
├── schemas/                          # JSON 数据结构契约
│   ├── user-profile.schema.json      # 用户画像
│   ├── xingce-route.schema.json      # 行测学习路线
│   ├── shenlun-route.schema.json     # 申论学习路线
│   ├── daily-news.schema.json        # 每日时政
│   ├── job-filter.schema.json        # 岗位数据
│   ├── agent-handoff.schema.json     # Agent 交接记录
│   ├── harness-execution.schema.json # Harness 执行记录
│   └── acceptance-report.schema.json # 最终验收报告
│
├── data/                             # 前端消费的正式业务数据
│   ├── user-profile/                 # 用户画像
│   ├── xingce/                       # 行测学习数据
│   ├── shenlun/                      # 申论学习数据
│   ├── daily-news/                   # 每日时政 JSON 与 Markdown
│   └── jobs/                         # 岗位来源、索引与职位目录
│
├── app/                              # Next.js App Router 前端
│   ├── page.tsx                      # 首页
│   ├── layout.tsx                    # 全局布局
│   ├── globals.css                   # 全局样式
│   ├── xingce/                       # 行测学习路线页面
│   ├── shenlun/                      # 申论学习路线页面
│   ├── news/                         # 每日时政页面
│   ├── jobs/                         # 岗位列表与筛选页面
│   ├── job/                          # 岗位相关页面
│   ├── api/                          # 岗位与内容导出接口
│   ├── components/                   # 公共组件
│   ├── services/                     # 本地数据读取服务
│   └── types/                        # 前端共享类型
│
├── public/                           # 前端静态资源
├── scripts/                          # 项目级 Harness 与校验脚本
│   ├── harness.py                    # Harness CLI
│   └── validate_project.py           # 项目结构与数据校验
├── tests/                            # Node.js 与 Python 自动化测试
└── deliverables/                     # 独立交付产物，非正式业务数据源
```

## Skill 路由

处理业务请求前先读取 `.agents/skills/SKILL.md`，再按任务选择对应 Skill：

| 请求 | Skill |
| --- | --- |
| 每日资讯、今日时政、指定日期补录 | `.agents/skills/daily-news/SKILL.md` |
| 行测、申论学习顺序与老师推荐 | `.agents/skills/study-route/SKILL.md` |
| 知识点、题型方法、训练技巧与复盘 | `.agents/skills/study-content/SKILL.md` |
| 岗位采集、更新与条件筛选 | `.agents/skills/job-filter/SKILL.md` |

## Agent 流水线

所有正式需求按 `docs/manifest.json` 定义的八阶段执行：

```text
01 需求确认
  -> 02 数据处理
  -> 03 数据校验
  -> 04 前端调整
  -> 05 结构校验
  -> 06 测试
  -> 07 自动修复
  -> 08 最终验收
```

- 01 至 06 顺序执行，不需要的阶段也要说明跳过原因。
- 03、05、06 任一失败时进入 07，修复后回跑 03、05、06。
- 自动修复最多 3 轮；仍失败则最终状态为 `has_bugs`。
- 只有 03、05、06 最新结果全部通过，08 才能输出 `all_passed`。
- Harness CLI 入口为 `python scripts/harness.py`，运行记录写入
  `docs/runs/<execution-id>/`。

## 修改边界

- 每项需求必须明确 `ownedPaths` 与 `excludedPaths`；未授权路径默认只读。
- `schemas/` 定义契约，`data/` 保存正式数据，`app/` 只负责消费和展示。
- 前端不得抓取外部数据、调用模型或生成正式业务数据。
- 公共组件放在 `app/components/`，页面专属组件放在对应路由的
  `components/`。
- 数据读取逻辑放在 `app/services/`，共享类型放在 `app/types/`。
- 项目级脚本放在 `scripts/`；单个业务能力的脚本放在对应
  `.agents/skills/<skill>/scripts/`。
- 正式 JSON 必须符合对应 Schema，不得包含占位值、临时字段或失效路径。
- 不得把 `docs/runs/`、缓存、构建产物或临时下载文件混入正式数据。
- 保留用户已有改动；不要回退、覆盖或清理与当前需求无关的文件。

## 校验与测试

按改动范围执行适用命令：

```bash
npm run validate:project
npm run lint
npm run typecheck
npm test
npm run build
```

完整校验：

```bash
npm run check
```

Harness 专项校验：

```bash
python -m unittest tests.test_harness
python scripts/harness.py validate <execution-id>
```

命令未执行、执行失败或缺少验证证据时，不得声明 `all_passed`。

## HANDOFF 协议

每个 Agent 或 Harness 阶段结束后必须输出：

```text
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

需要持久化时，同时生成符合 `schemas/agent-handoff.schema.json` 的 JSON。
