---
name: job-filter
description: 获取、更新并筛选公务员、事业单位、军队文职、国央企岗位。用户提到岗位检索、岗位表、能报什么、指定地区岗位、省考、国考或岗位数据更新时使用。
---

# 岗位筛选

1. 读取 `data/jobs/sources.json`，只下载其中声明的官方附件。
2. 原始附件保存到 `data/jobs/sources/`，不得人工改写。
3. 按考试适配器解析并写入统一 JSONL 目录。
4. 使用 `data/user-profile/profile.json` 做三态筛选。
5. 未知画像字段输出 `needs_confirmation`，不得默认符合。
6. 报名时效与资格分开判断；已截止岗位只能作为历史参考。
7. 结果使用 `schemas/job-filter.schema.json` 校验。

执行：

```bash
python .agents/skills/job-filter/scripts/job_pipeline.py all
```

可单独运行 `download`、`build` 或 `validate`。禁止编造岗位条件、报名日期、
分数或来源；无法从官方附件确认的字段必须保留为空或待确认。
