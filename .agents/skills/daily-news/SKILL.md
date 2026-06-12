---
name: daily-news
description: 生成、更新或补录每日时政。当用户提到今日时政、每日资讯、更新新闻或指定日期补录时使用。
---

# 每日时政

1. 读取 `schemas/daily-news.schema.json`、当天和前一天 JSON。
2. 仅使用权威原文，按 `Asia/Shanghai` 确认发布日期。
3. 核验标题、来源、URL 和事实；无法核验的不写入。
4. 与前一天按 URL、标题和事件去重。
5. 写入 `data/daily-news/YYYY-MM-DD.json`。
6. 执行：

```bash
python .agents/skills/daily-news/scripts/today_scan.py --date YYYY-MM-DD
```

脚本校验 JSON 后生成 `data/daily-news/markdown/YYYY-MM-DD.md`。失败时不生成
Markdown，并回报失败环节与文件。
