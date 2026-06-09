# 我要上岸项目协作规则

## 项目说明

“我要上岸”是一个备考学习项目，Agent 负责生成和更新数据，Next.js 只负责页面展示。

核心规则：

* 数据统一放在 `data/`。
* Next.js 不抓取网站、不调用模型、不生成业务数据。
* Agent 根据用户请求读取对应 Skill，生成结构化 JSON / Markdown。
* 所有生成结果必须能被前端直接读取。

## 目录规范

```txt
agents/
└── skills/
    └── daily-news/
        ├── SKILL.md
        ├── schema.json
        ├── examples.md
        └── scripts/
            └── scan.py

data/
├── news/
│   └── YYYY-MM-DD.json
├── markdown/
│   └── YYYY-MM-DD-daily-news.md
└── study/
    ├── shenlun.json
    ├── xingce.json
    └── roadmap.json
```

## Skill 格式

每个 Skill 必须放在 `agents/skills/` 下，一个 Skill 一个目录。

`SKILL.md` 必须使用标准格式：

```md
---
name: daily-news
description: 当用户要求生成、更新、补齐每日时政材料时使用本技能。
---

# 每日时政

技能说明和执行规则写在这里。
```

注意：

* frontmatter 开头和结尾都是 `---`。
* 不要使用长横线。
* `name` 简短稳定。
* `description` 写清楚触发场景。

## 技能调用

| 用户请求                               | 使用 Skill                              |
| -------------------------------------- | --------------------------------------- |
| 今日扫描、今日时政、每日时政、更新资讯 | `agents/skills/daily-news/SKILL.md`     |
| 补齐某天/某段日期时政                  | `agents/skills/daily-news/SKILL.md`     |
| 补全申论、整理申论技巧                 | `agents/skills/study-content/SKILL.md`  |
| 补全行测、整理行测技巧                 | `agents/skills/study-content/SKILL.md`  |
| 生成学习计划、本周怎么学               | `agents/skills/study-plan/SKILL.md`     |
| 错题复盘、分析薄弱点                   | `agents/skills/mistake-review/SKILL.md` |

## 每日时政规则

触发 `daily-news` 时：

1. 默认扫描今天和昨天。
2. 日期按 `Asia/Shanghai` 处理。
3. 只采集权威原文。
4. 昨天已存在的资讯，今天不重复写入。
5. 不用旧闻凑数。
6. 不使用转载页、聚合页、搜索结果页作为原文。
7. 输出到：

```txt
data/news/YYYY-MM-DD.json
data/markdown/YYYY-MM-DD-daily-news.md
```

执行命令：

```bash
python scripts/today_scan.py --date YYYY-MM-DD
```

## 子 Agent

| 子 Agent             | 职责                                                |
| -------------------- | --------------------------------------------------- |
| main-agent           | 判断用户意图，选择 Skill，汇总结果                  |
| news-scan-agent      | 扫描每日时政，生成 `data/news/` 和 `data/markdown/` |
| study-content-agent  | 整理申论、行测、学习路线                            |
| study-plan-agent     | 生成每日/每周学习计划                               |
| mistake-review-agent | 整理错题和薄弱点                                    |
| data-guard-agent     | 校验 JSON、Markdown 和数据目录                      |

## 数据写入规则

* 只写入 `data/`。
* 不把正式数据写进 `src/`、`app/`、`components/`。
* 不把扫描日志、候选池、调试信息暴露给前端。
* JSON 字段要稳定。
* Markdown 必须由 JSON 生成。
* 更新旧数据前先读取旧文件并去重。

## 前端规则

Next.js 只读取 `data/`：

```txt
data/news/YYYY-MM-DD.json
data/study/shenlun.json
data/study/xingce.json
data/study/roadmap.json
```

前端只负责：

* 展示数据
* 分类筛选
* 搜索
* 页面交互

前端禁止：

* 抓取外部新闻
* 调用模型
* 执行扫描脚本
* 硬编码正式业务数据

## 禁止事项

* 不编造新闻标题、日期、来源、URL。
* 不用旧闻冒充今日资讯。
* 不跳过 Schema 校验。
* 不生成与 JSON 不一致的 Markdown。
* 不让页面承担数据生产任务。
