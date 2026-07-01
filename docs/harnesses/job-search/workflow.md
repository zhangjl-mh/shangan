---
name: job-search-workflow
description: 岗位检索 Harness 的六阶段流程、Agent 产物门禁、命令和产物。
---

# 岗位检索 Harness

## 六阶段

1. `collect`：Agent 检索官方来源并提交带证据的候选；无提交时暂停。
2. `download`：只下载来源清单声明且域名已注册的官方附件。
3. `parse`：确定性解析附件，输出标准化岗位和失败片段。
4. `extract`：仅在存在失败片段时等待证据抽取 Agent；否则明确跳过。
5. `filter`：按画像做严格三态判断，通过发布保护后写正式目录。
6. `report`：校验 Index、逐行 Schema、摘要、计数和来源覆盖。

## 门禁与恢复

- Agent 阶段没有提交时执行状态为 `paused`。
- 使用
  `python scripts/job_search_harness.py submit <run-id> <stage-id> <result-json>`
  提交结构化结果，再使用 `resume`。
- Sub Agent 只返回候选和证据，不直接写正式数据。
- 失败阶段最多重试 3 轮；下载失败可使用已校验的上次产物并标记
  `stale_fallback`。

## 正式产物

- `data/jobs/index.json`
- `data/jobs/catalog/eligible.jsonl`
- `data/jobs/catalog/needs-confirmation.jsonl`
- `docs/runs/job-search/<run-id>/job-search-report.json`
