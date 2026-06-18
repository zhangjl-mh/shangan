---
name: eight-stage-architecture
description: 八阶段 Harness 的项目分层、职责边界和正式数据流向。需要判断写入边界或架构责任时使用。
---

# 架构

```text
AGENTS.md / docs        规则与说明
        ↓
docs/harnesses/eight-stage/manifest.json
                        8 阶段编排入口
        ↓
.agents/skills         业务执行规则
        ↓
schemas → data → app   契约、数据、展示
```

## 边界

- Harness 只负责编排、状态和证据，不复制业务 Skill。
- `schemas/` 是结构契约，`data/` 是正式数据，`app/` 只消费本地数据。
- 每项需求必须声明 `ownedPaths` 与 `excludedPaths`；未授权路径默认只读。
- 项目级脚本放 `scripts/`，单个 Skill 的专用脚本放其自身 `scripts/`。
- 运行记录写入 `docs/runs/<execution-id>/execution.json`，不得混入正式数据。
