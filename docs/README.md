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

## Harness CLI

入口为 `python scripts/harness.py`，配置来源固定为 `docs/manifest.json`。

```text
python scripts/harness.py init --requirement requirement.json --execution-id REQ-001-run
python scripts/harness.py run REQ-001-run
python scripts/harness.py resume REQ-001-run
python scripts/harness.py status REQ-001-run
python scripts/harness.py validate REQ-001-run
```

`init` 也可直接使用 `--id`、`--title`、`--objective`、重复的
`--owned-path` 与 `--excluded-path`。每次运行在 `docs/runs/<execution-id>/`
保存 `requirement.json`、`execution.json`、阶段 prompts、runner 日志、handoffs
和写入审计 evidence。

默认 runner 为：

```text
codex.cmd exec --json --output-schema <handoff-schema> --output-last-message <handoff>
```

测试或本地集成可通过 `--runner "<command>"` 或 `HARNESS_RUNNER` 注入 runner。
runner 会收到 `HARNESS_ROOT`、`HARNESS_EXECUTION_ID`、`HARNESS_EXECUTION_DIR`、
`HARNESS_WORKING_DIRECTORY`、`HARNESS_STAGE_ID` 和 `HARNESS_REPAIR_ROUND`
环境变量，并必须向
`--output-last-message` 指定路径写入符合 Agent Handoff Schema 的 JSON。
