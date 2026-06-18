---
name: shangan-docs-router
description: 按需加载“我要上岸”项目文档与 Harness。普通正式需求使用八阶段 Harness；岗位检索需求使用岗位检索 Harness。
---

# Docs Router

`docs/` 根目录只做路由说明。具体 Harness 规则放在各自文件夹中，按需加载。

| 场景 | 入口 |
| --- | --- |
| 普通正式需求、跨模块改动、最终验收 | [harnesses/eight-stage/README.md](harnesses/eight-stage/README.md) |
| 岗位检索、岗位来源采集、岗位表下载解析筛选 | [harnesses/job-search/README.md](harnesses/job-search/README.md) |

## 加载规则

- 先读本文件，根据任务选择一个 Harness。
- 进入对应 Harness 文件夹后，以该文件夹内的 `manifest.json`、`workflow.md`、
  `agents.md`、`prompts/`、`checks.md` 等文件为准。
- 更具体的 Harness 规则优先于通用规则。
- `docs/runs/` 只保存运行记录，不是正式业务数据源。

## Harness 入口格式

每个可按需加载的 Harness 说明文件使用和 Skill 一致的 frontmatter：

```md
---
name: job-search-harness
description: 处理岗位检索、下载、解析筛选和整理输出。用户提到岗位检索、岗位表、事业单位、军队文职、国央企或省考岗位时使用。
---
```
