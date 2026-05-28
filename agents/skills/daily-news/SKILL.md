---
name: daily-news
description: 为“上岸”生成或更新每日时政数据。当用户说“今日时政”“每日时政”“今日资讯”“检索今天的新闻”“更新资讯”或要求按日期补齐时政材料时，务必使用此技能：只采集指定日期的权威原文，验证链接，整理申论与行测备考角度，并写入前端可读 JSON/Markdown。
---

# 每日时政

## 输出

以扫描日期 `YYYY-MM-DD` 为准，更新：

```txt
content/local/news/YYYY-MM-DD.json
content/local/markdown/YYYY-MM-DD-daily-news.md
```

页面只读取生成文件，不在浏览器中联网抓取或调用模型。

## 执行步骤

1. 明确扫描日期，按 `Asia/Shanghai` 的自然日处理“今日”。向用户回报时使用绝对日期。
2. 读取 `agents/schema/daily-news.schema.json` 和当天已有 JSON；已有条目也要重新核对原文链接、发布时间和日期归属。
3. 从权威原始渠道检索当天发布的内容，优先使用中国政府网、国务院部门官网、新华社/新华网、人民日报/人民网、求是网以及事件主管部门官网。
4. 先建立 `candidateSources` 与 `candidatePool`：所有实际检索过的权威入口都要记录，所有符合日期且原文可访问的候选资讯都要进入候选池。
5. 阅读候选资讯原文后，按政策性、治理性、申论可加工度、行测常识关联度和公共服务价值，选取最适合备考的 5 篇写入 `items`。不足 5 篇时保留真实数量，不用旧闻填充。
6. 对纳入 `items` 的每一条资讯实际访问原文 URL。仅保留来源、标题、发布时间和事件事实能够从原文确认的条目。
7. 以备考加工信息补充 `policyBackground`、`shenlunAngles`、`xingceLinks`、`materials` 和 `examQuestions`；这些内容必须与原文事实区分清楚，不写成官方表述。
8. 写入 JSON，并校验 Schema。若岗位报告文件已存在，执行 `python scripts/today_scan.py --date YYYY-MM-DD` 生成 Markdown 与扫描清单；否则先保留已校验 JSON，说明需要岗位数据才能运行组合收口脚本。

## 内容标准

- 当天没有足够可核验资讯时，保留真实数量，不拿旧闻冒充今日资讯。
- 不编造标题、日期、来源或 URL，不将转载聚合页冒充官方原文。
- 主题优先关注政策部署、基层治理、法治、公共服务、经济运行、科技与公共安全。
- 每条 `verification` 应说明核验时间和原文可达状态。
- `candidatePool` 中 `selected=true` 的条目必须与 `items` 对齐；未选条目要写明未进入前五的原因。

## 回报

向用户说明扫描日期、收录条数、主要官方来源、输出文件，以及无法核验或未纳入的情况。
