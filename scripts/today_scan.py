"""Validate and render the daily current-affairs report."""

from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime
from pathlib import Path

from jsonschema import validate


ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = Path(os.getenv("GONGKAO_CONTENT_DIR", ROOT / "content" / "local"))
SCHEMA_PATH = ROOT / "agents" / "schema" / "daily-news.schema.json"


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
    meta = report.get("meta", {})
    lines = [
        f"# {report['title']}",
        "",
        f"> 原文链接核验时间：{meta.get('verifiedAt', '未记录')}。事实来自所列信源；备考角度为整理内容。",
        "",
        report["summary"],
        "",
    ]
    if report.get("candidateSources") or report.get("candidatePool"):
        lines.extend(
            [
                "## 候选收集与选取规则",
                "",
                f"- 候选数量：{meta.get('candidateCount', len(report.get('candidatePool', [])))}",
                f"- 选取规则：{meta.get('selectionRule', '优先选择当天发布、原文可核验、具备公考积累价值的政策与治理类资讯。')}",
                "",
            ]
        )
        for source in report.get("candidateSources", []):
            lines.append(f"- [{source['name']}]({source['url']})：{source['result']}")
        if report.get("candidateSources"):
            lines.append("")
        if report.get("candidatePool"):
            lines.extend(["### 候选池", ""])
            for candidate in report["candidatePool"]:
                prefix = "已选" if candidate.get("selected") else "未选"
                lines.append(
                    f"- {prefix}：[{candidate['title']}]({candidate['url']})"
                    f"（{candidate['source']}，{candidate.get('publishTime', '时间以原文为准')}）"
                    f"：{candidate['reason']}"
                )
            lines.append("")
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Finalize daily current-affairs data.")
    parser.add_argument("--date", default=date.today().isoformat(), dest="scan_date")
    args = parser.parse_args()

    news_path = CONTENT_DIR / "news" / f"{args.scan_date}.json"
    if not news_path.exists():
        raise SystemExit(f"缺少当日时政文件：{news_path}")

    news = read_json(news_path)
    validate(news, read_json(SCHEMA_PATH))

    markdown_path = CONTENT_DIR / "markdown" / f"{args.scan_date}-daily-news.md"
    write_text(markdown_path, render_news_markdown(news))

    manifest = {
        "scanDate": args.scan_date,
        "finalizedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": "daily-news",
        "news": {
            "file": str(news_path),
            "items": len(news["items"]),
            "verifiedAt": news.get("meta", {}).get("verifiedAt"),
        },
        "outputs": [str(markdown_path)],
    }
    manifest_path = CONTENT_DIR / "scan" / f"{args.scan_date}.json"
    write_json(manifest_path, manifest)

    print(f"[今日时政完成] {args.scan_date} | 时政 {len(news['items'])} 条")
    print(f"[输出] {markdown_path}")
    print(f"[清单] {manifest_path}")


if __name__ == "__main__":
    main()
