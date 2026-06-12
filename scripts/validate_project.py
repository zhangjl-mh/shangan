#!/usr/bin/env python3
"""Repository-level validation for the shangan project."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError
except ImportError as exc:  # pragma: no cover - exercised only in incomplete environments
    print(
        "[ERROR] Missing dependency 'jsonschema'. Install requirements.txt first.",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"
DATA_DIR = ROOT / "data"
SKILLS_DIR = ROOT / ".agents" / "skills"
HARNESS_CONFIG = ROOT / ".agents" / "harness" / "manifest.json"
INVALID_JSON = object()

TEXT_SUFFIXES = {
    "",
    ".css",
    ".env",
    ".example",
    ".html",
    ".js",
    ".json",
    ".jsonl",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORED_PARTS = {".git", ".next", "node_modules", "deliverables", "__pycache__"}


@dataclass(frozen=True)
class SchemaRule:
    pattern: str
    schema_name: str


SCHEMA_RULES = (
    SchemaRule("daily-news/*.json", "daily-news.schema.json"),
    SchemaRule("shenlun/route.json", "shenlun-route.schema.json"),
    SchemaRule("xingce/route.json", "xingce-route.schema.json"),
    SchemaRule("user-profile/profile.json", "user-profile.schema.json"),
    SchemaRule("jobs/national-civil-service.json", "job-filter.schema.json"),
    SchemaRule("harness/executions/*.json", "harness-execution.schema.json"),
    SchemaRule("handoffs/*.json", "agent-handoff.schema.json"),
    SchemaRule("acceptance/*.json", "acceptance-report.schema.json"),
)

# Keep obsolete paths segmented so this validator is itself valid controlled text.
LEGACY_REFERENCES = (
    ("old skills path", ("agents", "skills"), False),
    ("old schema path", ("agents", "schema"), False),
    ("old local content path", ("content", "local"), False),
    ("old library content path", ("content", "library"), False),
    ("old official content path", ("content", "official"), False),
    ("old root scan script", ("scripts", "today_scan.py"), True),
)
LEGACY_ROOTS = ("agents", "content", "components", "lib")


class ProjectValidator:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.check_count = 0

    def error(self, message: str) -> None:
        self.errors.append(message)

    def run(self) -> int:
        checks = (
            ("skill frontmatter", self.validate_skills),
            ("JSON and schemas", self.validate_json_data),
            ("daily news integrity", self.validate_daily_news),
            ("Harness configuration", self.validate_harness),
            ("legacy references", self.validate_legacy_references),
            ("legacy root directories", self.validate_legacy_roots),
        )

        for label, check in checks:
            before = len(self.errors)
            try:
                check()
            except Exception as exc:  # Keep one broken check from hiding the rest.
                self.error(f"{label}: unexpected validator failure: {exc}")
            self.check_count += 1
            status = "PASS" if len(self.errors) == before else "FAIL"
            print(f"[{status}] {label}")

        if self.errors:
            print(f"\nProject validation failed with {len(self.errors)} error(s):")
            for index, message in enumerate(self.errors, start=1):
                print(f"  {index}. {message}")
            return 1

        print(f"\nProject validation passed ({self.check_count} check groups).")
        return 0

    def validate_skills(self) -> None:
        if not SKILLS_DIR.is_dir():
            self.error(f"missing skills directory: {relative(SKILLS_DIR)}")
            return

        skill_dirs = sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())
        if not skill_dirs:
            self.error(f"no business skill directories found in {relative(SKILLS_DIR)}")
            return

        for skill_dir in skill_dirs:
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                self.error(f"{relative(skill_file)} is missing")
                continue

            try:
                frontmatter = parse_frontmatter(skill_file)
            except ValueError as exc:
                self.error(f"{relative(skill_file)} has invalid frontmatter: {exc}")
                continue

            name = frontmatter.get("name")
            if not isinstance(name, str) or not name.strip():
                self.error(f"{relative(skill_file)} frontmatter requires a string name")
            elif name.strip() != skill_dir.name:
                self.error(
                    f"{relative(skill_file)} name {name!r} does not match "
                    f"directory {skill_dir.name!r}"
                )
            description = frontmatter.get("description")
            if not isinstance(description, str) or not description.strip():
                self.error(
                    f"{relative(skill_file)} frontmatter requires a string description"
                )

    def validate_json_data(self) -> None:
        schemas: dict[str, dict[str, Any]] = {}
        if not SCHEMAS_DIR.is_dir():
            self.error(f"missing schemas directory: {relative(SCHEMAS_DIR)}")
        else:
            schema_files = sorted(SCHEMAS_DIR.glob("*.json"))
            if not schema_files:
                self.error(f"no JSON schemas found in {relative(SCHEMAS_DIR)}")
            for schema_path in schema_files:
                schema = load_json(schema_path, self.errors)
                if schema is INVALID_JSON:
                    continue
                try:
                    Draft202012Validator.check_schema(schema)
                except SchemaError as exc:
                    self.error(
                        f"{relative(schema_path)} is not a valid Draft 2020-12 schema: "
                        f"{format_schema_error(exc)}"
                    )
                    continue
                schemas[schema_path.name] = schema

        if not DATA_DIR.is_dir():
            self.error(f"missing data directory: {relative(DATA_DIR)}")
            return

        json_files = sorted(DATA_DIR.rglob("*.json"))
        if not json_files:
            self.error(f"no formal JSON data found in {relative(DATA_DIR)}")

        loaded_data: dict[Path, Any] = {}
        for data_path in json_files:
            value = load_json(data_path, self.errors)
            if value is not INVALID_JSON:
                loaded_data[data_path] = value

        for jsonl_path in sorted(DATA_DIR.rglob("*.jsonl")):
            validate_json_lines(jsonl_path, self.errors)

        for rule in SCHEMA_RULES:
            matched_paths = sorted(DATA_DIR.glob(rule.pattern))
            if not matched_paths:
                continue
            schema = schemas.get(rule.schema_name)
            if schema is None:
                self.error(
                    f"cannot validate {rule.pattern}: missing valid schema "
                    f"schemas/{rule.schema_name}"
                )
                continue

            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            for data_path in matched_paths:
                instance = loaded_data.get(data_path)
                if data_path not in loaded_data:
                    continue
                validation_errors = sorted(
                    validator.iter_errors(instance),
                    key=lambda item: tuple(str(part) for part in item.absolute_path),
                )
                for validation_error in validation_errors[:20]:
                    location = format_json_path(validation_error.absolute_path)
                    self.error(
                        f"{relative(data_path)} fails {rule.schema_name} at "
                        f"{location}: {validation_error.message}"
                    )
                if len(validation_errors) > 20:
                    self.error(
                        f"{relative(data_path)} has "
                        f"{len(validation_errors) - 20} additional schema error(s)"
                    )

    def validate_daily_news(self) -> None:
        news_dir = DATA_DIR / "daily-news"
        if not news_dir.is_dir():
            self.error(f"missing daily news directory: {relative(news_dir)}")
            return

        seen_urls: dict[str, str] = {}
        seen_titles: dict[str, str] = {}
        for news_path in sorted(news_dir.glob("*.json")):
            file_date = news_path.stem
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", file_date):
                self.error(f"{relative(news_path)} must use a YYYY-MM-DD filename")
                continue

            news = load_json(news_path, self.errors)
            if news is INVALID_JSON:
                continue
            if not isinstance(news, dict):
                continue

            if news.get("date") != file_date:
                self.error(
                    f"{relative(news_path)} date {news.get('date')!r} "
                    f"does not match filename {file_date!r}"
                )
            meta = news.get("meta")
            meta_date = meta.get("date") if isinstance(meta, dict) else None
            if meta_date != file_date:
                self.error(
                    f"{relative(news_path)} meta.date {meta_date!r} "
                    f"does not match filename {file_date!r}"
                )

            items = news.get("items")
            if not isinstance(items, list):
                continue
            for index, item in enumerate(items):
                if not isinstance(item, dict):
                    continue
                item_location = f"{relative(news_path)} items[{index}]"
                self.check_duplicate(
                    "URL",
                    normalize_url(item.get("url")),
                    item_location,
                    seen_urls,
                )
                self.check_duplicate(
                    "title",
                    normalize_title(item.get("title")),
                    item_location,
                    seen_titles,
                )

    def check_duplicate(
        self,
        kind: str,
        value: str,
        location: str,
        seen: dict[str, str],
    ) -> None:
        if not value:
            return
        previous = seen.get(value)
        if previous is not None:
            self.error(f"duplicate daily-news {kind}: {previous} and {location}")
        else:
            seen[value] = location

    def validate_harness(self) -> None:
        if not HARNESS_CONFIG.is_file():
            self.error(f"missing Harness config: {relative(HARNESS_CONFIG)}")
            return
        config = load_json(HARNESS_CONFIG, self.errors)
        if config is INVALID_JSON:
            return
        if not isinstance(config, dict):
            self.error(f"{relative(HARNESS_CONFIG)} must contain a JSON object")
            return

        stages = first_nested_value(config, ("stages",), ("pipeline", "stages"))
        if not isinstance(stages, list):
            self.error(f"{relative(HARNESS_CONFIG)} must define a stages array")
        elif len(stages) != 8:
            self.error(
                f"{relative(HARNESS_CONFIG)} must define exactly 8 stages, "
                f"found {len(stages)}"
            )

        max_repair_rounds = first_nested_value(
            config,
            ("execution", "maxRepairRounds"),
        )
        if max_repair_rounds != 3:
            self.error(
                f"{relative(HARNESS_CONFIG)} execution.maxRepairRounds must be 3, "
                f"found {max_repair_rounds!r}"
            )

    def validate_legacy_references(self) -> None:
        for path in controlled_text_files():
            if is_migration_report(path):
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError as exc:
                self.error(f"cannot read controlled text {relative(path)}: {exc}")
                continue

            for line_number, line in enumerate(lines, start=1):
                normalized_line = line.replace("\\", "/")
                for label, parts, root_only in LEGACY_REFERENCES:
                    obsolete_path = "/".join(parts)
                    prefix = r"(?<![.\w/-])" if root_only else r"(?<![.\w-])"
                    pattern = re.compile(
                        rf"{prefix}{re.escape(obsolete_path)}(?=$|[/\s`'\"():])"
                    )
                    if pattern.search(normalized_line):
                        self.error(
                            f"{relative(path)}:{line_number} contains {label}: "
                            f"{obsolete_path}"
                        )

    def validate_legacy_roots(self) -> None:
        for directory_name in LEGACY_ROOTS:
            path = ROOT / directory_name
            if path.exists():
                self.error(f"legacy root directory still exists: {directory_name}/")


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("file must start with ---")

    try:
        closing_index = next(
            index for index, line in enumerate(lines[1:], start=1)
            if line.strip() == "---"
        )
    except StopIteration as exc:
        raise ValueError("missing closing ---") from exc

    if closing_index == 1:
        raise ValueError("frontmatter is empty")

    result: dict[str, str] = {}
    current_key: str | None = None
    key_pattern = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")
    for line_number, line in enumerate(lines[1:closing_index], start=2):
        if "\t" in line:
            raise ValueError(f"line {line_number} contains a tab")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[:1].isspace():
            if current_key is None:
                raise ValueError(f"line {line_number} has an orphan continuation")
            continue

        match = key_pattern.fullmatch(line)
        if match is None:
            raise ValueError(f"line {line_number} is not a key/value entry")
        key, raw_value = match.groups()
        if key in result:
            raise ValueError(f"line {line_number} repeats key {key!r}")
        value = (raw_value or "").strip()
        if value[:1] in {"'", '"'}:
            if len(value) < 2 or value[-1] != value[0]:
                raise ValueError(f"line {line_number} has an unterminated quote")
            value = value[1:-1]
        result[key] = value
        current_key = key

    return result


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{relative(path)} is not valid UTF-8 JSON: {exc}")
        return INVALID_JSON


def validate_json_lines(path: Path, errors: list[str]) -> None:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(
                        f"{relative(path)}:{line_number} is not valid JSONL: {exc.msg}"
                    )
                    return
    except (OSError, UnicodeError) as exc:
        errors.append(f"{relative(path)} cannot be read as UTF-8 JSONL: {exc}")


def first_nested_value(data: dict[str, Any], *paths: tuple[str, ...]) -> Any:
    for path in paths:
        current: Any = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                break
            current = current[key]
        else:
            return current
    return None


def controlled_text_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        candidates = (ROOT / line for line in result.stdout.splitlines() if line)
    except (OSError, subprocess.CalledProcessError):
        candidates = ROOT.rglob("*")

    files: list[Path] = []
    for path in candidates:
        if not path.is_file():
            continue
        relative_parts = path.relative_to(ROOT).parts
        if any(part in IGNORED_PARTS for part in relative_parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        files.append(path)
    return sorted(set(files))


def is_migration_report(path: Path) -> bool:
    return path.relative_to(ROOT).as_posix() == "docs/migration-report.md"


def normalize_url(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return ""
    raw = value.strip()
    try:
        parts = urlsplit(raw)
    except ValueError:
        return raw.casefold().rstrip("/")
    return urlunsplit(
        (
            parts.scheme.casefold(),
            parts.netloc.casefold(),
            parts.path.rstrip("/") or "/",
            parts.query,
            "",
        )
    )


def normalize_title(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).casefold()


def format_json_path(path: Iterable[Any]) -> str:
    parts = list(path)
    if not parts:
        return "$"
    rendered = "$"
    for part in parts:
        rendered += f"[{part}]" if isinstance(part, int) else f".{part}"
    return rendered


def format_schema_error(error: SchemaError) -> str:
    location = format_json_path(error.absolute_path)
    return f"{location}: {error.message}"


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


if __name__ == "__main__":
    raise SystemExit(ProjectValidator().run())
