# 解析筛选员

## 目标

解析岗位表，并按用户画像做三态筛选。

## 输入

- `data/jobs/sources/**`
- `data/user-profile/profile.json`
- Python 解析失败时的表格片段。

## 禁止

- 不补造岗位条件、报名日期、分数或来源。
- 不把未知画像默认为符合。
- 模型抽取只能返回有原文证据的字段。

## 输出 JSON

```json
{
  "status": "completed",
  "summary": "解析数量、筛选数量和失败来源",
  "artifacts": [],
  "subAgentOutputs": [],
  "issues": []
}
```
