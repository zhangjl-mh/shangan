# 架构

```text
AGENTS.md / docs        规则与说明
        ↓
.agents/harness        8 阶段编排、写入策略、提示词
        ↓
.agents/skills         业务执行规则
        ↓
schemas → data → app   契约、数据、展示
```

## 边界

- Harness 只负责编排、状态和证据，不复制业务 Skill。
- `schemas/` 是结构契约，`data/` 是正式数据，`app/` 只消费本地数据。
- 每项需求必须声明 `ownedPaths` 与 `excludedPaths`；未授权路径默认只读。
- 运行记录写入 `.agents/harness/runs/<execution-id>/`，不得混入正式数据。
