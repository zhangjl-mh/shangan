"""Validate, deduplicate, and render the daily current-affairs report."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from jsonschema import validators


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = Path(os.getenv("GONGKAO_CONTENT_DIR", ROOT / "content" / "local"))
SCHEMA_PATH = Path(
    os.getenv("GONGKAO_DAILY_NEWS_SCHEMA", ROOT / "agents" / "schema" / "daily-news.schema.json")
)

TIMEZONE = "Asia/Shanghai"
TZ = ZoneInfo(TIMEZONE)


class DailyNewsError(Exception):
    def __init__(
        self,
        stage: str,
        reason: str,
        done: str = "已读取本地文件并完成基础检查。",
        undone: str = "未生成 Markdown。",
        suggestion: str = "请修复 JSON 后重新执行脚本。",
    ) -> None:
        self.stage = stage
        self.reason = reason
        self.done = done
        self.undone = undone
        self.suggestion = suggestion
        super().__init__(reason)


def shanghai_today() -> date:
    return datetime.now(TZ).date()


def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")


def parse_scan_date(value: str | None) -> date:
    if not value:
        return shanghai_today()

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise DailyNewsError(
            stage="参数解析",
            reason=f"--date 必须是 YYYY-MM-DD 格式，当前值：{value}",
            done="未读取文件。",
            undone="未校验 JSON，未生成 Markdown。",
            suggestion="使用示例：python scripts/today_scan.py --date 2026-06-09",
        ) from exc


def read_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise DailyNewsError(
            stage="文件读取",
            reason=f"缺少{label}：{path}",
            done="已解析扫描日期。",
            undone="未校验 JSON，未生成 Markdown。",
            suggestion=f"请先生成或补齐文件：{path}",
        )

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise DailyNewsError(
            stage="JSON 解析",
            reason=f"{label}不是合法 JSON：{path}；{exc}",
            done="已找到文件。",
            undone="未校验 JSON，未生成 Markdown。",
            suggestion="请修复 JSON 语法错误后重新执行。",
        ) from exc

    if not isinstance(data, dict):
        raise DailyNewsError(
            stage="JSON 结构检查",
            reason=f"{label}根节点必须是对象：{path}",
        )

    return data


def write_json(path: Path, contents: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(contents, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents.rstrip() + "\n", encoding="utf-8")


def rel_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_title(value: Any) -> str:
    text = clean_text(value)
    text = re.sub(r"[\s《》“”\"'，。！？、：:；;（）()【】\[\]—\-_/\\|]+", "", text)
    return text.lower()


def normalize_source(value: Any) -> str:
    return clean_text(value).lower()


def normalize_url(value: Any) -> str:
    raw = clean_text(value)
    if not raw:
        return ""

    parsed = urlsplit(raw)
    query = urlencode(
        [
            (key, val)
            for key, val in parse_qsl(parsed.query, keep_blank_values=True)
            if not    if not raw:
        return ""

    parsed = urlsplit(raw)
    query = urlencode(
        [
            (key, val)
            for key, val in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith("utm_")
            and key.lower() not in {"spm", "from", "source"}
        ],
        doseq=True,
    )

    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            query,
            "",
        )
    )


def title_similarity(left: Any, right: Any) -> float:
    a = normalize_title(left)
    b = normalize_title(right)

    if not a or not b:
        return 0

    return SequenceMatcher(None, a, b).ratio()


def extract_date(value: Any) -> str | None:
    text = clean_text(value)
    match = re.search(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", text)

    if not match:
        return None

    year, month, day = match.groups()
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except ValueError:
        return None


def append_note(report: dict[str, Any], note: str) -> None:
    notes = report.setdefault("notes", [])

    if isinstance(notes, list) and note not in notes:
        notes.append(note)


def ensure_basic_fields(report: dict[str, Any], scan_day: date, previous_day: date) -> None:
    scan_date = scan_day.isoformat()
    previous_date = previous_day.isoformat()

    if report.get("date") and report["date"] != scan_date:
        raise DailyNewsError(
            stage="日期归属检查",
            reason=f"文件日期与内容 date 不一致：文件是 {scan_date}，JSON date 是 {report['date']}",
            done="已读取当日 JSON。",
            undone="未写入 JSON，未生成 Markdown。",
            suggestion="请修正 JSON 的 date 字段，或使用正确的 --date 参数。",
        )

    report["date"] = scan_date
    report["timezone"] = TIMEZONE
    report["updatedAt"] = now_iso()
    report["scanDates"] = [scan_date, previous_date]
    report.setdefault("items", [])
    report.setdefault("skippedItems", [])
    report.setdefault("notes", [])

    if "candidatePool" not in report:
        append_note(report, "candidatePool 未提供，本次 Markdown 仅渲染最终入选资讯。")

    if len(report.get("items", [])) < 10:
        append_note(report, f"本日最终收录 {len(report.get('items', []))} 条，少于 10 条。")


def is_duplicate_from_previous(
    item: dict[str, Any],
    previous_items: list[dict[str, Any]],
) -> tuple[bool, str]:
    item_url = normalize_url(item.get("url"))
    item_title = item.get("title")
    item_source = normalize_source(item.get("source"))

    for previous in previous_items:
        previous_url = normalize_url(previous.get("url"))
        previous_source = normalize_source(previous.get("source"))

        if item_url and previous_url and item_url == previous_url:
            return True, "已存在于前一日文件（URL 相同）"

        if item_source and item_source == previous_source:
            if title_similarity(item_title, previous.get("title")) >= 0.92:
                return True, "已存在于前一日文件（标题高度一致且来源一致）"

    return False, ""


def skipped_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalize_url(item.get("url")),
        normalize_title(item.get("title")),
        normalize_source(item.get("source")),
    )


def remove_duplicate_items(
    report: dict[str, Any],
    previous_report: dict[str, Any],
) -> None:
    items = report.get("items", [])
    previous_items = previous_report.get("items", [])

    if not isinstance(items, list):
        raise DailyNewsError(stage="JSON 结构检查", reason="items 必须是数组。")

    if not isinstance(previous_items, list):
        raise DailyNewsError(stage="前一日数据检查", reason="前一日 items 必须是数组。")

    skipped_items = report.setdefault("skippedItems", [])
    if not isinstance(skipped_items, list):
        raise DailyNewsError(stage="JSON 结构检查", reason="skippedItems 必须是数组。")

    existing_skipped = {
        skipped_key(item)
        for item in skipped_items
        if isinstance(item, dict)
    }

    kept: list[dict[str, Any]] = []
    seen_today: set[tuple[str, str, str]] = set()
    previous_duplicate_count = 0
    today_duplicate_count = 0

    for item in items:
        if not isinstance(item, dict):
            raise DailyNewsError(stage="JSON 结构检查", reason="items 中每一项必须是对象。")

        key = skipped_key(item)

        duplicate, reason = is_duplicate_from_previous(item, previous_items)
        if duplicate:
            previous_duplicate_count += 1

            if key not in existing_skipped:
                skipped_items.append(
                    {
                        "title": clean_text(item.get("title")),
                        "source": clean_text(item.get("source")),
                        "url": clean_text(item.get("url")),
                        "reason": reason,
                    }
                )
                existing_skipped.add(key)
            continue

        today_identity = key
        if today_identity in seen_today:
            today_duplicate_count += 1

            if key not in existing_skipped:
                skipped_items.append(
                    {
                        "title": clean_text(item.get("title")),
                        "source": clean_text(item.get("source")),
                        "url": clean_text(item.get("url")),
                        "reason": "当天文件内重复",
                    }
                )
                existing_skipped.add(key)
            continue

        seen_today.add(today_identity)
        kept.append(item)

    historical_previous_skips = sum(
        1
        for item in skipped_items
        if isinstance(item, dict)
        and ("前一日" in clean_text(item.get("reason")) or "昨日" in clean_text(item.get("reason")))
    )

    report["items"] = kept
    report["duplicateFromPreviousDayCount"] = max(
        previous_duplicate_count,
        historical_previous_skips,
    )

    if previous_duplicate_count:
        append_note(report, f"本次从 items 中移除昨日重复资讯 {previous_duplicate_count} 条。")

    if today_duplicate_count:
        append_note(report, f"本次从 items 中移除当天重复资讯 {today_duplicate_count} 条。")


def collect_logic_errors(report: dict[str, Any], scan_day: date) -> list[str]:
    errors: list[str] = []
    scan_date = scan_day.isoformat()
    items = report.get("items", [])

    if not isinstance(items, list):
        return ["items 必须是数组。"]

    if len(items) > 10:
        errors.append(f"items 最多 10 条，当前为 {len(items)} 条。")

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"items[{index}] 必须是对象。")
            continue

        title = clean_text(item.get("title"))
        source = clean_text(item.get("source"))
        url = clean_text(item.get("url"))
        published_at = clean_text(item.get("publishedAt"))

        if not title:
            errors.append(f"items[{index}].title 不能为空。")

        if not source:
            errors.append(f"items[{index}].source 不能为空。")

        if not url:
            errors.append(f"items[{index}].url 不能为空。")

        item_date = extract_date(published_at)
        if not item_date:
            errors.append(f"items[{index}].publishedAt 无法识别日期：{published_at}")
        elif item_date != scan_date:
            errors.append(
                f"items[{index}].publishedAt 日期归属错误：应为 {scan_date}，实际为 {item_date}。"
            )

        verification = item.get("verification")
        if not isinstance(verification, dict):
            errors.append(f"items[{index}].verification 缺失或不是对象。")
            continue

        if verification.get("titleMatched") is not True:
            errors.append(f"items[{index}].verification.titleMatched 必须为 true。")

        if verification.get("dateMatched") is not True:
            errors.append(f"items[{index}].verification.dateMatched 必须为 true。")

        if not clean_text(verification.get("verifiedAt")):
            errors.append(f"items[{index}].verification.verifiedAt 不能为空。")

    return errors


def format_json_path(path: Any) -> str:
    parts = ["$"]

    for item in path:
        if isinstance(item, int):
            parts.append(f"[{item}]")
        else:
            parts.append(f".{item}")

    return "".join(parts)


def validate_schema(report: dict[str, Any], schema: dict[str, Any]) -> None:
    validator_class = validators.validator_for(schema)
    validator_class.check_schema(schema)
    validator = validator_class(schema)

    errors = sorted(validator.iter_errors(report), key=lambda err: list(err.path))
    if not errors:
        return

    messages = []
    for error in errors[:20]:
        messages.append(f"{format_json_path(error.path)}：{error.message}")

    raise DailyNewsError(
        stage="Schema 校验",
        reason="\n".join(messages),
        done="已完成本地去重和基础字段整理。",
        undone="未生成 Markdown。",
        suggestion="请按 agents/schema/daily-news.schema.json 修复对应字段。",
    )


def render_value(value: Any) -> str:
    if isinstance(value, str):
        return clean_text(value)

    if isinstance(value, dict):
        title = clean_text(
            value.get("title")
            or value.get("module")
            or value.get("point")
            or value.get("name")
        )
        explanation = clean_text(
            value.get("explanation")
            or value.get("content")
            or value.get("text")
            or value.get("summary")
            or value.get("question")
        )

        module = clean_text(value.get("module"))
        point = clean_text(value.get("point"))

        if module and point and explanation:
            return f"{module} / {point}：{explanation}"

        if title and explanation:
            return f"{title}：{explanation}"

        if title:
            return title

        if explanation:
            return explanation

    return json.dumps(value, ensure_ascii=False)


def render_list_section(lines: list[str], title: str, values: Any) -> None:
    if not values:
        return

    if not isinstance(values, list):
        values = [values]

    lines.extend([f"### {title}", ""])

    for value in values:
        text = render_value(value)
        if text:
            lines.append(f"- {text}")

    lines.append("")


def render_candidates(lines: list[str], report: dict[str, Any]) -> None:
    candidate_sources = report.get("candidateSources") or []
    candidate_pool = report.get("candidatePool") or []

    if not candidate_sources and not candidate_pool:
        return

    lines.extend(["## 候选收集与选取规则", ""])

    lines.append(f"- 候选数量：{len(candidate_pool)}")
    lines.append("- 选取规则：优先选择当天发布、原文可核验、具备公考积累价值的政策与治理类资讯。")
    lines.append("")

    if isinstance(candidate_sources, list) and candidate_sources:
        lines.append("### 候选来源")
        lines.append("")

        for source in candidate_sources:
            if not isinstance(source, dict):
                continue

            name = clean_text(source.get("name") or source.get("source"))
            url = clean_text(source.get("url"))
            result = clean_text(source.get("result") or source.get("note"))

            if name and url:
                lines.append(f"- [{name}]({url})：{result or '已检索'}")
            elif name:
                lines.append(f"- {name}：{result or '已检索'}")

        lines.append("")

    if isinstance(candidate_pool, list) and candidate_pool:
        lines.append("### 候选池")
        lines.append("")

        for candidate in candidate_pool:
            if not isinstance(candidate, dict):
                continue

            selected = "已选" if candidate.get("selected") else "未选"
            title = clean_text(candidate.get("title"))
            url = clean_text(candidate.get("url"))
            source = clean_text(candidate.get("source"))
            published_at = clean_text(candidate.get("publishedAt") or candidate.get("publishTime"))
            reason = clean_text(candidate.get("reason"))

            link = f"[{title}]({url})" if title and url else title or url
            extra = "，".join(part for part in [source, published_at] if part)

            if extra:
                lines.append(f"- {selected}：{link}（{extra}）：{reason}")
            else:
                lines.append(f"- {selected}：{link}：{reason}")

        lines.append("")


def render_skipped(lines: list[str], report: dict[str, Any]) -> None:
    skipped_items = report.get("skippedItems") or []

    if not isinstance(skipped_items, list) or not skipped_items:
        return

    lines.extend(["## 跳过资讯", ""])

    for item in skipped_items:
        if not isinstance(item, dict):
            continue

        title = clean_text(item.get("title"))
        source = clean_text(item.get("source"))
        url = clean_text(item.get("url"))
        reason = clean_text(item.get("reason"))

        link = f"[{title}]({url})" if title and url else title or url

        if source:
            lines.append(f"- {link}（{source}）：{reason}")
        else:
            lines.append(f"- {link}：{reason}")

    lines.append("")


def render_news_markdown(report: dict[str, Any]) -> str:
    scan_dates = report.get("scanDates", [])
    items = report.get("items", [])

    lines = [
        f"# {report['date']} 每日时政",
        "",
        f"> 扫描日期：{'、'.join(scan_dates)}",
        f"> 更新时间：{report.get('updatedAt', '未记录')}",
        "> 说明：事实来自所列权威信源；备考分析为整理内容，不等同于官方原文。",
        "",
        "## 本日概览",
        "",
        f"- 收录条数：{len(items)} 条",
        f"- 候选资讯：{len(report.get('candidatePool') or [])} 条",
        f"- 跳过昨日重复：{report.get('duplicateFromPreviousDayCount', 0)} 条",
        "",
    ]

    render_candidates(lines, report)

    for index, item in enumerate(items, start=1):
        verification = item.get("verification", {}) if isinstance(item.get("verification"), dict) else {}

        lines.extend(
            [
                f"## {index}. {item['title']}",
                "",
                f"- 来源：[{item['source']}]({item['url']})",
                f"- 发布时间：{item['publishedAt']}",
                f"- 分类：{item.get('category', '未分类')}",
                f"- 核验时间：{verification.get('verifiedAt', '未记录')}",
                "",
                "### 摘要",
                "",
                item.get("summary", ""),
                "",
            ]
        )

        render_list_section(lines, "事实要点", item.get("facts"))
        render_list_section(lines, "政策背景", item.get("policyBackground"))
        render_list_section(lines, "申论角度", item.get("shenlunAngles"))
        render_list_section(lines, "行测关联", item.get("xingceLinks"))
        render_list_section(lines, "积累表达", item.get("materials"))
        render_list_section(lines, "可能出题方向", item.get("examQuestions"))

        note = clean_text(verification.get("note"))
        if note:
            lines.extend(["### 核验说明", "", note, ""])

    render_skipped(lines, report)

    notes = report.get("notes") or []
    if isinstance(notes, list) and notes:
        lines.extend(["## 备注", ""])
        for note in notes:
            lines.append(f"- {clean_text(note)}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and render daily current-affairs data.")
    parser.add_argument("--date", default=None, dest="scan_date", help="扫描日期，格式：YYYY-MM-DD")
    parser.add_argument("--content-dir", default=str(CONTENT_DIR), help="本地内容目录")
    parser.add_argument("--schema", default=str(SCHEMA_PATH), help="daily-news schema 路径")
    args = parser.parse_args()

    scan_label = args.scan_date or shanghai_today().isoformat()

    try:
        scan_day = parse_scan_date(args.scan_date)
        previous_day = scan_day - timedelta(days=1)

        content_dir = Path(args.content_dir)
        schema_path = Path(args.schema)

        news_path = content_dir / "news" / f"{scan_day.isoformat()}.json"
        previous_path = content_dir / "news" / f"{previous_day.isoformat()}.json"
        markdown_path = content_dir / "markdown" / f"{scan_day.isoformat()}-daily-news.md"
        manifest_path = content_dir / "scan" / f"{scan_day.isoformat()}.json"

        schema = read_json(schema_path, "Schema 文件")
        news = read_json(news_path, "当日时政文件")
        previous_news = read_json(previous_path, "前一日时政文件")

        ensure_basic_fields(news, scan_day, previous_day)
        remove_duplicate_items(news, previous_news)

        logic_errors = collect_logic_errors(news, scan_day)
        if logic_errors:
            raise DailyNewsError(
                stage="本地数据复核",
                reason="\n".join(logic_errors),
                done="已读取 Schema、当日 JSON、前一日 JSON，并完成重复检查。",
                undone="未写入 JSON，未生成 Markdown。",
                suggestion="请修复标题、来源、URL、发布时间或 verification 字段后重新执行。",
            )

        validate_schema(news, schema)

        write_json(news_path, news)
        write_text(markdown_path, render_news_markdown(news))

        sources = []
        for item in news.get("items", []):
            source = clean_text(item.get("source"))
            if source and source not in sources:
                sources.append(source)

        manifest = {
            "scanDate": scan_day.isoformat(),
            "timezone": TIMEZONE,
            "finalizedAt": now_iso(),
            "mode": "daily-news",
            "scanDates": news.get("scanDates", []),
            "news": {
                "file": rel_path(news_path),
                "items": len(news.get("items", [])),
                "candidatePool": len(news.get("candidatePool") or []),
                "duplicateFromPreviousDayCount": news.get("duplicateFromPreviousDayCount", 0),
                "sources": sources,
            },
            "outputs": [rel_path(markdown_path)],
        }
        write_json(manifest_path, manifest)

        print(f"已完成 {scan_day.isoformat()} 每日时政更新。")
        print()
        print(f"扫描日期：{scan_day.isoformat()}、{previous_day.isoformat()}")
        print(f"收录条数：{len(news.get('items', []))} 条")
        print(f"候选资讯：{len(news.get('candidatePool') or [])} 条")
        print(f"跳过昨日重复：{news.get('duplicateFromPreviousDayCount', 0)} 条")
        print(f"主要来源：{'、'.join(sources) if sources else '无'}")
        print()
        print("输出文件：")
        print(f"- {rel_path(news_path)}")
        print(f"- {rel_path(markdown_path)}")

    except DailyNewsError as exc:
        print(f"{scan_label} 每日时政更新失败。", file=sys.stderr)
        print(file=sys.stderr)
        print(f"失败环节：{exc.stage}", file=sys.stderr)
        print(f"失败原因：{exc.reason}", file=sys.stderr)
        print(f"已完成内容：{exc.done}", file=sys.stderr)
        print(f"未完成内容：{exc.undone}", file=sys.stderr)
        print(f"建议处理：{exc.suggestion}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()