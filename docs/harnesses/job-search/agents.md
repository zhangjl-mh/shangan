---
name: job-search-agents
description: 岗位检索 Harness 的检索员、下载员、解析筛选员、整理员和可并行 sub agent 职责。需要拆分岗位检索 Agent 时使用。
---

# 岗位检索 Agent

岗位检索 Harness 使用轻角色，不让单个 Agent 背太多任务。

## 主 Agent

| Agent | 职责 | 禁止事项 |
| --- | --- | --- |
| 检索员 | 找官方公告、岗位表和报名入口，优先用户画像地区 | 不编造来源，不用论坛或二手整理替代官方来源 |
| 下载员 | 下载 `sources.json` 声明的官方附件并记录摘要 | 不改写附件，不下载非官方附件 |
| 解析员 | 确定性解析表格并输出失败片段 | 不补造字段，不直接调用模型 |
| 证据抽取员 | 只处理解析失败片段并保留原文坐标 | 不猜测、不绕过确定性解析 |
| 资格筛选员 | 按画像做严格三态筛选 | 不把未知画像当作符合 |
| 整理员 | 汇总正式 index/catalog、运行报告和失败清单 | 不修改原始附件，不隐藏失败来源 |

## 可并行 Sub Agent

| Sub Agent | 阶段 | 单一职责 |
| --- | --- | --- |
| 公务员来源检索员 | `01 collect` | 国考、北京、河北、天津公务员岗位表 |
| 事业单位来源检索员 | `01 collect` | 画像地区事业单位公告与岗位表 |
| 军队文职来源检索员 | `01 collect` | 军队文职全国入口与岗位表 |
| 国央企来源检索员 | `01 collect` | 国资委、央企和地方国企招聘入口 |
| 模型抽取员 | `03 parse-filter` | Python 解析失败的表格片段，只抽取有证据字段 |

Sub agent 不直接写正式数据。它们只返回结构化候选结果，由主 Harness 合并和验收。

## 输出约定

每个 Agent 返回 JSON：

```json
{
  "status": "completed",
  "summary": "一句话说明",
  "artifacts": [],
  "subAgentOutputs": [],
  "issues": []
}
```

允许状态：`completed`、`awaiting_review`、`has_bugs`。
