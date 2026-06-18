# 02 数据处理

阶段顺序与完成条件以 `docs/harnesses/eight-stage/workflow.md` 为准，本文件只补充数据处理动作。

读取已确认需求和对应 `.agents/skills/`。

1. 仅在授权数据路径内生成或更新数据。
2. 遵守 Schema、来源、日期和隐私要求。
3. 不改前端，不撤销他人改动。
4. 无数据工作时记录 `skipped: not_applicable`。
5. 输出变更清单、证据与 `AGENT-HANDOFF`，下一阶段为 03。
