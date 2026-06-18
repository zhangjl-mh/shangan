---
name: job-search-harness
description: 处理岗位检索、下载、解析筛选和整理输出。用户提到岗位检索、岗位表、公务员、事业单位、军队文职、国央企或省考岗位时使用。
---

# 岗位检索 Harness

这是岗位检索专用 Harness，和通用八阶段 Harness 并列，按需加载。

| 内容 | 路径 |
| --- | --- |
| 机器入口 | [manifest.json](manifest.json) |
| 执行流程 | [workflow.md](workflow.md) |
| Agent 角色 | [agents.md](agents.md) |
| 阶段提示词 | [prompts/](prompts/) |

## CLI

```text
python scripts/job_search_harness.py all
python scripts/job_search_harness.py status <run-id>
python scripts/job_search_harness.py resume <run-id>
python scripts/job_search_harness.py validate <run-id>
```

运行记录写入 `docs/runs/job-search/<run-id>/`，正式岗位数据仍写入 `data/jobs/**`。
