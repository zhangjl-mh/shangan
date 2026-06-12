# Harness 规范

`docs/` 是项目 Harness 的唯一入口，负责八阶段编排、写入策略、阶段提示词、校验规则和交付模板。

| 路径 | 内容 |
| --- | --- |
| [manifest.json](manifest.json) | Harness 机器入口与阶段配置 |
| [workflow.md](workflow.md) | 八阶段流程、跳转和完成条件 |
| [checks.md](checks.md) | 项目校验命令与状态判定 |
| [prompts/](prompts/) | 各阶段执行提示词 |
| [policies/](policies/) | 写入所有权策略 |
| [templates/](templates/) | 需求、交接和验收模板 |
| [architecture.md](architecture.md) | 项目分层与职责边界 |
| [migration-report.md](migration-report.md) | 历史迁移记录 |

## 职责边界

- `docs/` 管流程，`.agents/skills/` 管业务能力，`schemas/` 管格式，`data/` 管正式内容，`app/` 管展示。
- `scripts/validate_project.py` 是跨目录的项目级质量门禁，因此保留在根 `scripts/`。
- 只服务单个业务能力的采集或处理脚本，放在对应 `.agents/skills/<skill>/scripts/`。
- Harness 运行记录写入 `docs/runs/<execution-id>/execution.json`，按
  `schemas/harness-execution.schema.json` 校验；`docs/runs/` 不进入版本管理。
