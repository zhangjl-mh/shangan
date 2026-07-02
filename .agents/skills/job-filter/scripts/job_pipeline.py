#!/usr/bin/env python3
"""Download, normalize, screen, and validate official civil-service jobs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import time
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
SOURCE_REGISTRY_PATH = JOBS_DIR / "source-registry.json"
PROFILE_PATH = ROOT / "data" / "user-profile" / "profile.json"
DATABASE_PATH = JOBS_DIR / "jobs.sqlite"
DATABASE_SCHEMA_PATH = ROOT / "schemas" / "job-database.sql"
LEGACY_INDEX_PATH = JOBS_DIR / "index.json"
LEGACY_CATALOG_DIR = JOBS_DIR / "catalog"
SCHEMA_PATH = ROOT / "schemas" / "job-filter.schema.json"
POSITION_SCHEMA_PATH = ROOT / "schemas" / "job-position.schema.json"
SOURCES_SCHEMA_PATH = ROOT / "schemas" / "job-sources.schema.json"
SOURCE_REGISTRY_SCHEMA_PATH = ROOT / "schemas" / "job-source-registry.schema.json"
USER_AGENT = "shangan-job-pipeline/5.0"
DATABASE_USER_VERSION = 500
SUPPORTED_FORMATS = {"xlsx", "xls", "csv", "tsv", "zip"}
MAX_ZIP_MEMBER_SIZE = 64 * 1024 * 1024
MAX_ZIP_TOTAL_SIZE = 256 * 1024 * 1024
SCHEMA_VALIDATORS: dict[Path, Draft202012Validator] = {}

XLSX_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "officeRel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "packageRel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "organization": (
        "部门名称",
        "招录机关",
        "单位名称",
        "用人单位名称",
        "机关名称",
        "招考单位",
        "部门",
    ),
    "department": (
        "用人司局",
        "用人单位",
        "用人部门",
        "招录单位",
        "职位所在部门",
        "招考部门",
        "岗位类别",
        "单位",
    ),
    "title": ("招考职位", "职位名称", "职位", "岗位名称", "招聘岗位"),
    "positionCode": ("职位代码", "职位编码", "岗位代码", "招录职位代码", "代码"),
    "region": ("工作地点", "职位所在地", "工作地区", "行政区划", "地区", "考区"),
    "recruitCount": (
        "招考人数",
        "计划招录人数",
        "招录人数",
        "招聘人数",
        "拟招聘人数",
        "计划招聘人数",
        "招考数量",
        "人数",
    ),
    "majorRequirement": ("专业", "专业要求", "所学专业"),
    "educationRequirement": ("学历", "学历要求", "学历低限", "文化程度"),
    "degreeRequirement": ("学位", "学位要求", "学位低限"),
    "educationDegreeRequirement": ("学历学位",),
    "politicalRequirement": ("政治面貌", "政治面貌要求"),
    "grassrootsRequirement": (
        "基层工作最低年限",
        "基层工作经历最低年限",
        "基层工作经历",
        "基层工作年限",
        "专业工作年限",
    ),
    "serviceProjectRequirement": ("服务基层项目工作经历", "服务基层项目经历"),
    "freshGraduateRequirement": ("招录对象", "招聘范围", "来源类别"),
    "ageRequirement": ("年龄", "年龄要求"),
    "genderRequirement": ("性别", "性别要求"),
    "householdRequirement": ("户别要求", "户籍要求", "户籍或生源要求"),
    "certificateRequirement": ("资格证书", "证书要求"),
    "additionalRequirement": ("其他条件", "其它条件"),
    "remarks": (
        "备注",
        "其他条件",
        "其他要求",
        "职位要求",
        "其他资格条件",
        "任职要求",
    ),
}

REQUIRED_COLUMNS = ("organization", "title", "positionCode")
REQUIRED_HEADER_COLUMNS = ("organization", "title")
REQUIRED_CATEGORIES = (
    "civil_service",
    "institution",
    "military_civilian",
    "state_owned_enterprise",
)
REQUIREMENT_COLUMN_FIELDS = {
    "major": "majorRequirement",
    "education": "educationRequirement",
    "degree": "degreeRequirement",
    "politicalStatus": "politicalRequirement",
    "grassrootsYears": "grassrootsRequirement",
    "serviceProject": "serviceProjectRequirement",
    "freshGraduate": "freshGraduateRequirement",
    "age": "ageRequirement",
    "gender": "genderRequirement",
    "household": "householdRequirement",
    "certificate": "certificateRequirement",
    "remarks": "remarks",
}
REQUIREMENT_KEYS = (
    "major",
    "education",
    "degree",
    "politicalStatus",
    "grassrootsYears",
    "serviceProject",
    "freshGraduate",
    "age",
    "gender",
    "household",
    "certificate",
    "remarks",
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


def write_jsonl(path: Path, values: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for value in values:
            output.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


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


def sha256_jsonl(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    canonical = "\n".join(text.splitlines())
    if canonical:
        canonical += "\n"
    return sha256_bytes(canonical.encode("utf-8"))


def official_url(url: str, allowed_hosts: Iterable[str]) -> bool:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    normalized_hosts = tuple(str(value).strip().lower() for value in allowed_hosts)
    return parsed.scheme in {"http", "https"} and any(
        host == allowed or host.endswith(f".{allowed}")
        for allowed in normalized_hosts
    )


def download_attachment(
    attachment: dict[str, Any],
    allowed_hosts: Iterable[str] | None = None,
    force: bool = False,
) -> dict[str, Any]:
    url = attachment["url"]
    hosts = tuple(allowed_hosts or ())
    if not hosts or not official_url(url, hosts):
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
        for depth in (1, 2, 3):
            header_rows = rows[row_index : row_index + depth]
            width = max((len(item) for item in header_rows), default=0)
            mapping: dict[str, int] = {}
            for column_index_ in range(width):
                for header_row in reversed(header_rows):
                    value = (
                        header_row[column_index_]
                        if column_index_ < len(header_row)
                        else ""
                    )
                    field = canonical_header(value)
                    if field is not None:
                        mapping[field] = column_index_
                        break
            if all(field in mapping for field in REQUIRED_HEADER_COLUMNS):
                if best is None or len(mapping) > len(best[1]):
                    best = (row_index + depth - 1, mapping)
    return best


def embedded_requirements(values: dict[str, str]) -> dict[str, str]:
    text = "；".join(
        value
        for value in (
            values.get("additionalRequirement", ""),
            values.get("remarks", ""),
        )
        if value
    )
    extracted: dict[str, str] = {}
    compact_text = compact(text)
    if "专业不限" in compact_text:
        extracted["major"] = "不限"
    else:
        major_match = re.search(
            r"(?:学历|学位)[，,]\s*([^；;。]+?)(?:等)?相关专业",
            text,
        )
        if major_match:
            extracted["major"] = major_match.group(1).strip("，,；; ")

    age_match = re.search(r"年龄\s*(\d+\s*周岁(?:及)?以下)", text)
    if age_match:
        extracted["age"] = age_match.group(1)

    years_match = re.search(
        r"(?:具有|有)(\d+\s*年(?:及)?以上(?:相关)?工作经验)",
        text,
    )
    if years_match:
        extracted["grassrootsYears"] = years_match.group(1)

    if "应届毕业生" in text:
        extracted["freshGraduate"] = "应届毕业生"
    if re.search(r"(?:^|[;；，,])\s*男(?:[;；，,]|$)", text):
        extracted["gender"] = "男"
    elif re.search(r"(?:^|[;；，,])\s*女(?:[;；，,]|$)", text):
        extracted["gender"] = "女"
    political_match = re.search(r"中共(?:正式|预备)?党员", text)
    if political_match:
        extracted["politicalStatus"] = political_match.group()
    return extracted


def stable_id(source_id: str, cycle: str, organization: str, code: str, title: str) -> str:
    digest = sha256_bytes(
        "|".join((source_id, cycle, organization, code, title)).encode("utf-8")
    )[:20]
    return f"{source_id}-{cycle}-{digest}"


def explicit_unlimited(value: Any) -> bool:
    text = compact(value)
    return bool(text) and (
        text
        in {
            "无",
            "不限",
            "无限制",
            "无要求",
            "不限制",
            "否",
            "专业不限",
            "学历不限",
            "学位不限",
        }
    )


def requirement_state(
    field: str,
    value: Any,
    mapping: dict[str, int],
    source: dict[str, Any],
) -> str:
    text = display(value)
    if explicit_unlimited(text):
        return "unrestricted"
    if text:
        return "specified"
    aliases = {REQUIREMENT_COLUMN_FIELDS[field]}
    if field in {"education", "degree"}:
        aliases.add("educationDegreeRequirement")
    column_present = bool(aliases.intersection(mapping))
    blank_unrestricted = field in source.get("blankMeansUnrestricted", [])
    if column_present and blank_unrestricted:
        return "unrestricted"
    return "missing"


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
                errors.append(
                    {
                        "source": attachment["id"],
                        "message": f"{member}/{sheet} has no recognized position header",
                    }
                )
                continue
            header_index, mapping = header
            forward_fill: dict[str, str] = {}
            for row_number, row in enumerate(rows[header_index + 1 :], start=header_index + 2):
                values = {
                    field: display(row[index]) if index < len(row) else ""
                    for field, index in mapping.items()
                }
                for field in source.get("forwardFillFields", []):
                    if values.get(field):
                        forward_fill[field] = values[field]
                    elif forward_fill.get(field):
                        values[field] = forward_fill[field]
                if not any(values.values()):
                    continue
                required_columns = (
                    REQUIRED_HEADER_COLUMNS
                    if source.get("allowMissingPositionCode")
                    else REQUIRED_COLUMNS
                )
                if not all(values.get(field) for field in required_columns):
                    errors.append(
                        {
                            "source": attachment["id"],
                            "message": f"{member}/{sheet} row {row_number} lacks required fields",
                        }
                    )
                    continue
                code = values.get("positionCode") or f"官方表第{row_number}行"
                organization = values["organization"]
                department = values.get("department", "")
                if source.get("organizationColumnAsDepartment"):
                    department = organization
                    organization = source.get("defaultOrganization", "")
                elif source.get("defaultOrganization"):
                    organization = source["defaultOrganization"]
                combined_education = values.get("educationDegreeRequirement", "")
                education = values.get("educationRequirement", "")
                degree = values.get("degreeRequirement", "")
                if combined_education:
                    parts = [
                        part.strip()
                        for part in re.split(r"[;；]", combined_education)
                        if part.strip()
                    ]
                    education = parts[0] if parts else combined_education
                    degree = parts[1] if len(parts) > 1 else ""
                grassroots = values.get("grassrootsRequirement", "")
                fresh_graduate = values.get("freshGraduateRequirement", "")
                if "应届" in compact(grassroots):
                    fresh_graduate = grassroots
                    grassroots = ""
                extracted = embedded_requirements(values)
                education = education or extracted.get("education", "")
                degree = degree or extracted.get("degree", "")
                grassroots = grassroots or extracted.get("grassrootsYears", "")
                fresh_graduate = fresh_graduate or extracted.get("freshGraduate", "")
                remarks = "；".join(
                    value
                    for value in (
                        fresh_graduate,
                        values.get("ageRequirement", ""),
                        values.get("genderRequirement", ""),
                        values.get("householdRequirement", ""),
                        values.get("certificateRequirement", ""),
                        values.get("additionalRequirement", ""),
                        values.get("remarks", ""),
                    )
                    if value and not is_unlimited(value)
                )
                requirements = {
                    "major": values.get("majorRequirement", "")
                    or extracted.get("major", ""),
                    "education": education,
                    "degree": degree,
                    "politicalStatus": values.get("politicalRequirement", "")
                    or extracted.get("politicalStatus", ""),
                    "grassrootsYears": grassroots,
                    "serviceProject": values.get("serviceProjectRequirement", ""),
                    "freshGraduate": fresh_graduate,
                    "age": values.get("ageRequirement", "")
                    or extracted.get("age", ""),
                    "gender": values.get("genderRequirement", "")
                    or extracted.get("gender", ""),
                    "household": values.get("householdRequirement", ""),
                    "certificate": values.get("certificateRequirement", ""),
                    "remarks": remarks,
                }
                states = {
                    field: requirement_state(field, value, mapping, source)
                    for field, value in requirements.items()
                }
                if "应届" in compact(values.get("grassrootsRequirement", "")):
                    states["freshGraduate"] = "specified"
                    states["grassrootsYears"] = (
                        "unrestricted"
                        if "grassrootsYears" in source.get("blankMeansUnrestricted", [])
                        else "missing"
                    )
                positions.append(
                    {
                        "id": stable_id(
                            source["sourceId"],
                            source["cycle"],
                            organization,
                            code,
                            values["title"],
                        ),
                        "sourceId": source["sourceId"],
                        "sourceLabel": source["label"],
                        "category": source["category"],
                        "cycle": source["cycle"],
                        "batchStatus": source["selectionMode"],
                        "examAt": source.get("examAt"),
                        "organization": organization,
                        "department": department,
                        "title": values["title"],
                        "positionCode": code,
                        "region": values.get("region", source.get("region", "")),
                        "recruitCount": integer_or_zero(values.get("recruitCount")),
                        "requirements": requirements,
                        "requirementStates": states,
                        "registration": source["registration"],
                        "source": {
                            "attachmentId": attachment["id"],
                            "url": attachment["url"],
                            "portalUrl": source["portalUrl"],
                            "evidenceUrl": source["evidenceUrl"],
                            "member": member,
                            "sheet": sheet,
                            "row": row_number,
                        },
                    }
                )
    if not positions:
        errors.append(
            {
                "source": source["sourceId"],
                "message": "official position attachments produced zero rows",
            }
        )
    return positions, errors


def integer_or_zero(value: Any) -> int:
    match = re.search(r"\d+", display(value))
    return int(match.group()) if match else 0


def is_unlimited(value: str) -> bool:
    return explicit_unlimited(value)


def decision(field: str, result: str, reason: str) -> dict[str, str]:
    return {"field": field, "result": result, "reason": reason}


def requirement_gate(
    position: dict[str, Any],
    field: str,
    label: str,
) -> dict[str, str] | None:
    state = position["requirementStates"].get(field, "unparsed")
    if state in {"missing", "unparsed"}:
        return decision(field, "unknown", f"{label}缺少可核验的官方字段。")
    if state == "unrestricted":
        return decision(field, "pass", f"岗位{label}不限。")
    return None


def education_rank(value: Any) -> int | None:
    text = compact(value)
    if not text or text == "unknown":
        return None
    for marker, rank in (
        ("博士", 6),
        ("硕士", 5),
        ("研究生", 5),
        ("本科", 4),
        ("学士", 4),
        ("大专", 3),
        ("专科", 3),
        ("中专", 2),
        ("高中", 1),
    ):
        if marker in text:
            return rank
    return None


def evaluate_education(
    position: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, str]:
    gated = requirement_gate(position, "education", "学历")
    if gated is not None:
        return gated
    raw = compact(position["requirements"]["education"])
    profile_raw = profile["basic"].get("education")
    profile_rank = education_rank(profile_raw)
    if profile_rank is None:
        return decision("education", "unknown", "画像学历尚未确认。")

    minimums = (
        (("博士",), 6),
        (("硕士研究生及以上", "研究生及以上", "硕士及以上"), 5),
        (("本科及以上", "大学本科及以上"), 4),
        (("大专及以上", "专科及以上"), 3),
        (("中专及以上",), 2),
    )
    for markers, minimum in minimums:
        if any(marker in raw for marker in markers):
            return decision(
                "education",
                "pass" if profile_rank >= minimum else "fail",
                f"画像学历为{profile_raw}，岗位学历要求为：{position['requirements']['education']}",
            )

    exact_markers = (
        ("仅限硕士研究生", 5),
        ("仅限研究生", 5),
        ("仅限本科", 4),
        ("本科", 4),
        ("大专", 3),
        ("专科", 3),
    )
    for marker, required in exact_markers:
        if marker in raw:
            return decision(
                "education",
                "pass" if profile_rank == required else "fail",
                f"画像学历为{profile_raw}，岗位学历要求为：{position['requirements']['education']}",
            )
    return decision(
        "education",
        "unknown",
        f"无法可靠解析岗位学历口径：{position['requirements']['education']}",
    )


def evaluate_degree(
    position: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, str]:
    gated = requirement_gate(position, "degree", "学位")
    if gated is not None:
        return gated
    raw = compact(position["requirements"]["degree"])
    profile_degree = compact(profile["basic"].get("degree"))
    if not profile_degree or profile_degree == "unknown":
        return decision("degree", "unknown", "画像学位尚未确认。")
    if any(
        marker in raw
        for marker in (
            "与最高学历相对应的学位",
            "与学历相对应的学位",
            "取得相应学位",
            "相应学位",
        )
    ):
        return decision("degree", "pass", f"{profile_degree}满足相应学位要求。")

    profile_rank = education_rank(profile_degree)
    requirement_rank = education_rank(raw)
    if profile_rank is None or requirement_rank is None:
        return decision(
            "degree",
            "unknown",
            f"无法可靠解析岗位学位口径：{position['requirements']['degree']}",
        )
    is_minimum = "及以上" in raw or "以上学位" in raw
    passed = profile_rank >= requirement_rank if is_minimum else profile_rank == requirement_rank
    return decision(
        "degree",
        "pass" if passed else "fail",
        f"画像学位为{profile_degree}，岗位学位要求为：{position['requirements']['degree']}",
    )


def select_major_branch(raw: str, education: Any) -> tuple[str, bool]:
    text = display(raw)
    if "本科" not in text or "研究生" not in text:
        return text, True
    profile_rank = education_rank(education)
    if profile_rank is None:
        return text, False
    bachelor = re.search(
        r"本科\s*[:：]\s*(.*?)(?=研究生\s*[:：])",
        text,
        flags=re.DOTALL,
    )
    graduate = re.search(r"研究生\s*[:：]\s*(.*)$", text, flags=re.DOTALL)
    selected = graduate if profile_rank >= 5 else bachelor
    return (selected.group(1).strip(), True) if selected else (text, False)


def evaluate_major(
    position: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, str]:
    gated = requirement_gate(position, "major", "专业")
    if gated is not None:
        return gated
    requirements = position["requirements"]
    branch, parsed = select_major_branch(
        requirements["major"],
        profile["basic"].get("education"),
    )
    if not parsed:
        return decision("major", "unknown", "岗位专业按学历分段，但画像学历无法用于选段。")
    text = compact(branch)
    profile_major = compact(profile["basic"].get("major"))
    major_code = compact(profile["basic"].get("majorCode"))
    if not profile_major or profile_major == "unknown":
        return decision("major", "unknown", "画像专业尚未确认。")
    if any(
        marker in text
        for marker in (
            f"不含{profile_major}",
            f"不包括{profile_major}",
            f"除{profile_major}",
        )
    ):
        return decision(
            "major",
            "fail",
            f"岗位专业明确排除{profile_major}。",
        )
    exact_name = profile_major in text
    exact_code = bool(
        major_code
        and re.search(rf"(?<!\d){re.escape(major_code)}(?!\d)", text)
    )
    parent_code = major_code[:4] if len(major_code) >= 4 else ""
    parent_match = bool(
        parent_code
        and re.search(rf"(?<!\d){re.escape(parent_code)}(?!\d)", text)
    )
    known_parent_name = major_code.startswith("0809") and "计算机类" in text
    if exact_name or exact_code or parent_match or known_parent_name:
        return decision(
            "major",
            "pass",
            f"{profile_major}（{major_code or '无专业代码'}）匹配岗位专业要求。",
        )
    if any(marker in text for marker in ("相关专业", "相近专业", "等专业")):
        return decision(
            "major",
            "unknown",
            f"岗位专业表述存在开放或歧义口径：{branch}",
        )
    return decision("major", "fail", f"岗位专业要求为：{branch}")


def parse_years(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    text = compact(value)
    if not text or text == "unknown":
        return None
    match = re.search(r"(\d+(?:\.\d+)?)年", text)
    if match:
        return float(match.group(1))
    chinese = {"一年": 1.0, "二年": 2.0, "两年": 2.0, "三年": 3.0, "四年": 4.0, "五年": 5.0}
    for marker, years in chinese.items():
        if marker in text:
            return years
    return None


def profile_truth(value: Any) -> bool | None:
    if value is True:
        return True
    if value is False:
        return False
    text = compact(value).casefold()
    if not text or text == "unknown":
        return None
    if text in {"是", "有", "符合", "yes", "true", "应届"}:
        return True
    if text in {"否", "无", "不符合", "no", "false", "非应届"}:
        return False
    return True


def application_status(registration: dict[str, Any], as_of: datetime) -> str:
    opens_value = registration.get("opensAt")
    closes_value = registration.get("closesAt")
    if not opens_value or not closes_value:
        return "unknown"
    opens_at = datetime.fromisoformat(opens_value)
    closes_at = datetime.fromisoformat(closes_value)
    if opens_at.tzinfo is None:
        opens_at = opens_at.replace(tzinfo=timezone.utc)
    if closes_at.tzinfo is None:
        closes_at = closes_at.replace(tzinfo=timezone.utc)
    current = as_of.astimezone(opens_at.tzinfo)
    if current < opens_at:
        return "upcoming"
    if current <= closes_at:
        return "open"
    return "closed"


def evaluate_position(
    position: dict[str, Any],
    profile: dict[str, Any],
    as_of: datetime,
) -> dict[str, Any]:
    basic = profile["basic"]
    experience = profile["experience"]
    qualifications = profile["qualifications"]
    requirements = position["requirements"]
    checks: list[dict[str, str]] = [
        evaluate_education(position, profile),
        evaluate_degree(position, profile),
        evaluate_major(position, profile),
    ]

    political = compact(requirements["politicalStatus"])
    profile_political = compact(basic.get("politicalStatus"))
    political_gate = requirement_gate(position, "politicalStatus", "政治面貌")
    if political_gate is not None:
        checks.append(political_gate)
    elif not profile_political or profile_political == "unknown":
        checks.append(decision("politicalStatus", "unknown", "画像政治面貌尚未确认。"))
    elif "非中共党员" in political:
        checks.append(
            decision(
                "politicalStatus",
                "fail" if "中共党员" in profile_political else "pass",
                f"画像政治面貌为{basic.get('politicalStatus')}，岗位要求非中共党员。",
            )
        )
    elif "中共党员" in political or "党员" in political:
        checks.append(
            decision(
                "politicalStatus",
                "pass" if "中共党员" in profile_political else "fail",
                f"画像政治面貌为{basic.get('politicalStatus')}，岗位要求为{requirements['politicalStatus']}。",
            )
        )
    elif profile_political in political:
        checks.append(decision("politicalStatus", "pass", "画像政治面貌满足岗位要求。"))
    else:
        checks.append(
            decision(
                "politicalStatus",
                "fail",
                f"岗位政治面貌要求为：{requirements['politicalStatus']}",
            )
        )

    fresh_text = compact(
        requirements.get("freshGraduate", "") or requirements["remarks"]
    )
    if any(marker in fresh_text for marker in ("应届高校毕业生", "应届毕业生", "2026届", "2026应届")):
        checks.append(
            decision(
                "freshGraduateStatus",
                (
                    "unknown"
                    if profile_truth(basic.get("freshGraduateStatus")) is None
                    else "pass"
                    if profile_truth(basic.get("freshGraduateStatus"))
                    else "fail"
                ),
                f"岗位限制应届毕业生，画像毕业年份为{basic.get('graduationYear', '未填写')}。",
            )
        )

    gender = compact(requirements.get("gender", ""))
    if not gender:
        remarks_gender = compact(requirements["remarks"])
        has_gender_ratio = "男女比例" in remarks_gender
        if not has_gender_ratio and any(
            marker in remarks_gender for marker in ("仅限女性", "限女性", "女性报考")
        ):
            gender = "女性"
        elif not has_gender_ratio and any(
            marker in remarks_gender for marker in ("仅限男性", "限男性", "男性报考", "适合男性")
        ):
            gender = "男性"
    if gender and not is_unlimited(gender):
        profile_gender = compact(basic.get("gender"))
        if "男性" in gender or gender == "男":
            checks.append(
                decision(
                    "gender",
                    "pass" if profile_gender == "男" else "fail",
                    f"岗位性别要求为：{gender}",
                )
            )
        elif "女性" in gender or gender == "女":
            checks.append(
                decision(
                    "gender",
                    "pass" if profile_gender == "女" else "fail",
                    f"岗位性别要求为：{gender}",
                )
            )

    household = compact(requirements.get("household", ""))
    if household and not is_unlimited(household):
        profile_household = compact(basic.get("householdRegistration"))
        profile_origin = compact(basic.get("studentOrigin"))
        known_values = {
            value
            for value in (profile_household, profile_origin)
            if value and value != "unknown"
        }
        if any(value in household for value in known_values):
            checks.append(decision("householdRegistration", "pass", "画像户籍或生源满足岗位要求。"))
        elif len(known_values) < 2:
            checks.append(decision("householdRegistration", "unknown", "岗位限制户籍或生源，画像尚未完整确认。"))
        else:
            checks.append(decision("householdRegistration", "fail", f"岗位户籍或生源要求为：{requirements.get('household', '')}"))

    age_text = compact(requirements.get("age", "") or requirements["remarks"])
    age = basic.get("age")
    age_limit_match = re.search(r"(\d+)周岁(?:及)?以下|不超过(\d+)周岁", age_text)
    if age_limit_match and isinstance(age, int):
        limit = int(age_limit_match.group(1) or age_limit_match.group(2))
        checks.append(
            decision(
                "age",
                "pass" if age <= limit else "fail",
                f"画像年龄{age}岁，岗位要求{limit}周岁以下。",
            )
        )

    grassroots = compact(requirements["grassrootsYears"])
    grassroots_state = position["requirementStates"].get(
        "grassrootsYears",
        "unparsed",
    )
    if (
        grassroots_state == "specified"
        and not is_unlimited(grassroots)
        and not grassroots.startswith("0")
    ):
        value = experience.get("grassrootsYears", "unknown")
        required_years = parse_years(grassroots)
        profile_years = parse_years(value)
        result = (
            "unknown"
            if value == "unknown" or required_years is None or profile_years is None
            else "pass"
            if profile_years >= required_years
            else "fail"
        )
        checks.append(
            decision(
                "grassrootsYears",
                result,
                f"岗位基层经历要求为{requirements['grassrootsYears']}，画像为{value}。",
            )
        )

    service = compact(requirements["serviceProject"])
    service_markers = (
        "服务基层项目",
        "退役士兵",
        "退役大学生士兵",
        "大学生退役士兵",
        "三支一扶",
        "西部计划",
    )
    service_state = position["requirementStates"].get(
        "serviceProject",
        "unparsed",
    )
    if service_state != "specified" and any(
        marker in compact(requirements["remarks"]) for marker in service_markers
    ):
        service = compact(requirements["remarks"])
        service_state = "specified"
    if service_state == "specified" and not is_unlimited(service):
        value = experience.get("veteranOrServiceProgram", "unknown")
        truth = profile_truth(value)
        checks.append(
            decision(
                "serviceProject",
                "unknown" if truth is None else "pass" if truth else "fail",
                f"岗位要求服务基层项目经历，画像填写为{value}。",
            )
        )

    remarks = requirements["remarks"]
    if any(marker.casefold() in remarks.casefold() for marker in ("英语四级", "英语六级", "大学英语", "CET")):
        value = qualifications.get("english", "unknown")
        if value == "unknown":
            checks.append(decision("english", "unknown", "岗位限制英语等级，画像尚未填写。"))
        else:
            required_six = any(marker in remarks for marker in ("六级", "CET6", "CET-6"))
            profile_text = compact(value).upper()
            passed = (
                any(marker in profile_text for marker in ("六级", "CET6", "CET-6"))
                if required_six
                else any(marker in profile_text for marker in ("四级", "六级", "CET4", "CET6", "CET-4", "CET-6"))
            )
            checks.append(decision("english", "pass" if passed else "fail", f"岗位英语要求为：{remarks}"))

    certificate_text = compact(requirements.get("certificate", "") or remarks)
    if any(marker in certificate_text for marker in ("资格证", "职业资格", "法律职业资格")):
        value = qualifications.get("professional", "unknown")
        truth = profile_truth(value)
        checks.append(
            decision(
                "professional",
                "unknown" if truth is None else "pass" if truth else "fail",
                f"岗位资格证要求为：{requirements.get('certificate') or remarks}",
            )
        )

    if any(marker in remarks for marker in ("工作经历", "工作经验", "从事相关工作")):
        value = experience.get("workYears", "unknown")
        required_years = parse_years(remarks)
        profile_years = parse_years(value)
        checks.append(
            decision(
                "workYears",
                "unknown"
                if required_years is None or profile_years is None
                else "pass"
                if profile_years >= required_years
                else "fail",
                f"岗位工作经历要求为：{remarks}；画像为{value}。",
            )
        )

    failures = [item for item in checks if item["result"] == "fail"]
    unknowns = [item for item in checks if item["result"] == "unknown"]
    eligibility = "ineligible" if failures else "needs_confirmation" if unknowns else "eligible"

    return {
        **position,
        "eligibility": eligibility,
        "applicationStatus": application_status(position["registration"], as_of),
        "matchReasons": [item["reason"] for item in checks if item["result"] == "pass"],
        "confirmationFields": sorted({item["field"] for item in unknowns}),
        "exclusionReasons": [item["reason"] for item in failures],
        "decisions": checks,
    }


def validate_schema(instance: Any, schema_path: Path, label: str) -> None:
    validator = SCHEMA_VALIDATORS.get(schema_path)
    if validator is None:
        schema = read_json(schema_path)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        SCHEMA_VALIDATORS[schema_path] = validator
    failures = sorted(validator.iter_errors(instance), key=lambda item: list(item.path))
    if failures:
        raise ValueError(
            f"{label} validation failed: "
            + "; ".join(f"{list(error.path)}: {error.message}" for error in failures[:20])
        )


def load_sources() -> dict[str, Any]:
    config = read_json(SOURCES_CONFIG)
    validate_schema(config, SOURCES_SCHEMA_PATH, "job sources")
    for source in config.get("sources", []):
        allowed_hosts = source["allowedHosts"]
        for field in ("portalUrl", "announcementUrl", "evidenceUrl"):
            if not official_url(source[field], allowed_hosts):
                raise ValueError(
                    f"non-official {field} URL rejected for {source['sourceId']}: "
                    f"{source[field]}"
                )
        if not official_url(source["portalUrl"], allowed_hosts):
            raise ValueError(f"non-official portal URL rejected: {source['portalUrl']}")
        for attachment in source.get("attachments", []):
            if not official_url(attachment["url"], allowed_hosts):
                raise ValueError(f"non-official attachment URL rejected: {attachment['url']}")
            path = (ROOT / attachment["path"]).resolve()
            source_root = (JOBS_DIR / "sources").resolve()
            if path != source_root and source_root not in path.parents:
                raise ValueError(f"attachment path escapes data/jobs/sources: {path}")
    return config


def optional_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(str(value))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def select_campaigns(config: dict[str, Any], as_of: datetime) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for source in config["sources"]:
        grouped.setdefault(source["sourceId"], []).append(source)

    selected: list[dict[str, Any]] = []
    for source_id, campaigns in grouped.items():
        recruitment_mode = campaigns[0]["recruitmentMode"]
        current: list[tuple[datetime, dict[str, Any]]] = []
        previous: list[tuple[datetime, dict[str, Any]]] = []
        for campaign in campaigns:
            if recruitment_mode == "exam":
                boundary = optional_datetime(campaign.get("examAt"))
            else:
                boundary = optional_datetime(campaign["registration"].get("closesAt"))
            if boundary is None:
                previous.append((datetime.min.replace(tzinfo=timezone.utc), campaign))
                continue
            normalized_as_of = as_of.astimezone(boundary.tzinfo or timezone.utc)
            target = current if boundary >= normalized_as_of else previous
            target.append((boundary, campaign))
        if current:
            _, chosen = min(current, key=lambda item: item[0])
            mode = "current"
        elif previous:
            _, chosen = max(previous, key=lambda item: item[0])
            mode = "previous_reference"
        else:
            raise ValueError(f"source family has no campaigns: {source_id}")
        selected.append({**chosen, "selectionMode": mode})
    return {**config, "sources": sorted(selected, key=lambda item: item["sourceId"])}


def download_all(config: dict[str, Any], force: bool = False) -> list[dict[str, Any]]:
    downloaded: list[dict[str, Any]] = []
    for source in config["sources"]:
        for attachment in source["attachments"]:
            downloaded.append(
                download_attachment(
                    attachment,
                    allowed_hosts=source["allowedHosts"],
                    force=force,
                )
            )
    return downloaded


def harness_run_directory() -> Path | None:
    value = os.environ.get("JOB_SEARCH_RUN_DIR")
    return Path(value).resolve() if value else None


def parse_for_harness(config: dict[str, Any]) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    fragments: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    for source in config["sources"]:
        positions, errors = parse_source(source)
        normalized.extend(positions)
        source_counts[source["sourceId"]] = len(positions)
        fragments.extend(
            {
                **error,
                "sourceId": source["sourceId"],
                "evidenceUrl": source["evidenceUrl"],
            }
            for error in errors
        )
    run_directory = harness_run_directory()
    if run_directory is not None:
        run_directory.mkdir(parents=True, exist_ok=True)
        write_jsonl(run_directory / "parsed-positions.jsonl", normalized)
        write_json(run_directory / "extraction-fragments.json", fragments)
    return {
        "status": "completed",
        "summary": (
            f"parsed {len(normalized)} positions with "
            f"{len(fragments)} extraction fragments"
        ),
        "positions": len(normalized),
        "fragments": len(fragments),
        "sourceCounts": source_counts,
        "artifacts": [
            "parsed-positions.jsonl",
            "extraction-fragments.json",
        ],
        "issues": [item["message"] for item in fragments],
    }


def load_agent_extracted_positions() -> list[dict[str, Any]]:
    run_directory = harness_run_directory()
    if run_directory is None:
        return []
    submission = run_directory / "stage-results" / "04-submitted.json"
    if not submission.is_file():
        return []
    payload = read_json(submission)
    positions = payload.get("normalizedPositions", [])
    if not isinstance(positions, list):
        raise ValueError("agent normalizedPositions must be an array")
    required = {
        "id",
        "sourceId",
        "sourceLabel",
        "category",
        "cycle",
        "batchStatus",
        "organization",
        "title",
        "positionCode",
        "requirements",
        "requirementStates",
        "registration",
        "source",
    }
    for index, position in enumerate(positions):
        if not isinstance(position, dict) or required - position.keys():
            raise ValueError(
                f"agent normalized position {index} lacks required evidence fields"
            )
    return positions


def build(
    config: dict[str, Any],
    as_of: datetime,
    allow_large_delta: bool = False,
) -> dict[str, Any]:
    profile = read_json(PROFILE_PATH)
    profile_bytes = json.dumps(profile, ensure_ascii=False, sort_keys=True).encode("utf-8")
    all_positions: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    source_index: list[dict[str, Any]] = []
    extracted_by_source: dict[str, list[dict[str, Any]]] = {}
    for position in load_agent_extracted_positions():
        extracted_by_source.setdefault(position["sourceId"], []).append(position)

    for source in config["sources"]:
        positions, source_errors = parse_source(source)
        positions.extend(extracted_by_source.get(source["sourceId"], []))
        if not positions:
            raise ValueError(
                f"{source['sourceId']} produced zero normalized positions: "
                + "; ".join(item["message"] for item in source_errors)
            )
        all_positions.extend(positions)
        errors.extend(source_errors)
        source_index.append(
            {
                "sourceId": source["sourceId"],
                "label": source["label"],
                "category": source["category"],
                "cycle": source["cycle"],
                "selectionMode": source["selectionMode"],
                "examAt": source.get("examAt"),
                "portalUrl": source["portalUrl"],
                "evidenceUrl": source["evidenceUrl"],
                "allowedHosts": source["allowedHosts"],
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
            key=lambda item: (item["sourceId"], item["organization"], item["positionCode"]),
        )
    ]

    eligible_positions = [
        position for position in evaluated if position["eligibility"] == "eligible"
    ]
    needs_confirmation_positions = [
        position
        for position in evaluated
        if position["eligibility"] == "needs_confirmation"
    ]
    eligibility = Counter(item["eligibility"] for item in evaluated)
    application = Counter(item["applicationStatus"] for item in evaluated)
    unknown_fields = sorted(
        key
        for group in ("basic", "experience", "qualifications", "preferences")
        for key, value in profile.get(group, {}).items()
        if value == "unknown"
    )
    registry = (
        read_json(SOURCE_REGISTRY_PATH)
        if SOURCE_REGISTRY_PATH.is_file()
        else {
            "requiredCategories": list(REQUIRED_CATEGORIES),
            "sourceFamilies": [],
        }
    )
    if SOURCE_REGISTRY_PATH.is_file():
        validate_schema(
            registry,
            SOURCE_REGISTRY_SCHEMA_PATH,
            "job source registry",
        )
    required_categories = registry.get("requiredCategories", list(REQUIRED_CATEGORIES))
    registered_categories = sorted(
        {item["category"] for item in registry.get("sourceFamilies", [])}
    )
    catalog_categories = sorted({item["category"] for item in evaluated})
    eligible_next = ELIGIBLE_CATALOG_PATH.with_suffix(".jsonl.next")
    confirmation_next = NEEDS_CONFIRMATION_CATALOG_PATH.with_suffix(".jsonl.next")
    index_next = INDEX_PATH.with_suffix(".json.next")
    write_jsonl(eligible_next, eligible_positions)
    write_jsonl(confirmation_next, needs_confirmation_positions)

    index = {
        "schemaVersion": "4.0",
        "generatedAt": now_iso(),
        "asOf": as_of.astimezone().isoformat(timespec="seconds"),
        "profileSnapshot": {
            "sha256": sha256_bytes(profile_bytes),
            "updatedAt": profile["updatedAt"],
            "unknownFields": unknown_fields,
        },
        "eligibleCatalog": {
            "path": ELIGIBLE_CATALOG_PATH.relative_to(ROOT).as_posix(),
            "rowCount": len(eligible_positions),
            "sha256": sha256_jsonl(eligible_next),
        },
        "needsConfirmationCatalog": {
            "path": NEEDS_CONFIRMATION_CATALOG_PATH.relative_to(ROOT).as_posix(),
            "rowCount": len(needs_confirmation_positions),
            "sha256": sha256_jsonl(confirmation_next),
        },
        "sources": source_index,
        "stats": {
            "processed": len(evaluated),
            "eligible": eligibility["eligible"],
            "needsConfirmation": eligibility["needs_confirmation"],
            "excluded": eligibility["ineligible"],
            "currentCampaigns": sum(
                item["selectionMode"] == "current" for item in source_index
            ),
            "referenceCampaigns": sum(
                item["selectionMode"] == "previous_reference"
                for item in source_index
            ),
            "application": {
                "upcoming": application["upcoming"],
                "open": application["open"],
                "closed": application["closed"],
                "unknown": application["unknown"],
            },
        },
        "coverage": {
            "requiredCategories": required_categories,
            "registeredCategories": registered_categories,
            "catalogCategories": catalog_categories,
            "missingCatalogCategories": sorted(
                set(required_categories) - set(catalog_categories)
            ),
        },
        "errors": errors,
    }
    try:
        validate_schema(index, SCHEMA_PATH, "job index")
        validate_catalog_path(
            eligible_next,
            expected_count=index["stats"]["eligible"],
            expected_eligibility="eligible",
            expected_sha256=index["eligibleCatalog"]["sha256"],
        )
        validate_catalog_path(
            confirmation_next,
            expected_count=index["stats"]["needsConfirmation"],
            expected_eligibility="needs_confirmation",
            expected_sha256=index["needsConfirmationCatalog"]["sha256"],
        )
        enforce_release_guard(index, allow_large_delta=allow_large_delta)
        write_json(index_next, index)
        eligible_next.replace(ELIGIBLE_CATALOG_PATH)
        confirmation_next.replace(NEEDS_CONFIRMATION_CATALOG_PATH)
        index_next.replace(INDEX_PATH)
        OLD_CATALOG_PATH.unlink(missing_ok=True)
    finally:
        eligible_next.unlink(missing_ok=True)
        confirmation_next.unlink(missing_ok=True)
        index_next.unlink(missing_ok=True)
    return index


def enforce_release_guard(
    next_index: dict[str, Any],
    allow_large_delta: bool = False,
) -> None:
    processed = next_index["stats"]["processed"]
    eligible = next_index["stats"]["eligible"]
    if processed > 0 and eligible == 0 and not allow_large_delta:
        raise ValueError(
            "release guard rejected an empty eligible catalog; "
            "use --allow-large-delta only after manual review"
        )
    if not INDEX_PATH.is_file() or allow_large_delta:
        return
    previous = read_json(INDEX_PATH)
    previous_eligible = int(previous.get("stats", {}).get("eligible", 0))
    if previous_eligible > 0 and eligible < previous_eligible * 0.5:
        raise ValueError(
            "release guard rejected eligible count drop: "
            f"previous={previous_eligible}, next={eligible}"
        )
    previous_categories = set(
        previous.get("coverage", {}).get("catalogCategories", [])
    )
    next_categories = set(next_index["coverage"]["catalogCategories"])
    missing = previous_categories - next_categories
    if missing:
        raise ValueError(
            f"release guard rejected lost catalog categories: {sorted(missing)}"
        )


def validate_index(index: dict[str, Any] | None = None) -> None:
    instance = index if index is not None else read_json(INDEX_PATH)
    validate_schema(instance, SCHEMA_PATH, "job index")
    validate_catalog_artifact(
        instance["eligibleCatalog"],
        expected_count=instance["stats"]["eligible"],
        expected_eligibility="eligible",
    )
    validate_catalog_artifact(
        instance["needsConfirmationCatalog"],
        expected_count=instance["stats"]["needsConfirmation"],
        expected_eligibility="needs_confirmation",
    )
    published = (
        instance["stats"]["eligible"]
        + instance["stats"]["needsConfirmation"]
        + instance["stats"]["excluded"]
    )
    if published != instance["stats"]["processed"]:
        raise ValueError(
            "job stats mismatch: "
            f"processed={instance['stats']['processed']}, decisions={published}"
        )


def validate_catalog_artifact(
    artifact: dict[str, Any],
    expected_count: int | None = None,
    expected_eligibility: str | None = None,
) -> None:
    catalog = ROOT / artifact["path"]
    if not catalog.is_file():
        raise FileNotFoundError(f"missing catalog: {catalog}")
    validate_catalog_path(
        catalog,
        expected_count=(
            expected_count if expected_count is not None else artifact["rowCount"]
        ),
        expected_eligibility=expected_eligibility,
        expected_sha256=artifact["sha256"],
    )


def validate_catalog_path(
    catalog: Path,
    expected_count: int,
    expected_eligibility: str | None,
    expected_sha256: str,
) -> None:
    rows = 0
    with catalog.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            try:
                validate_schema(
                    value,
                    POSITION_SCHEMA_PATH,
                    f"catalog line {line_number}",
                )
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
            if (
                expected_eligibility is not None
                and value["eligibility"] != expected_eligibility
            ):
                raise ValueError(
                    f"catalog line {line_number} has unexpected eligibility: "
                    f"{value['eligibility']}"
                )
            rows += 1
    if rows != expected_count:
        raise ValueError(
            f"catalog row mismatch: index={expected_count}, actual={rows}"
        )
    if sha256_jsonl(catalog) != expected_sha256:
        raise ValueError("catalog sha256 mismatch")


def parse_as_of(value: str | None) -> datetime:
    if not value:
        return datetime.now().astimezone()
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("download", "parse", "filter", "build", "all", "validate"),
    )
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--as-of", default="")
    parser.add_argument("--allow-large-delta", action="store_true")
    args = parser.parse_args()
    as_of = parse_as_of(args.as_of)
    config = select_campaigns(load_sources(), as_of)

    if args.command in {"download", "all"}:
        metadata = download_all(config, force=args.force)
        print(json.dumps({"downloaded": len(metadata), "artifacts": metadata}, ensure_ascii=False))
    if args.command == "parse":
        result = parse_for_harness(config)
        print(json.dumps(result, ensure_ascii=False))
    if args.command in {"filter", "build", "all"}:
        index = build(
            config,
            as_of,
            allow_large_delta=args.allow_large_delta,
        )
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
