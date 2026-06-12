"""Validate, deduplicate, and render one daily-news JSON file."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = REPO_ROOT / "data" / "daily-news"
SCHEMA_PATH = REPO_ROOT / "schemas" / "daily-news.schema.json"
TIMEZONE = timezone(timedelta(hours=8))


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"缺少文件：{path.relative_to(REPO_ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 非法：{path.relative_to(REPO_ROOT)}：{exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON 根节点必须是对象：{path.relative_to(REPO_ROOT)}")
    return value


def normalize_url(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parsed = urlsplit(raw)
    query = urlencode(
        [
            (key, item)
            for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith("utm_")
            and key.lower() not in {"from", "source", "spm"}
        ]
    )
    return urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path.rstrip("/"), query, "")
    )


def normalize_title(value: Any) -> str:
    return re.sub(r"\W+", "", str(value or ""), flags=re.UNICODE).lower()


def same_item(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_url = normalize_url(left.get("url"))
    right_url = normalize_url(right.get("url"))
    if left_url and left_url == right_url:
        return True
    left_title = normalize_title(left.get("title"))
    right_title = normalize_title(right.get("title"))
    return bool(
        left_title
        and right_title
        and str(left.get("source", "")).strip() == str(right.get("source", "")).strip()
        and SequenceMatcher(None, left_title, right_title).ratio() >= 0.92
    )


def extract_date(value: Any) -> str | None:
    match = re.search(r"\d{4}-\d{2}-\d{2}", str(value or ""))
    return match.group(0) if match else None


def validate_business(report: dict[str, Any], scan_date: str) -> None:
    if report.get("date") != scan_date:
        raise ValueError(f"date 必须与文件日期一致：{scan_date}")
    if report.get("meta", {}).get("date") != scan_date:
        raise ValueError(f"meta.date 必须与文件日期一致：{scan_date}")

    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    for index, item in enumerate(report.get("items", [])):
        item_date = extract_date(item.get("publishTime"))
        if item_date != scan_date:
            raise ValueError(
                f"items[{index}].publishTime 日期错误：应为 {scan_date}，实际为 {item_date}"
            )
        url = normalize_url(item.get("url"))
        title = normalize_title(item.get("title"))
        if url in seen_urls or title in seen_titles:
            raise ValueError(f"items[{index}] 与当天其他资讯重复")
        seen_urls.add(url)
        seen_titles.add(title)
        if item.get("verification", {}).get("status") != "verified":
            raise ValueError(f"items[{index}].verification.status 必须为 verified")


def remove_previous_duplicates(
    report: dict[str, Any], previous: dict[str, Any]
) -> int:
    kept: list[dict[str, Any]] = []
    removed = 0
    for item in report.get("items", []):
        if any(same_item(item, old) for old in previous.get("items", [])):
            removed += 1
        else:
            kept.append(item)
    report["items"] = kept
    report.setdefault("meta", {})["itemCount"] = len(kept)
    return removed


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['title']}",
        "",
        report.get("summary", ""),
        "",
    ]
    for index, item in enumerate(report.get("items", []), start=1):
        lines.extend(
            [
                f"## {index}. {item['title']}",
                "",
                f"- 来源：[{item['source']}]({item['url']})",
                f"- 发布时间：{item['publishTime']}",
                "",
                item.get("summary", ""),
                "",
            ]
        )
        for title, key in (
            ("申论角度", "shenlunAngles"),
            ("行测关联", "xingceLinks"),
            ("积累表达", "materials"),
            ("出题方向", "examQuestions"),
        ):
            values = item.get(key) or []
            if not values:
                continue
            lines.extend([f"### {title}", ""])
            for value in values:
                if isinstance(value, dict):
                    text = "：".join(
                        part
                        for part in (
                            value.get("title") or value.get("module"),
                            value.get("explanation") or value.get("point"),
                        )
                        if part
                    )
                else:
                    text = str(value)
                lines.append(f"- {text}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now(TIMEZONE).date().isoformat())
    args = parser.parse_args()
    scan_day = date.fromisoformat(args.date)
    previous_day = scan_day - timedelta(days=1)
    news_path = DATA_DIR / f"{scan_day.isoformat()}.json"
    previous_path = DATA_DIR / f"{previous_day.isoformat()}.json"
    markdown_path = DATA_DIR / "markdown" / f"{scan_day.isoformat()}.md"

    try:
        report = read_json(news_path)
        previous = read_json(previous_path)
        removed = remove_previous_duplicates(report, previous)
        validate_business(report, scan_day.isoformat())

        schema = read_json(SCHEMA_PATH)
        errors = sorted(
            Draft202012Validator(
                schema, format_checker=FormatChecker()
            ).iter_errors(report),
            key=lambda error: list(error.path),
        )
        if errors:
            detail = "; ".join(error.message for error in errors[:10])
            raise ValueError(f"Schema 校验失败：{detail}")

        news_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(render_markdown(report), encoding="utf-8")
        print(
            json.dumps(
                {
                    "date": scan_day.isoformat(),
                    "items": len(report.get("items", [])),
                    "removedPreviousDuplicates": removed,
                    "outputs": [
                        news_path.relative_to(REPO_ROOT).as_posix(),
                        markdown_path.relative_to(REPO_ROOT).as_posix(),
                    ],
                },
                ensure_ascii=False,
            )
        )
    except (ValueError, OSError) as exc:
        print(f"每日资讯处理失败：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
