# 验收报告

- `requirement-id`: REQ-{id}
- `status`: all_passed | has_bugs | awaiting_review
- `summary`: {结论}

## 标准

| ID | 结果 | 证据 |
| --- | --- | --- |
| AC-01 | passed / failed | {文件、命令或记录} |

## 检查

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| {名称} | passed / failed | {命令与退出码} |

## 问题

{无则填 none}

持久化报告必须符合 `schemas/acceptance-report.schema.json`；仅全部结果为 `passed` 时状态可为 `all_passed`。
