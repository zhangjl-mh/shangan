---

name: daily-news
description: 为“上岸”生成或更新每日时政数据。当用户说“今日时政”“每日时政”“今日资讯”“检索今天的新闻”“更新资讯”或要求按日期补齐时政材料时，必须使用本技能：默认扫描今天和昨天，只采集指定日期范围内的权威原文，去重后整理备考角度，并写入前端可读 JSON/Markdown。
---------------------------------------------------------------------------------------------------------------------------------------------------

# 每日时政

## 输出文件

以扫描日期 `YYYY-MM-DD` 为准，更新：

```txt
content/local/news/YYYY-MM-DD.json
content/local/markdown/YYYY-MM-DD-daily-news.md
```

页面只读取本地生成文件，不在浏览器中联网抓取或调用模型。

## 日期规则

* “今日/今天”按 `Asia/Shanghai` 自然日处理。
* 默认每次扫描两个自然日：今天和昨天。
* 回报用户时必须使用绝对日期。
* 今天文件只写入今天发布且未在昨天文件中收录的资讯。
* 昨天已存在的资讯，今天不重复写入。

## 输入依赖

执行前读取：

```txt
agents/schema/daily-news.schema.json
content/local/news/YYYY-MM-DD.json
content/local/news/YYYY-MM-DD-1.json
```

说明：

* `YYYY-MM-DD.json` 是当前扫描日期文件。
* `YYYY-MM-DD-1.json` 表示前一日文件，实际路径应替换为前一天日期。
* 如果当天 JSON 已存在，必须重新核验已有条目的标题、来源、发布时间和日期归属。
* 如果资讯 URL、标题或核心事实已经存在于昨天文件，今天不再收录。

## 来源优先级

优先检索：

1. 中国政府网
2. 国务院部门官网
3. 新华社 / 新华网
4. 人民日报 / 人民网
5. 求是网
6. 事件主管部门官网
7. 省级政府官网或权威政务平台


## 执行步骤

1. 明确扫描日期：
   * 默认扫描今天和昨天。
   * 指定日期时扫描指定日期。
2. 读取 Schema、当天 JSON、前一天 JSON。
3. 检索权威来源，建立 `candidateSources`。
4. 阅读原文，建立 `candidatePool`。
5. 与前一天 `items` 去重：
   * URL 相同，视为重复。
   * 标题高度一致且来源一致，视为重复。
   * 同一事件仅发布时间不同，优先保留原已收录日期。
6. 从候选池中按政策性、治理性、申论价值、行测关联度和公共服务价值，选取最适合备考的前 10 条写入 `items`。
7. 对每条入选资讯核验标题、来源、发布时间和原文事实。
8. 补充备考加工内容：`policyBackground`、`shenlunAngles`、`xingceLinks`、`materials`、`examQuestions`。
9. 写入 JSON，校验 Schema。
10. 执行脚本生成 Markdown：

```bash
python scripts/today_scan.py --date YYYY-MM-DD
```

## JSON格式要求

```json
{
  "date": "YYYY-MM-DD",
  "timezone": "Asia/Shanghai",
  "updatedAt": "",
  "scanDates": ["YYYY-MM-DD", "YYYY-MM-DD-1"],
  "items": [
    {
      "id": "",
      "title": "",
      "source": "",
      "url": "",
      "publishedAt": "",
      "category": "",
      "summary": "",
      "facts": [],
      "shenlunAngles": [],
      "xingceLinks": [],
      "materials": [],
      "examQuestions": [],
      "verification": {
        "verifiedAt": "",
        "titleMatched": true,
        "dateMatched": true,
        "note": ""
      }
    }
  ],
  "skippedItems": [
    {
      "title": "",
      "source": "",
      "url": "",
      "reason": "已存在于前一日文件"
    }
  ],
  "notes": []
}
```

说明：

* `date` 是当前输出文件对应日期。
* `scanDates` 记录本次实际扫描日期，默认包含今天和昨天。
* `candidatePool` 记录候选资讯。
* `items` 记录最终入选资讯，最多 10 条。
* `duplicateFromPreviousDayCount` 记录因已存在于昨天文件而跳过的数量。
* `notes` 记录不足 10 条、无法核验、旧数据修正、重复跳过等情况。

## 校验

写入 JSON 后执行：

```bash
python scripts/validate_output.py --schema agents/schema/daily-news.schema.json --file content/local/news/YYYY-MM-DD.json
```

校验通过后再生成 Markdown：

```bash
python scripts/today_scan.py --date YYYY-MM-DD
```

校验失败时，先修复 JSON；仍失败则不生成 Markdown，并向用户说明失败字段。

## 禁止事项

* 不编造标题、日期、来源或 URL。
* 不用旧闻冒充今日资讯。
* 不把转载页、聚合页、搜索结果页当作原文。
* 不跳过已有 JSON 的重新核验。
* 不跳过与昨天文件的去重。
* 不跳过 Schema 校验。
* 不生成与 JSON 不一致的 Markdown。
* 不把备考分析写成官方原文。

## 回报格式

成功后回报：

```txt
已完成 YYYY-MM-DD 每日时政更新。

扫描日期：YYYY-MM-DD、YYYY-MM-DD-1
收录条数：X 条
候选资讯：X 条
跳过昨日重复：X 条
主要来源：XXX、XXX、XXX

输出文件：
- content/local/news/YYYY-MM-DD.json
- content/local/markdown/YYYY-MM-DD-daily-news.md
```

失败时回报：

```txt
YYYY-MM-DD 每日时政更新失败。

失败环节：
失败原因：
已完成内容：
未完成内容：
建议处理：
```
