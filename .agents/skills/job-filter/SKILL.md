---
name: job-filter
description: 获取并筛选公务员、事业单位或国企岗位。当用户询问能报什么、指定地区岗位或要求更新岗位数据时使用。
---

# 岗位筛选

1. 读取 `data/user-profile/profile.json`。
2. 获取用户指定地区的完整官方岗位数据。
3. 保存官方附件和来源，再标准化、去重、筛选。
4. 未知画像字段输出 `needs_confirmation`，不得默认符合。
5. 正式结果写入 `data/jobs/`，使用
   `schemas/job-filter.schema.json` 校验。

国考数据执行：

```bash
python .agents/skills/job-filter/scripts/scan_national_jobs.py
```

禁止编造岗位条件、报名日期、分数或来源。
