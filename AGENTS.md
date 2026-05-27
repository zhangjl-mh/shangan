# 我要上岸项目协作规则

当用户在本项目中提出“今日扫描”“扫一下今天”“更新今日时政和岗位”或同义请求时，读取并执行 `agents/skills/today-scan/SKILL.md`。

该工作流同时处理：

1. 当日权威时政检索、原文链接验证和 `content/local/news/YYYY-MM-DD.json` 更新。
2. 岗位权威渠道扫描、用户画像匹配、岗位详情与公开参考指标整理，以及 `content/local/job/eligible-jobs.json` 更新。
3. 执行 `python scripts/today_scan.py --date YYYY-MM-DD` 完成结构校验和导出收口。

页面本身不启动扫描、不调用模型、不抓取外部网站。
