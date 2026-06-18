# Agent Handoff

每阶段结束时原样输出：

```text
---AGENT-HANDOFF---
requirement-id:   REQ-{id}
agent:            {当前 Agent}
status:           completed | awaiting_review | has_bugs | all_passed
output:           {产物路径}
issues:           {问题描述，无则填 none}
next-agent:       {下一个 Agent}
next-step-prompt: {下一个 Agent 的启动提示词}
---END-HANDOFF---
```

需要持久化交接时，同时生成符合 `schemas/agent-handoff.schema.json` 的 JSON。
