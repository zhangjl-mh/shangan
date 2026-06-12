---
name: study-route
description: 生成或更新行测、申论完整学习路线和分科老师推荐。当用户询问学习顺序、课程选择、老师推荐或备考路线时使用。
---

# 学习路线

1. 读取 `data/user-profile/profile.json` 和已有路线。
2. 明确科目、阶段、周期、每日动作和验收标准。
3. 老师推荐按模块说明主线、适用阶段、使用方法和公开来源。
4. 行测写入 `data/xingce/route.json`。
5. 申论写入 `data/shenlun/route.json`。
6. 使用对应 Schema 校验并执行 `npm run check`。

不编造课程、履历、评价或考试规则。
