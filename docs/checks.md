# 校验

## 必检

- 写入文件全部位于需求的 `ownedPaths`，且不命中 `excludedPaths`。
- JSON 可解析，并按对应 `schemas/*.schema.json` 校验。
- 正式数据无临时字段、占位值和遗留路径引用。
- 交接、执行记录、验收报告字段完整。

## 项目命令

按改动范围执行：

```text
npm run validate:project
npm run lint
npm run typecheck
npm test
npm run build
```

完整检查使用 `npm run check`。命令未执行、失败或证据缺失均不得输出 `all_passed`。

## 最终状态

| 状态 | 含义 |
| --- | --- |
| `all_passed` | 所有标准、结构检查和适用测试通过 |
| `has_bugs` | 自动修复 3 轮后仍有失败 |
| `awaiting_review` | 缺少不可自行获得的输入或人工决定 |
