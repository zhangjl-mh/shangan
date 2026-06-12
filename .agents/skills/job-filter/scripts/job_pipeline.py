#!/usr/bin/env python3
"""Download, normalize, screen, and validate official civil-service jobs."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator
from xml.etree import ElementTree as ET

import xlrd
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[4]
JOBS_DIR = ROOT / "data" / "jobs"
SOURCES_CONFIG = JOBS_DIR / "sources.json"
PROFILE_PATH = ROOT / "data" / "user-profile" / "profile.json"
CATALOG_PATH = JOBS_DIR / "catalog" / "positions.jsonl"
INDEX_PATH = JOBS_DIR / "index.json"
SCHEMA_PATH = ROOT / "schemas" / "job-filter.schema.json"
USER_AGENT = "shangan-job-pipeline/3.0"

XLSX_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "officeRel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "packageRel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "organization": ("部门名称", "招录机关", "单位名称", "机关名称"),
    "department": ("用人司局", "用人单位", "招录单位", "职位所在部门"),
    "title": ("招考职位", "职位名称", "职位", "岗位名称"),
    "positionCode": ("职位代码", "职位编码", "岗位代码", "招录职位代码"),
    "region": ("工作地点", "职位所在地", "工作地区", "行政区划", "地区"),
    "recruitCount": ("招考人数", "计划招录人数", "招录人数", "人数"),
    "majorRequirement": ("专业", "专业要求", "所学专业"),
    "educationRequirement": ("学历", "学历要求"),
    "degreeRequirement": ("学位", "学位要求"),
    "politicalRequirement": ("政治面貌", "政治面貌要求"),
    "grassrootsRequirement": ("基层工作最低年限", "基层工作经历", "基层工作年限"),
    "serviceProjectRequirement": ("服务基层项目工作经历", "服务基层项目经历"),
    "remarks": ("备注", "其他条件", "其他要求", "职位要求"),
}

REQUIRED_COLUMNS = ("organization", "title", "positionCode")
ALLOWED_OFFICIAL_SUFFIXES = (
    ".gov.cn",
    ".scs.gov.cn",
    ".beijing.gov.cn",
    ".tj.gov.cn",
    ".hebei.gov.cn",
    ".hebgwyks.gov.cn",
)


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def compact(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return re.sub(r"\s+", "", str(value)).strip()


def display(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return re.sub(r"\s+", " ", str(value)).strip()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def official_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme in {"http", "https"} and any(
        host == suffix.lstrip(".") or host.endswith(suffix)
        for suffix in ALLOWED_OFFICIAL_SUFFIXES
    )


def download_attachment(attachment: dict[str, Any], force: bool = False) -> dict[str, Any]:
    url = attachment["url"]
    if not official_url(url):
        raise ValueError(f"non-official attachment URL rejected: {url}")

    destination = ROOT / attachment["path"]
    expected = attachment.get("sha256")
    if destination.is_file() and not force:
        actual = sha256_file(destination)
        if not expected or actual == expected:
            return artifact_metadata(attachment, destination)

    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            with temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
        if temporary.stat().st_size == 0:
            raise ValueError(f"downloaded empty attachment: {url}")
        actual = sha256_file(temporary)
        if expected and actual != expected:
            raise ValueError(
                f"attachment hash changed for {attachment['id']}: "
                f"expected {expected}, got {actual}"
            )
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return artifact_metadata(attachment, destination)


def artifact_metadata(attachment: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "id": attachment["id"],
        "url": attachment["url"],
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def column_index(cell_ref: str) -> int:
    letters = "".join(char for char in cell_ref if char.isalpha())
    result = 0
    for char in letters.upper():
        result = result * 26 + ord(char) - 64
    return result - 1


def xlsx_tables(data: bytes) -> Iterator[tuple[str, list[list[str]]]]:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", XLSX_NS):
                shared_strings.append(
                    "".join(
                        node.text or ""
                        for node in item.iter(f"{{{XLSX_NS['main']}}}t")
                    )
                )

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            relation.attrib["Id"]: relation.attrib["Target"]
            for relation in relations.findall("packageRel:Relationship", XLSX_NS)
        }
        sheets = workbook.find("main:sheets", XLSX_NS)
        if sheets is None:
            return

        for sheet in sheets:
            name = sheet.attrib["name"]
            relation_id = sheet.attrib[f"{{{XLSX_NS['officeRel']}}}id"]
            target = targets[relation_id].lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            root = ET.fromstring(archive.read(target))
            rows: list[list[str]] = []
            for row in root.findall(".//main:sheetData/main:row", XLSX_NS):
                values: dict[int, str] = {}
                for cell in row.findall("main:c", XLSX_NS):
                    index = column_index(cell.attrib.get("r", "A1"))
                    cell_type = cell.attrib.get("t")
                    if cell_type == "inlineStr":
                        value = "".join(
                            node.text or ""
                            for node in cell.findall(".//main:t", XLSX_NS)
                        )
                    else:
                        value_node = cell.find("main:v", XLSX_NS)
                        value = "" if value_node is None else (value_node.text or "")
                        if cell_type == "s" and value:
                            value = shared_strings[int(value)]
                    values[index] = display(value)
                rows.append(
                    [values.get(index, "") for index in range(max(values, default=-1) + 1)]
                )
            yield name, rows


def xls_tables(data: bytes) -> Iterator[tuple[str, list[list[str]]]]:
    workbook = xlrd.open_workbook(file_contents=data)
    for sheet in workbook.sheets():
        yield sheet.name, [
            [display(sheet.cell_value(row, column)) for column in range(sheet.ncols)]
            for row in range(sheet.nrows)
        ]


def attachment_tables(path: Path) -> Iterator[tuple[str, str, list[list[str]]]]:
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        for sheet, rows in xlsx_tables(data):
            yield path.name, sheet, rows
        return
    if suffix == ".xls":
        for sheet, rows in xls_tables(data):
            yield path.name, sheet, rows
        return
    if suffix != ".zip":
        raise ValueError(f"unsupported position attachment: {path}")

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.namelist():
            member_suffix = Path(member).suffix.lower()
            if member_suffix not in {".xls", ".xlsx"} or member.endswith("/"):
                continue
            member_data = archive.read(member)
            tables = xlsx_tables(member_data) if member_suffix == ".xlsx" else xls_tables(member_data)
            for sheet, rows in tables:
                yield member, sheet, rows


def canonical_header(value: str) -> str | None:
    normalized = compact(value).replace("（", "(").replace("）", ")")
    for field, aliases in COLUMN_ALIASES.items():
        if any(normalized == compact(alias) for alias in aliases):
            return field
    return None


def find_header(rows: list[list[str]]) -> tuple[int, dict[str, int]] | None:
    best: tuple[int, dict[str, int]] | None = None
    for row_index, row in enumerate(rows[:80]):
        mapping = {
            field: column_index_
            for column_index_, value in enumerate(row)
            if (field := canonical_header(value)) is not None
        }
        if all(field in mapping for field in REQUIRED_COLUMNS):
            if best is None or len(mapping) > len(best[1]):
                best = (row_index, mapping)
    return best


def stable_id(exam_id: str, cycle: str, organization: str, code: str, title: str) -> str:
    digest = sha256_bytes(
        "|".join((exam_id, cycle, organization, code, title)).encode("utf-8")
    )[:20]
    return f"{exam_id}-{cycle}-{digest}"


def parse_source(source: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    positions: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for attachment in source["attachments"]:
        if attachment.get("kind", "positions") != "positions":
            continue
        path = ROOT / attachment["path"]
        try:
            tables = list(attachment_tables(path))
        except Exception as exc:
            errors.append({"source": attachment["id"], "message": str(exc)})
            continue
        for member, sheet, rows in tables:
            header = find_header(rows)
            if header is None:
                continue
            header_index, mapping = header
            for row_number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
                values = {
                    field: display(row[index]) if index < len(row) else ""
                    for field, index in mapping.items()
                }
                if not any(values.values()):
                    continue
                if not all(values.get(field) for field in REQUIRED_COLUMNS):
                    errors.append(
                        {
                            "source": attachment["id"],
                            "message": f"{member}/{sheet} row {row_number} lacks required fields",
                        }
                    )
                    continue
                code = values["positionCode"]
                positions.append(
                    {
                        "id": stable_id(
                            source["examId"],
                            source["cycle"],
                            values["organization"],
                            code,
                            values["title"],
                        ),
                        "examId": source["examId"],
                        "examLabel": source["label"],
                        "cycle": source["cycle"],
                        "organization": values["organization"],
                        "department": values.get("department", ""),
                        "title": values["title"],
                        "positionCode": code,
                        "region": values.get("region", source.get("region", "")),
                        "recruitCount": integer_or_zero(values.get("recruitCount")),
                        "requirements": {
                            "major": values.get("majorRequirement", ""),
                            "education": values.get("educationRequirement", ""),
                            "degree": values.get("degreeRequirement", ""),
                            "politicalStatus": values.get("politicalRequirement", ""),
                            "grassrootsYears": values.get("grassrootsRequirement", ""),
                            "serviceProject": values.get("serviceProjectRequirement", ""),
                            "remarks": values.get("remarks", ""),
                        },
                        "registration": source["registration"],
                        "source": {
                            "attachmentId": attachment["id"],
                            "url": attachment["url"],
                            "portalUrl": source["portalUrl"],
                            "member": member,
                            "sheet": sheet,
                            "row": row_number,
                        },
                    }
                )
    return positions, errors


def integer_or_zero(value: Any) -> int:
    match = re.search(r"\d+", display(value))
    return int(match.group()) if match else 0


def is_unlimited(value: str) -> bool:
    text = compact(value)
    return not text or any(marker in text for marker in ("不限", "无要求", "不限制"))


def decision(field: str, result: str, reason: str) -> dict[str, str]:
    return {"field": field, "result": result, "reason": reason}


def evaluate_position(position: dict[str, Any], profile: dict[str, Any], as_of: datetime) -> dict[str, Any]:
    basic = profile["basic"]
    experience = profile["experience"]
    qualifications = profile["qualifications"]
    requirements = position["requirements"]
    checks: list[dict[str, str]] = []

    education = compact(requirements["education"])
    if is_unlimited(education) or "本科" in education or "大专及以上" in education or "专科及以上" in education:
        checks.append(decision("education", "pass", "本科学历满足岗位学历口径。"))
    elif any(marker in education for marker in ("硕士", "研究生", "博士")):
        checks.append(decision("education", "fail", f"岗位学历要求为：{requirements['education']}"))
    else:
        checks.append(decision("education", "unknown", f"无法自动判断学历口径：{requirements['education']}"))

    degree = compact(requirements["degree"])
    profile_degree = compact(basic.get("degree"))
    if is_unlimited(degree):
        checks.append(decision("degree", "pass", "岗位未限制学位。"))
    elif profile_degree and ("学士" in degree or "相应学位" in degree or profile_degree in degree):
        checks.append(decision("degree", "pass", "学士学位满足岗位要求。"))
    elif profile_degree == "unknown":
        checks.append(decision("degree", "unknown", "画像尚未确认学位。"))
    else:
        checks.append(decision("degree", "fail", f"岗位学位要求为：{requirements['degree']}"))

    major = compact(requirements["major"])
    major_code = compact(basic.get("majorCode"))
    profile_major = compact(basic.get("major"))
    computer_markers = ("计算机", "0809", "软件工程", "网络工程", "信息安全")
    if is_unlimited(major):
        checks.append(decision("major", "pass", "岗位专业不限。"))
    elif profile_major in major or (major_code and major_code in major) or any(marker in major for marker in computer_markers):
        checks.append(decision("major", "pass", "计算机科学与技术符合岗位专业表述。"))
    else:
        checks.append(decision("major", "fail", f"岗位专业要求为：{requirements['major']}"))

    political = compact(requirements["politicalStatus"])
    profile_political = compact(basic.get("politicalStatus"))
    if is_unlimited(political):
        checks.append(decision("politicalStatus", "pass", "岗位政治面貌不限。"))
    elif "党员" in political and "党员" in profile_political:
        checks.append(decision("politicalStatus", "pass", "中共党员身份满足岗位要求。"))
    elif profile_political == "unknown":
        checks.append(decision("politicalStatus", "unknown", "画像尚未确认政治面貌。"))
    else:
        checks.append(decision("politicalStatus", "fail", f"岗位政治面貌要求为：{requirements['politicalStatus']}"))

    fresh_text = compact(requirements["remarks"])
    if any(marker in fresh_text for marker in ("应届高校毕业生", "应届毕业生", "2026届")):
        checks.append(
            decision(
                "freshGraduateStatus",
                "pass" if basic.get("freshGraduateStatus") in (True, "是", "应届") else "fail",
                "岗位限制应届毕业生，画像为2023年毕业且非应届。",
            )
        )

    grassroots = compact(requirements["grassrootsYears"])
    if not is_unlimited(grassroots) and not grassroots.startswith("0"):
        value = experience.get("grassrootsYears", "unknown")
        checks.append(
            decision(
                "grassrootsYears",
                "unknown" if value == "unknown" else "pass",
                "岗位要求基层工作经历，画像尚需人工核对。"
                if value == "unknown"
                else "画像已填写基层工作经历，仍需对照原文。",
            )
        )

    service = compact(requirements["serviceProject"])
    if not is_unlimited(service):
        value = experience.get("veteranOrServiceProgram", "unknown")
        checks.append(
            decision(
                "serviceProject",
                "unknown" if value == "unknown" else "pass",
                "岗位要求服务基层项目经历，画像尚需人工核对。"
                if value == "unknown"
                else "画像已填写服务项目经历，仍需对照原文。",
            )
        )

    unknown_markers = {
        "english": ("英语四级", "英语六级", "大学英语", "CET"),
        "professional": ("资格证", "职业资格", "法律职业资格"),
        "workYears": ("工作经历", "工作经验", "从事相关工作"),
    }
    for field, markers in unknown_markers.items():
        if any(marker.casefold() in requirements["remarks"].casefold() for marker in markers):
            group = qualifications if field != "workYears" else experience
            value = group.get(field, "unknown")
            if value == "unknown":
                checks.append(decision(field, "unknown", f"备注涉及{field}，画像尚未填写。"))

    failures = [item for item in checks if item["result"] == "fail"]
    unknowns = [item for item in checks if item["result"] == "unknown"]
    eligibility = "ineligible" if failures else "needs_confirmation" if unknowns else "eligible"
    closes_at = datetime.fromisoformat(position["registration"]["closesAt"])
    opens_at = datetime.fromisoformat(position["registration"]["opensAt"])
    if closes_at.tzinfo is None:
        closes_at = closes_at.replace(tzinfo=timezone.utc)
    if opens_at.tzinfo is None:
        opens_at = opens_at.replace(tzinfo=timezone.utc)
    status = "active" if opens_at <= as_of.astimezone(opens_at.tzinfo) <= closes_at else "historical"

    return {
        **position,
        "eligibility": eligibility,
        "timingStatus": status,
        "matchReasons": [item["reason"] for item in checks if item["result"] == "pass"],
        "confirmationFields": [item["field"] for item in unknowns],
        "exclusionReasons": [item["reason"] for item in failures],
        "decisions": checks,
    }


def load_sources() -> dict[str, Any]:
    config = read_json(SOURCES_CONFIG)
    if config.get("cycle") != "2026":
        raise ValueError("first release requires sources.json cycle 2026")
    for source in config.get("sources", []):
        if not official_url(source["portalUrl"]):
            raise ValueError(f"non-official portal URL rejected: {source['portalUrl']}")
        for attachment in source.get("attachments", []):
            if not official_url(attachment["url"]):
                raise ValueError(f"non-official attachment URL rejected: {attachment['url']}")
            path = (ROOT / attachment["path"]).resolve()
            source_root = (JOBS_DIR / "sources").resolve()
            if path != source_root and source_root not in path.parents:
                raise ValueError(f"attachment path escapes data/jobs/sources: {path}")
    return config


def download_all(config: dict[str, Any], force: bool = False) -> list[dict[str, Any]]:
    downloaded: list[dict[str, Any]] = []
    for source in config["sources"]:
        for attachment in source["attachments"]:
            downloaded.append(download_attachment(attachment, force=force))
    return downloaded


def build(config: dict[str, Any], as_of: datetime) -> dict[str, Any]:
    profile = read_json(PROFILE_PATH)
    profile_bytes = json.dumps(profile, ensure_ascii=False, sort_keys=True).encode("utf-8")
    all_positions: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    source_index: list[dict[str, Any]] = []

    for source in config["sources"]:
        positions, source_errors = parse_source(source)
        all_positions.extend(positions)
        errors.extend(source_errors)
        source_index.append(
            {
                "examId": source["examId"],
                "label": source["label"],
                "portalUrl": source["portalUrl"],
                "registration": source["registration"],
                "attachments": [
                    artifact_metadata(attachment, ROOT / attachment["path"])
                    for attachment in source["attachments"]
                ],
            }
        )

    unique: dict[str, dict[str, Any]] = {}
    for position in all_positions:
        unique[position["id"]] = position
    evaluated = [
        evaluate_position(position, profile, as_of)
        for position in sorted(
            unique.values(),
            key=lambda item: (item["examId"], item["organization"], item["positionCode"]),
        )
    ]

    CATALOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CATALOG_PATH.open("w", encoding="utf-8", newline="\n") as output:
        for position in evaluated:
            output.write(json.dumps(position, ensure_ascii=False, separators=(",", ":")) + "\n")

    eligibility = Counter(item["eligibility"] for item in evaluated)
    timing = Counter(item["timingStatus"] for item in evaluated)
    unknown_fields = sorted(
        key
        for group in ("basic", "experience", "qualifications", "preferences")
        for key, value in profile.get(group, {}).items()
        if value == "unknown"
    )
    index = {
        "schemaVersion": "3.0",
        "generatedAt": now_iso(),
        "cycle": config["cycle"],
        "profileSnapshot": {
            "sha256": sha256_bytes(profile_bytes),
            "updatedAt": profile["updatedAt"],
            "unknownFields": unknown_fields,
        },
        "catalog": {
            "path": CATALOG_PATH.relative_to(ROOT).as_posix(),
            "rowCount": len(evaluated),
            "sha256": sha256_file(CATALOG_PATH),
        },
        "sources": source_index,
        "stats": {
            "total": len(evaluated),
            "eligible": eligibility["eligible"],
            "needsConfirmation": eligibility["needs_confirmation"],
            "ineligible": eligibility["ineligible"],
            "active": timing["active"],
            "historical": timing["historical"],
        },
        "errors": errors,
    }
    write_json(INDEX_PATH, index)
    validate_index(index)
    return index


def validate_index(index: dict[str, Any] | None = None) -> None:
    instance = index if index is not None else read_json(INDEX_PATH)
    schema = read_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    failures = sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
    if failures:
        raise ValueError(
            "job index validation failed: "
            + "; ".join(f"{list(error.path)}: {error.message}" for error in failures[:20])
        )
    catalog = ROOT / instance["catalog"]["path"]
    if not catalog.is_file():
        raise FileNotFoundError(f"missing catalog: {catalog}")
    rows = 0
    with catalog.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            required = {
                "id",
                "examId",
                "organization",
                "title",
                "positionCode",
                "eligibility",
                "timingStatus",
                "source",
            }
            missing = required - value.keys()
            if missing:
                raise ValueError(f"catalog line {line_number} missing: {sorted(missing)}")
            rows += 1
    if rows != instance["catalog"]["rowCount"]:
        raise ValueError(
            f"catalog row mismatch: index={instance['catalog']['rowCount']}, actual={rows}"
        )
    if sha256_file(catalog) != instance["catalog"]["sha256"]:
        raise ValueError("catalog sha256 mismatch")


def parse_as_of(value: str | None) -> datetime:
    if not value:
        return datetime.now().astimezone()
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("download", "build", "all", "validate"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--as-of", default="")
    args = parser.parse_args()
    config = load_sources()

    if args.command in {"download", "all"}:
        metadata = download_all(config, force=args.force)
        print(json.dumps({"downloaded": len(metadata), "artifacts": metadata}, ensure_ascii=False))
    if args.command in {"build", "all"}:
        index = build(config, parse_as_of(args.as_of))
        print(json.dumps({"stats": index["stats"], "errors": len(index["errors"])}, ensure_ascii=False))
    if args.command == "validate":
        validate_index()
        print("job data validation passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
