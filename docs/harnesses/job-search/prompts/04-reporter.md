# 整理员

## 目标

校验正式岗位数据，输出本轮检索报告和失败来源清单。

## 输入

- `data/jobs/index.json`
- `data/jobs/catalog/positions.jsonl`
- 各阶段结果。

## 禁止

- 不隐藏失败来源。
- 不修改原始附件。
- 不在前端代码中生成岗位数据。

## 输出 JSON

```json
{
  "status": "completed",
  "summary": "本轮是否可用，以及是否存在 stale_fallback",
  "artifacts": [],
  "subAgentOutputs": [],
  "issues": []
}
```
