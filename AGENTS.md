# 我要上岸项目协作规则

项目业务技能位于 `agents/skills/`。根据用户请求读取对应技能：

| 请求意图 | 技能文件 |
| --- | --- |
| “今日扫描”“扫一下今天”“更新今日时政和岗位” | `agents/skills/today-scan/SKILL.md` |
| “今日时政”“每日时政”“更新资讯” | `agents/skills/daily-news/SKILL.md` |
| “扫描岗位”“找我能报的岗位”“国考名单有了吗” | `agents/skills/job-scan/SKILL.md` |
| “补全申论”“补全行测”“整理技巧/学习路线” | `agents/skills/study-content/SKILL.md` |
| “建立画像”“修改个人信息”“根据我的条件找岗位” | `agents/skills/profile-intake/SKILL.md` |

`today-scan` 工作流同时处理：

1. 当日权威时政检索、原文链接验证和 `content/local/news/YYYY-MM-DD.json` 更新。
2. 岗位权威渠道扫描、用户画像匹配、岗位详情与公开参考指标整理，以及 `content/local/job/eligible-jobs.json` 更新。
3. 执行 `python scripts/today_scan.py --date YYYY-MM-DD` 完成结构校验和导出收口。

页面本身不启动扫描、不调用模型、不抓取外部网站。
