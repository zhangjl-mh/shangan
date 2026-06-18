---
name: job-search-workflow
description: 岗位检索 Harness 的四步流程、轻循环、命令和产物。需要执行岗位检索流程时使用。
---

# 岗位检索 Harness

这是岗位检索专用 Harness，和 `docs/harnesses/eight-stage/manifest.json`
定义的八阶段 Harness 并列。
它只在岗位检索需求中按需加载，不处理学习路线、每日时政或前端调整。

## 四步

1. `collect`：检索官方来源，先看用户画像地区，再补全国入口。
2. `download`：下载官方附件；下载失败时，允许沿用上一次成功数据并标记
   `stale_fallback`。
3. `parse-filter`：Python 先解析，失败表格交给模型抽取员；筛选必须输出
   `eligible`、`needs_confirmation` 或 `ineligible`。
4. `report`：写正式岗位索引、岗位目录和本轮报告。

## 轻循环

- 每个阶段只做一件事，失败只重跑失败阶段。
- 最多重试 3 轮。
- 仍失败时保留已可用的旧数据，状态为 `awaiting_review` 或 `has_bugs`。
- 运行记录写入 `docs/runs/job-search/<run-id>/`，正式数据仍只写
  `data/jobs/**`。

## 命令

```bash
python scripts/job_search_harness.py all
python scripts/job_search_harness.py status <run-id>
python scripts/job_search_harness.py resume <run-id>
python scripts/job_search_harness.py validate <run-id>
```

## 产物

- `data/jobs/index.json`
- `data/jobs/catalog/positions.jsonl`
- `docs/runs/job-search/<run-id>/job-search-report.json`
- `docs/runs/job-search/<run-id>/execution.json`
