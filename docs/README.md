# 项目文档

| 文件 | 内容 |
| --- | --- |
| [architecture.md](architecture.md) | 分层与边界 |
| [workflow.md](workflow.md) | 8 阶段流水线 |
| [checks.md](checks.md) | 校验与完成条件 |
| [migration-report.md](migration-report.md) | 本次迁移记录 |
| [templates/](templates/) | 需求、交接、验收模板 |

执行入口为 `.agents/harness/manifest.json`。业务规则以 `.agents/skills/` 为准，数据契约以 `schemas/` 为准。
