---
name: shangan-router
description: 路由“我要上岸”项目任务。当用户要求学习路线、岗位筛选、每日资讯或学习内容维护时，先读取本入口。
---

# 项目路由

| 请求 | Skill |
| --- | --- |
| 每日资讯、今日时政 | `.agents/skills/daily-news/SKILL.md` |
| 行测、申论完整学习路线和老师推荐 | `.agents/skills/study-route/SKILL.md` |
| 知识点、题型与技巧补全 | `.agents/skills/study-content/SKILL.md` |
| 岗位采集与筛选 | `.agents/skills/job-filter/SKILL.md` |

确认需求后按 `.agents/harness/manifest.json` 执行流水线。
