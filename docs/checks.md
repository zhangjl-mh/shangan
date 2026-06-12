# 校验

## 必检

- 写入文件全部位于需求的 `ownedPaths`，且不命中 `excludedPaths`。
- JSON 可解析，并按对应 `schemas/*.schema.json` 校验。
- 正式数据无临时字段、占位值和遗留路径引用。
- 不存在旧 Harness 路径、嵌套 Harness 文档目录、拼写错误目录或下划线私有组件目录。
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

## Harness 检查

```text
python -m unittest tests.test_harness
python scripts/harness.py validate <execution-id>
```

- 每阶段执行前后比较 `git status --porcelain`，并对已变更文件计算摘要，以识别
  阶段期间对既有脏文件的继续修改。
- `docs/runs/**` 为运行产物；其他变更必须命中需求 `ownedPaths`，且不得命中
  `excludedPaths`。禁止规则优先。
- runner 非零退出、缺失/无效 handoff 时保留当前阶段并标记 `paused`；
  使用 `resume` 从该阶段重试。
- 03、05、06 任一阶段失败进入 07。每轮 07 后回跑 03、05、06，最多三轮，
  随后必须进入 08。
- 只有 08 返回 `all_passed` 且 03、05、06 最新结果均通过，执行状态才可为
  `all_passed`。

## 最终状态

| 状态 | 含义 |
| --- | --- |
| `all_passed` | 所有标准、结构检查和适用测试通过 |
| `has_bugs` | 自动修复 3 轮后仍有失败 |
| `awaiting_review` | 缺少不可自行获得的输入或人工决定 |
