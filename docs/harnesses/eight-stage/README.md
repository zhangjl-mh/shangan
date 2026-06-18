---
name: eight-stage-harness
description: 执行“我要上岸”项目通用八阶段流程。用户提出正式需求、跨模块改动、数据维护、前端调整、校验测试或最终验收时使用。
---

# 八阶段 Harness

这是项目通用 Harness，负责需求确认、数据处理、校验、前端调整、测试、自动修复和最终验收。

| 内容 | 路径 |
| --- | --- |
| 机器入口 | [manifest.json](manifest.json) |
| 执行流程 | [workflow.md](workflow.md) |
| 校验规则 | [checks.md](checks.md) |
| 架构边界 | [architecture.md](architecture.md) |
| 阶段提示词 | [prompts/](prompts/) |
| 写入策略 | [policies/](policies/) |
| 交付模板 | [templates/](templates/) |

## CLI

```text
python scripts/harness.py init --requirement requirement.json --execution-id REQ-001-run
python scripts/harness.py run REQ-001-run
python scripts/harness.py resume REQ-001-run
python scripts/harness.py status REQ-001-run
python scripts/harness.py validate REQ-001-run
```

运行记录写入 `docs/runs/<execution-id>/`。
