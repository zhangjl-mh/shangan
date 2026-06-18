# 01 需求确认

阶段顺序与完成条件以 `docs/harnesses/eight-stage/workflow.md` 为准，本文件只补充需求确认动作。

读取用户需求、`AGENTS.md`、相关 Skill、Schema 和写入策略。

1. 使用 `docs/harnesses/eight-stage/templates/requirement.md` 固化目标、输入、`ownedPaths`、`excludedPaths`、非目标和可验证验收标准。
2. 消除可从仓库确认的歧义；仅在关键输入无法获得时标记 `awaiting_review`。
3. 不修改业务文件。
4. 输出阶段产物与 `AGENT-HANDOFF`，下一阶段为 02。
