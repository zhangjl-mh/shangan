# 08 最终验收

使用 `docs/templates/acceptance.md` 汇总需求、交接和检查证据。

1. 逐项判断验收标准，证据必须可定位。
2. 验证执行记录、交接和验收 JSON 符合对应 Schema。
3. 只有全部标准与适用检查通过时输出 `all_passed`。
4. 修复 3 轮后仍失败输出 `has_bugs`；缺少外部决定输出 `awaiting_review`。
5. 输出最终报告与最后一个 `AGENT-HANDOFF`；非 `all_passed` 不得标记完成。
