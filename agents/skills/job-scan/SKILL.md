---
name: job-scan
description: 为“我要上岸”扫描和整理岗位数据。当用户说“扫描岗位”“找我能报的岗位”“更新岗位”“国考名单出来了吗”“事业单位/国企招聘”或询问岗位值不值得报时，务必使用此技能：读取本地画像，检索登记的全部官方渠道，导入符合硬条件的岗位，并形成匹配、风险、备考与待遇判断面板所需数据。
---

# 岗位扫描

## 输出

更新供岗位判断工作台读取的数据：

```txt
content/local/job/eligible-jobs.json
content/local/markdown/YYYY-MM-DD-job-scan.md
content/local/scan/YYYY-MM-DD.json
```

## 开始前

1. 执行 `python scripts/ensure_profile.py`。若画像不存在，由脚本在终端问询并写入 `data/profile.local.json`。
2. 读取 `data/profile.local.json`、`data/job-sources.json` 与 `agents/schema/eligible-jobs.schema.json`。
3. 将画像仅用于本地资格筛选。输出文件不写入姓名、毕业年份、画像哈希或其他可识别个人的原始字段。

## 覆盖规则

1. 扫描 `data/job-sources.json` 中登记的全部官方入口，并记录每个入口的核验结论。
2. 每次检查国家公务员局当前年度及下一招录年度专题；下一年度官方附件尚未发布时写明核验日期，不推测职位表。
3. 运行 `python scripts/import_national_jobs.py`，同步已接入的国家公务员局、石家庄市人社局和中国雄安官网官方附件。官网年度附件临时不可访问时，可以读取仓库中的同年度已核验官方快照。
4. 对尚未接入确定性解析的北京、天津、区县门户、军队文职与国企公告，依据官方原文补充核验结果和岗位条目。
5. 国企只纳入官方正式招聘，排除劳务派遣、外包和无法追溯到用人单位/主管部门公告的转载。

## 纳入岗位

- 将所有能够确认符合画像硬性条件的岗位写入 `positions`，不只保留推荐前几条。
- 已结束岗位仍可作为历史参考，但状态必须显示为 `已截止` 或 `已结束`；不可显示成当前可报名。
- 硬性条件缺失或不确定时，不将岗位判定为符合；记录待确认事项即可。
- 页面不展示“符合依据”和泛泛的“岗位优势”。输出应服务判断：是否能报、是否值得关注、风险是什么、如何备考。

## 判断字段

每个岗位尽量整理：

```txt
单位、岗位、类别、地区、状态、招录人数、岗位代码、公告 URL、采集时间
学历、学位、专业、届别与公告备注
公告职责或标明为推断的工作内容
matchScore、matchLevel、recommendation、matchReasons
riskLevel、riskReminders、studyAdvice
historicalReferences（只使用可追溯官方分数/人数/报录数据）
compensationReference、benefits、housingReference、householdReference
```

待遇金额未在官方材料中公开时，只能给出地区与岗位性质对应的宽区间推算，并明确写明“非招聘单位待遇承诺”。房子和户口没有官方说明时直接标注未载明。

## 收口

如当日时政 JSON 已存在，执行：

```bash
python scripts/today_scan.py --date YYYY-MM-DD
npm run typecheck
npm run build
```

回报官方入口覆盖数、符合岗位数及状态分布、当前可报名岗位数、下一年度国考发布状态和验证结果。
