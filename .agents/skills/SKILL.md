---
name: shangan-router
description: 路由“我要上岸”项目任务并选择业务 Skill 与 Harness。用户提到学习路线、岗位检索、每日资讯、学习内容维护或项目流程时先读取本入口。
---

# 项目路由

| 请求 | Skill |
| --- | --- |
| 每日资讯、今日时政 | `.agents/skills/daily-news/SKILL.md` |
| 行测、申论完整学习路线和老师推荐 | `.agents/skills/study-route/SKILL.md` |
| 知识点、题型与技巧补全 | `.agents/skills/study-content/SKILL.md` |
| 岗位采集与筛选 | `.agents/skills/job-filter/SKILL.md` |

确认需求后先读 `docs/README.md` 选择 Harness；普通正式需求按
`docs/harnesses/eight-stage/manifest.json` 执行，岗位检索需求可按需加载
`docs/harnesses/job-search/manifest.json`。
