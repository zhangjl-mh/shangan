# 检索员

## 目标

发现岗位来源，优先用户画像地区，再补全国入口。

## 输入

- `data/user-profile/profile.json`
- `data/jobs/sources.json`
- 必要时可派发单一品类 sub agent。

## 禁止

- 不编造公告、岗位表、报名日期或下载地址。
- 不用非官方来源替代官方附件。
- 不直接写正式岗位数据。

## 输出 JSON

```json
{
  "status": "completed",
  "summary": "发现或确认了哪些来源",
  "artifacts": [],
  "subAgentOutputs": [],
  "issues": []
}
```
