"""Finalize files produced by the today-scan skill.

This script does not scrape sites or call a model. The skill prepares verified
JSON facts, then this deterministic step validates and renders display files.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from pathlib import Path

from jsonschema import validate


ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = Path(os.getenv("GONGKAO_CONTENT_DIR", ROOT / "content" / "local"))
DATA_DIR = Path(os.getenv("GONGKAO_DATA_DIR", ROOT / "data"))
SCHEMA_DIR = ROOT / "agents" / "schema"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, contents: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(contents, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def render_news_markdown(report: dict) -> str:
    lines = [
        f"# {report['title']}",
        "",
        f"> 原文链接核验时间：{report.get('meta', {}).get('verifiedAt', '未记录')}。事实来自所列信源；备考角度为整理内容。",
        "",
        report["summary"],
        "",
    ]
    for item in report["items"]:
        lines.extend(
            [
                f"## {item['title']}",
                "",
                f"- 来源：[{item['source']}]({item['url']})",
                f"- 发布时间：{item['publishTime']}",
                f"- 关键词：{'、'.join(item['keywords'])}",
                "",
                item["summary"],
                "",
            ]
        )
        if item.get("policyBackground"):
            lines.extend(["### 政策背景", "", item["policyBackground"], ""])
        if item.get("shenlunAngles"):
            lines.extend(["### 申论角度", ""])
            for angle in item["shenlunAngles"]:
                lines.append(f"- {angle['title']}：{angle['explanation']}")
            lines.append("")
        if item.get("xingceLinks"):
            lines.extend(["### 行测关联", ""])
            for link in item["xingceLinks"]:
                lines.append(f"- {link['module']} / {link['point']}：{link['explanation']}")
            lines.append("")
        if item.get("materials"):
            lines.extend(["### 积累表达", ""])
            lines.extend(f"- {text}" for text in item["materials"])
            lines.append("")
        if item.get("examQuestions"):
            lines.extend(["### 可能出题方向", ""])
            lines.extend(f"- {question}" for question in item["examQuestions"])
            lines.append("")
    return "\n".join(lines)


def render_job_markdown(report: dict) -> str:
    positions = [
        position for position in report.get("positions", [])
        if position.get("status") in {"报名中", "即将报名", "待考试"}
    ]
    lines = [
        "# 今日岗位扫描报告",
        "",
        f"- 生成时间：{report['generatedAt']}",
        f"- 当前尚未考试岗位数量：{len(positions)}",
        f"- 扫描渠道数量：{len(report.get('searchedSources', []))}",
        "",
        "## 筛选结论",
        "",
        report.get("screeningNote", "暂无说明。"),
        "",
        "## 参考数据规则",
        "",
        report.get("referencePolicy", "仅展示有可追溯信源的信息。"),
        "",
    ]
    if positions:
        lines.extend(["## 当前可报或尚待考试岗位", ""])
        for position in positions:
            lines.extend(
                [
                    f"### {position['organization']} - {position['title']}",
                    "",
                    f"- 地区：{position['region']}{(' / ' + position['district']) if position.get('district') else ''}",
                    f"- 状态：{position['status']}",
                    f"- 招录人数：{position.get('recruitCount', '官方未公开')}",
                    f"- 报名截止：{position.get('registrationEndAt') or position.get('registrationEndDate', '以官方公告为准')}",
                    f"- 资格初审截止：{position.get('qualificationReviewEndAt', '以官方公告为准')}",
                    f"- 缴费截止：{position.get('paymentEndAt', '以官方公告为准')}",
                    f"- 笔试时间：{position.get('examDate', '以官方公告为准')}",
                    f"- 岗位代码：{position.get('positionCode', '官方未公开')}",
                    f"- 原文：[{position['sourceName']}]({position['sourceUrl']})",
                    "",
                ]
            )
            if position.get("recommendation"):
                lines.extend(
                    [
                        f"- 推荐结论：{position['recommendation']}",
                        f"- 匹配度：{position.get('matchScore', '未评估')} / 风险等级：{position.get('riskLevel', '未评估')}",
                        "",
                    ]
                )
            if position.get("responsibilities"):
                lines.extend([f"- 工作内容：{position['responsibilities']}", ""])
            for reason in position.get("matchReasons", []):
                lines.append(f"- 匹配原因：{reason}")
            for risk in position.get("riskReminders", []):
                lines.append(f"- 风险提醒：{risk}")
            for advice in position.get("studyAdvice", []):
                lines.append(f"- 备考建议：{advice}")
            for history in position.get("historicalReferences", []):
                lines.append(
                    f"- {history['year']}参考：进面/入围分 {history.get('finalEntryScore', '官方未公开')}；"
                    f"报录比 {history.get('applicationRatio', '官方未公开')}；"
                    f"来源 [{history['sourceName']}]({history['sourceUrl']})"
                )
            for note in position.get("applicationNotes", []):
                lines.append(f"- 报考提示：{note}")
            if position.get("compensationReference"):
                pay = position["compensationReference"]
                lines.extend(["", f"- 薪资估算：{pay['text']}（{pay['disclaimer']}）"])
            lines.append(f"- 福利待遇：{'；'.join(position.get('benefits', [])) or '官方公告未载明。'}")
            lines.append(f"- 房子：{position.get('housingReference', '官方公告未载明住房安排。')}")
            lines.append(f"- 户口：{position.get('householdReference', '官方公告未载明落户安排。')}")
            lines.append("")
    lines.extend(["## 已扫描权威渠道", ""])
    for source in report.get("searchedSources", []):
        lines.append(f"- [{source['name']}]({source['url']})：{source['result']}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize today's news and job scan data.")
    parser.add_argument("--date", default=date.today().isoformat(), dest="scan_date")
    parser.add_argument(
        "--jobs-only",
        action="store_true",
        help="Only validate and render the job scan report for this date.",
    )
    args = parser.parse_args()

    news_path = CONTENT_DIR / "news" / f"{args.scan_date}.json"
    jobs_path = CONTENT_DIR / "job" / "eligible-jobs.json"
    if not news_path.exists() and not args.jobs_only:
        raise SystemExit(f"缺少当日时政文件：{news_path}")
    if not jobs_path.exists():
        raise SystemExit(f"缺少岗位扫描文件：{jobs_path}")

    news = read_json(news_path) if news_path.exists() and not args.jobs_only else None
    jobs = read_json(jobs_path)
    jobs["positions"] = [
        position for position in jobs.get("positions", [])
        if position.get("status") in {"报名中", "即将报名", "待考试"}
    ]
    if news is not None:
        validate(news, read_json(SCHEMA_DIR / "daily-news.schema.json"))
    validate(jobs, read_json(SCHEMA_DIR / "eligible-jobs.schema.json"))
    write_json(jobs_path, jobs)

    markdown_dir = CONTENT_DIR / "markdown"
    news_markdown = markdown_dir / f"{args.scan_date}-daily-news.md"
    jobs_markdown = markdown_dir / f"{args.scan_date}-job-scan.md"
    outputs = []
    if news is not None:
        write_text(news_markdown, render_news_markdown(news))
        outputs.append(str(news_markdown))
    write_text(jobs_markdown, render_job_markdown(jobs))
    outputs.append(str(jobs_markdown))

    source_registry = read_json(DATA_DIR / "job-sources.json")
    manifest = {
        "scanDate": args.scan_date,
        "finalizedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "jobs-only" if args.jobs_only else "news-and-jobs",
        "news": (
            {
                "file": str(news_path),
                "items": len(news["items"]),
                "verifiedAt": news.get("meta", {}).get("verifiedAt"),
            }
            if news is not None
            else None
        ),
        "jobs": {
            "file": str(jobs_path),
            "positions": len(jobs.get("positions", [])),
            "searchedSources": len(jobs.get("searchedSources", [])),
            "registeredOfficialSources": len(source_registry.get("sources", [])),
        },
        "outputs": outputs,
    }
    manifest_path = CONTENT_DIR / "scan" / f"{args.scan_date}.json"
    write_json(manifest_path, manifest)

    print(
        f"[今日扫描完成] {args.scan_date} | "
        f"时政 {manifest['news']['items'] if manifest['news'] else 0} 条 | "
        f"当前可展示岗位 {manifest['jobs']['positions']} 个 | "
        f"权威入口 {manifest['jobs']['searchedSources']} 个"
    )
    if news is not None:
        print(f"[输出] {news_markdown}")
    print(f"[输出] {jobs_markdown}")
    print(f"[清单] {manifest_path}")


if __name__ == "__main__":
    main()
