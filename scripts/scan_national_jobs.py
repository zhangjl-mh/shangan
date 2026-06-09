"""Build a complete 2026 national civil-service job catalog and decisions.

The official workbook is the fact source. Profile screening is a separate,
tri-state projection so uncertain profile fields never silently become passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET

import xlrd


ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / "data" / "profile.local.json"
OFFICIAL_DIR = ROOT / "content" / "official" / "job" / "national-civil-service" / "2026"
LOCAL_JOB_DIR = ROOT / "content" / "local" / "job"
CATALOG_PATH = LOCAL_JOB_DIR / "catalog" / "national-civil-service" / "2026.jsonl"
DOMAIN_PATH = LOCAL_JOB_DIR / "national-civil-service.json"

CHINA_TZ = timezone(timedelta(hours=8))
DOMAIN = "national-civil-service"
CYCLE = "2026"
MAIN_URL = "http://dl.scs.gov.cn/download/8a81f6d19780e4080199e13f881f0153"
INTERVIEW_URL = "http://dl.scs.gov.cn/download/8a81f6d09bb1deaf019bbfaf036b0011"
SUPPLEMENT_URL = "http://dl.scs.gov.cn/download/8a81f6d09bb1deaf019e004d392d0964"
PORTAL_URL = "http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/home/gkhome.html"

XLSX_NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "officeRel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "packageRel": "http://schemas.openxmlformats.org/package/2006/relationships",
}

MAIN_COLUMNS = {
    "departmentCode": "部门代码",
    "organization": "部门名称",
    "department": "用人司局",
    "organizationNature": "机构性质",
    "title": "招考职位",
    "positionAttribute": "职位属性",
    "positionDistribution": "职位分布",
    "responsibilities": "职位简介",
    "positionCode": "职位代码",
    "organizationLevel": "机构层级",
    "examCategory": "考试类别",
    "recruitCount": "招考人数",
    "majorRequirement": "专业",
    "educationRequirement": "学历",
    "degreeRequirement": "学位",
    "politicalRequirement": "政治面貌",
    "grassrootsRequirement": "基层工作最低年限",
    "serviceProjectRequirement": "服务基层项目工作经历",
    "professionalTest": "是否在面试阶段组织专业能力测试",
    "interviewRatio": "面试人员比例",
    "region": "工作地点",
    "settlementRegion": "落户地点",
    "remarks": "备注",
    "departmentWebsite": "部门网站",
    "consultationPhone1": "咨询电话1",
    "consultationPhone2": "咨询电话2",
    "consultationPhone3": "咨询电话3",
}

SUPPLEMENT_EXTRA_COLUMNS = {
    "writtenTotalLine": "总分分数线",
    "writtenAptitudeLine": "行政职业能力测验分数线",
    "writtenProfessionalLine": "专业科目分数线",
}


def now_iso() -> str:
    return datetime.now(CHINA_TZ).isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for row in rows:
            output.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            count += 1
    return count


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def compact(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return re.sub(r"\s+", "", str(value)).strip()


def display_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return re.sub(r"\s+", " ", str(value)).strip()


def stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"ncs-{CYCLE}-{digest}"


def region_group(region: str) -> str:
    text = compact(region)
    if "北京" in text:
        return "北京"
    if "天津" in text:
        return "天津"
    if any(marker in text for marker in ("雄安", "雄县", "容城", "安新")):
        return "雄安"
    if any(marker in text for marker in ("石家庄", "井陉", "鹿泉", "藁城", "栾城", "正定")):
        return "石家庄"
    return "其他"


def column_index(cell_ref: str) -> int:
    letters = "".join(char for char in cell_ref if char.isalpha())
    index = 0
    for char in letters.upper():
        index = index * 26 + ord(char) - 64
    return index - 1


def xlsx_rows(data: bytes) -> list[tuple[str, int, list[str]]]:
    """Return (sheet name, 1-based row number, values) for every XLSX row."""

    rows: list[tuple[str, int, list[str]]] = []
    with zipfile.ZipFile(PathLikeBytes(data)) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", XLSX_NS):
                shared_strings.append(
                    "".join(node.text or "" for node in item.iter(f"{{{XLSX_NS['main']}}}t"))
                )

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            relation.attrib["Id"]: relation.attrib["Target"]
            for relation in relations.findall("packageRel:Relationship", XLSX_NS)
        }

        sheets = workbook.find("main:sheets", XLSX_NS)
        if sheets is None:
            return rows

        for sheet in sheets:
            sheet_name = sheet.attrib["name"]
            relation_id = sheet.attrib[f"{{{XLSX_NS['officeRel']}}}id"]
            target = targets[relation_id].lstrip("/")
            if not target.startswith("xl/"):
                target = f"xl/{target}"
            root = ET.fromstring(archive.read(target))
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
                    values[index] = display_text(value)
                maximum = max(values, default=-1)
                rows.append(
                    (
                        sheet_name,
                        int(row.attrib.get("r", len(rows) + 1)),
                        [values.get(index, "") for index in range(maximum + 1)],
                    )
                )
    return rows


class PathLikeBytes:
    """Small seekable wrapper accepted by zipfile without an extra temp file."""

    def __init__(self, data: bytes):
        import io

        self._buffer = io.BytesIO(data)

    def read(self, *args: Any) -> bytes:
        return self._buffer.read(*args)

    def seek(self, *args: Any) -> int:
        return self._buffer.seek(*args)

    def tell(self) -> int:
        return self._buffer.tell()

    def seekable(self) -> bool:
        return True


def header_map(headers: list[str]) -> dict[str, int]:
    return {compact(header): index for index, header in enumerate(headers) if compact(header)}


def cell(row: list[str], headers: dict[str, int], name: str) -> str:
    index = headers.get(compact(name))
    if index is None or index >= len(row):
        return ""
    return display_text(row[index])


def normalize_fact(
    row: list[str],
    headers: dict[str, int],
    *,
    source_kind: str,
    sheet_name: str,
    row_number: int,
    file_name: str,
    file_sha256: str,
) -> dict[str, Any]:
    source_url = MAIN_URL if source_kind == "main" else SUPPLEMENT_URL
    columns = {**MAIN_COLUMNS, **(SUPPLEMENT_EXTRA_COLUMNS if source_kind == "supplement" else {})}
    values = {key: cell(row, headers, label) for key, label in columns.items()}
    position_code = values["positionCode"]
    department_code = values["departmentCode"]
    fact_id = stable_id(source_kind, department_code, position_code, sheet_name, str(row_number))
    try:
        recruit_count = int(float(values["recruitCount"] or "0"))
    except ValueError:
        recruit_count = 0

    return {
        "id": fact_id,
        "domain": DOMAIN,
        "cycle": CYCLE,
        "sourceKind": source_kind,
        "announcementId": f"national-civil-service-{CYCLE}-{source_kind}",
        "departmentCode": department_code,
        "organization": values["organization"],
        "department": values["department"],
        "organizationNature": values["organizationNature"],
        "title": values["title"],
        "positionAttribute": values["positionAttribute"],
        "positionDistribution": values["positionDistribution"],
        "responsibilities": values["responsibilities"],
        "positionCode": position_code,
        "organizationLevel": values["organizationLevel"],
        "examCategory": values["examCategory"],
        "recruitCount": recruit_count,
        "region": values["region"],
        "regionGroup": region_group(values["region"]),
        "settlementRegion": values["settlementRegion"],
        "requirements": {
            "major": values["majorRequirement"],
            "education": values["educationRequirement"],
            "degree": values["degreeRequirement"],
            "politicalStatus": values["politicalRequirement"],
            "grassrootsYears": values["grassrootsRequirement"],
            "serviceProject": values["serviceProjectRequirement"],
            "professionalTest": values["professionalTest"],
            "interviewRatio": values["interviewRatio"],
            "remarks": values["remarks"],
        },
        "writtenScoreLines": {
            "total": values.get("writtenTotalLine", ""),
            "aptitude": values.get("writtenAptitudeLine", ""),
            "professional": values.get("writtenProfessionalLine", ""),
        },
        "contact": {
            "website": values["departmentWebsite"],
            "phones": [
                phone
                for phone in (
                    values["consultationPhone1"],
                    values["consultationPhone2"],
                    values["consultationPhone3"],
                )
                if phone
            ],
        },
        "status": "已截止",
        "phase": "interview-list-published" if source_kind == "main" else "supplement-registration-ended",
        "registration": (
            {
                "start": "2026-05-08T08:00:00+08:00",
                "end": "2026-05-10T18:00:00+08:00",
            }
            if source_kind == "supplement"
            else {"start": "", "end": ""}
        ),
        "source": {
            "name": (
                "国家公务员局：中央机关及其直属机构2026年度考试录用公务员招考简章"
                if source_kind == "main"
                else "国家公务员局：中央机关及其直属机构2026年度补充录用职位表"
            ),
            "url": source_url,
            "portalUrl": PORTAL_URL,
            "official": True,
        },
        "artifact": {
            "fileName": file_name,
            "sha256": file_sha256,
            "sheet": sheet_name,
            "rowNumber": row_number,
        },
    }


def parse_main(path: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    archive_data = path.read_bytes()
    archive_sha = sha256_bytes(archive_data)
    facts: list[dict[str, Any]] = []
    metrics = Counter()
    with zipfile.ZipFile(PathLikeBytes(archive_data)) as archive:
        workbook_names = [
            name for name in archive.namelist() if name.lower().endswith(".xls")
        ]
        if len(workbook_names) != 1:
            raise ValueError(f"Expected one XLS in {path.name}, found {workbook_names}")
        workbook_name = workbook_names[0]
        workbook_data = archive.read(workbook_name)
        workbook = xlrd.open_workbook(file_contents=workbook_data)
        for sheet in workbook.sheets():
            if sheet.nrows < 2:
                continue
            headers = [display_text(sheet.cell_value(1, column)) for column in range(sheet.ncols)]
            mapping = header_map(headers)
            required = [compact(label) for label in MAIN_COLUMNS.values()]
            if any(label not in mapping for label in required):
                raise ValueError(f"Missing expected headers in main sheet {sheet.name}")
            for row_index in range(2, sheet.nrows):
                metrics["sourceRows"] += 1
                row = [
                    display_text(sheet.cell_value(row_index, column))
                    for column in range(sheet.ncols)
                ]
                if not any(compact(value) for value in row):
                    metrics["skippedRows"] += 1
                    continue
                fact = normalize_fact(
                    row,
                    mapping,
                    source_kind="main",
                    sheet_name=sheet.name,
                    row_number=row_index + 1,
                    file_name=path.name,
                    file_sha256=archive_sha,
                )
                if not fact["positionCode"] or not fact["title"]:
                    metrics["parseErrors"] += 1
                    continue
                facts.append(fact)
    return facts, dict(metrics)


def parse_supplement(path: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    data = path.read_bytes()
    file_sha = sha256_bytes(data)
    rows = xlsx_rows(data)
    facts: list[dict[str, Any]] = []
    metrics = Counter()
    by_sheet: dict[str, list[tuple[int, list[str]]]] = defaultdict(list)
    for sheet, row_number, values in rows:
        by_sheet[sheet].append((row_number, values))

    for sheet_name, sheet_rows in by_sheet.items():
        header_index = next(
            (
                index
                for index, (_, values) in enumerate(sheet_rows)
                if "职位代码" in [compact(value) for value in values]
            ),
            None,
        )
        if header_index is None:
            continue
        headers = header_map(sheet_rows[header_index][1])
        for row_number, row in sheet_rows[header_index + 1 :]:
            metrics["sourceRows"] += 1
            if not any(compact(value) for value in row):
                metrics["skippedRows"] += 1
                continue
            fact = normalize_fact(
                row,
                headers,
                source_kind="supplement",
                sheet_name=sheet_name,
                row_number=row_number,
                file_name=path.name,
                file_sha256=file_sha,
            )
            if not fact["positionCode"] or not fact["title"]:
                metrics["parseErrors"] += 1
                continue
            facts.append(fact)
    return facts, dict(metrics)


def parse_interview_scores(path: Path) -> tuple[dict[str, dict[str, Any]], int]:
    rows = xlsx_rows(path.read_bytes())
    if not rows:
        return {}, 0
    header_position = next(
        (
            index
            for index, (_, _, values) in enumerate(rows)
            if "职位代码" in [compact(value) for value in values]
        ),
        None,
    )
    if header_position is None:
        raise ValueError("Interview workbook has no position-code header")
    headers = header_map(rows[header_position][2])
    aggregates: dict[str, dict[str, Any]] = {}
    source_rows = 0
    for _, _, row in rows[header_position + 1 :]:
        position_code = cell(row, headers, "职位代码")
        score_text = cell(row, headers, "最低面试分数")
        if not position_code:
            continue
        source_rows += 1
        score: float | None
        try:
            score = float(score_text)
        except ValueError:
            score = None
        current = aggregates.setdefault(
            position_code,
            {"candidateCount": 0, "minimumInterviewScore": score},
        )
        current["candidateCount"] += 1
        if score is not None:
            previous = current["minimumInterviewScore"]
            current["minimumInterviewScore"] = score if previous is None else min(previous, score)
    return aggregates, source_rows


def decision(field: str, result: str, reason: str, evidence: str) -> dict[str, str]:
    return {
        "field": field,
        "result": result,
        "reason": reason,
        "evidence": evidence,
    }


def is_unrestricted(text: str) -> bool:
    normalized = compact(text)
    return not normalized or any(
        marker in normalized
        for marker in ("无限制", "不限", "无要求", "不作要求", "不限制")
    )


def evaluate_education(requirement: str) -> dict[str, str]:
    text = compact(requirement)
    if is_unrestricted(text):
        return decision("education", "pass", "岗位未设置学历限制。", requirement)
    if any(marker in text for marker in ("仅限博士", "博士研究生")):
        return decision("education", "fail", "岗位要求博士研究生，画像为本科。", requirement)
    if any(marker in text for marker in ("仅限硕士", "硕士研究生及以上", "研究生（硕士）及以上")):
        return decision("education", "fail", "岗位最低要求硕士研究生，画像为本科。", requirement)
    if "研究生及以上" in text and "本科" not in text:
        return decision("education", "fail", "岗位最低要求研究生，画像为本科。", requirement)
    if any(marker in text for marker in ("本科", "大专及以上", "专科及以上", "大学本科")):
        return decision("education", "pass", "岗位学历范围包含本科。", requirement)
    return decision("education", "unknown", "学历表述无法自动确认是否包含本科。", requirement)


def evaluate_degree(requirement: str, profile_degree: str) -> dict[str, str]:
    if is_unrestricted(requirement):
        return decision("degree", "pass", "岗位未设置学位限制。", requirement)
    if profile_degree == "unknown":
        return decision("degree", "unknown", "岗位有学位要求，但本地画像尚未填写学位。", requirement)
    text = compact(requirement)
    profile = compact(profile_degree)
    if profile and (profile in text or "相对应的学位" in text):
        return decision("degree", "pass", "画像学位满足岗位要求。", requirement)
    return decision("degree", "fail", "画像学位不满足岗位要求。", requirement)


def evaluate_major(requirement: str, major: str, major_code: str) -> dict[str, str]:
    text = compact(requirement)
    if is_unrestricted(text):
        return decision("major", "pass", "岗位专业不限。", requirement)

    direct_markers = (
        compact(major),
        compact(major_code),
        "0809",
        "计算机类",
    )
    if any(marker and marker in text for marker in direct_markers):
        return decision("major", "pass", "岗位专业范围明确包含计算机科学与技术或本科计算机类。", requirement)

    broad_markers = ("08工学", "工学门类", "工学类")
    if any(marker in text for marker in broad_markers):
        return decision("major", "pass", "岗位接受工学门类，画像专业属于工学。", requirement)

    ambiguous_markers = (
        "计算机相关",
        "信息技术相关",
        "相近专业",
        "相关专业",
        "专业目录",
        "以主修专业为准",
    )
    if any(marker in text for marker in ambiguous_markers):
        return decision("major", "unknown", "专业使用“相关/相近”等口径，需招录机关确认。", requirement)

    return decision("major", "fail", "岗位列出的专业范围未包含计算机科学与技术。", requirement)


def evaluate_political(requirement: str, profile_value: str) -> dict[str, str]:
    if is_unrestricted(requirement):
        return decision("politicalStatus", "pass", "岗位政治面貌不限。", requirement)
    if profile_value == "unknown":
        return decision(
            "politicalStatus",
            "unknown",
            "岗位有政治面貌要求，但本地画像尚未填写。",
            requirement,
        )
    if compact(profile_value) in compact(requirement):
        return decision("politicalStatus", "pass", "画像政治面貌满足岗位要求。", requirement)
    return decision("politicalStatus", "fail", "画像政治面貌不满足岗位要求。", requirement)


def evaluate_grassroots(requirement: str, profile_value: Any) -> dict[str, str]:
    if is_unrestricted(requirement):
        return decision("grassrootsYears", "pass", "岗位不要求基层工作年限。", requirement)
    if profile_value == "unknown":
        return decision(
            "grassrootsYears",
            "unknown",
            "岗位要求基层工作年限，但本地画像尚未填写。",
            requirement,
        )
    digits = re.findall(r"\d+", compact(requirement))
    required = int(digits[0]) if digits else None
    try:
        actual = int(profile_value)
    except (TypeError, ValueError):
        actual = None
    if required is not None and actual is not None and actual >= required:
        return decision("grassrootsYears", "pass", "画像基层工作年限满足要求。", requirement)
    return decision("grassrootsYears", "fail", "画像基层工作年限不满足岗位要求。", requirement)


def evaluate_service_project(requirement: str, profile_value: str) -> dict[str, str]:
    if is_unrestricted(requirement):
        return decision("serviceProject", "pass", "岗位不限定服务基层项目经历。", requirement)
    if profile_value == "unknown":
        return decision(
            "serviceProject",
            "unknown",
            "岗位限定服务基层项目经历，但本地画像尚未填写。",
            requirement,
        )
    if compact(profile_value) in compact(requirement):
        return decision("serviceProject", "pass", "画像服务基层项目经历满足要求。", requirement)
    return decision("serviceProject", "fail", "画像服务基层项目经历不满足要求。", requirement)


def evaluate_fresh_graduate(fact: dict[str, Any], profile_value: str) -> dict[str, str]:
    evidence = "；".join(
        value
        for value in (
            fact["positionDistribution"],
            fact["positionAttribute"],
            fact["requirements"]["remarks"],
        )
        if value
    )
    text = compact(evidence)
    markers = (
        "应届高校毕业生",
        "应届毕业生",
        "2026届",
        "限当年毕业",
        "高校毕业生职位",
    )
    if not any(marker in text for marker in markers):
        return decision("freshGraduateStatus", "pass", "岗位未发现明确应届生限制。", evidence)
    if profile_value == "unknown":
        return decision(
            "freshGraduateStatus",
            "unknown",
            "岗位存在应届生口径，但本地画像尚未确认应届身份。",
            evidence,
        )
    if profile_value in ("是", "yes", "应届"):
        return decision("freshGraduateStatus", "pass", "画像已确认应届身份。", evidence)
    return decision("freshGraduateStatus", "fail", "岗位限应届生，画像不满足。", evidence)


def evaluate_gender(remarks: str, gender: str) -> dict[str, str]:
    text = compact(remarks)
    if re.search(r"(仅限|限|要求)女性", text):
        if gender == "女":
            return decision("gender", "pass", "画像性别满足岗位明确要求。", remarks)
        return decision("gender", "fail", "岗位明确限女性，画像为男性。", remarks)
    if re.search(r"(仅限|限|要求)男性", text):
        if gender == "男":
            return decision("gender", "pass", "画像性别满足岗位明确要求。", remarks)
        return decision("gender", "fail", "岗位明确限男性，画像不满足。", remarks)
    return decision("gender", "pass", "岗位未发现明确性别硬限制。", remarks)


def evaluate_remarks(fact: dict[str, Any], profile: dict[str, Any]) -> list[dict[str, str]]:
    remarks = fact["requirements"]["remarks"]
    text = compact(remarks)
    results: list[dict[str, str]] = []

    checks = [
        (
            "householdRegistration",
            ("户籍", "常住户口", "生源地", "生源"),
            profile["basic"].get("householdRegistration", "unknown"),
            "岗位备注存在户籍或生源限制，但本地画像尚未填写。",
        ),
        (
            "englishQualification",
            ("大学英语四级", "大学英语六级", "英语四级", "英语六级", "CET-4", "CET-6"),
            profile["qualifications"].get("english", "unknown"),
            "岗位备注存在英语资格要求，但本地画像尚未填写。",
        ),
        (
            "professionalQualification",
            ("资格证", "职业资格", "法律职业资格", "注册会计师", "通过司法考试"),
            profile["qualifications"].get("professional", "unknown"),
            "岗位备注存在职业资格要求，但本地画像尚未填写。",
        ),
        (
            "workExperience",
            ("工作经历", "相关工作经验", "从业经历", "任职经历"),
            profile["experience"].get("workYears", "unknown"),
            "岗位备注存在工作经历要求，但本地画像尚未填写。",
        ),
        (
            "identity",
            ("退役大学生士兵", "残疾人", "大学生村官", "三支一扶", "西部计划"),
            profile["experience"].get("veteranOrServiceProgram", "unknown"),
            "岗位备注存在定向身份要求，但本地画像尚未填写。",
        ),
    ]
    for field, markers, profile_value, unknown_reason in checks:
        matched = [marker for marker in markers if marker in text]
        if not matched:
            continue
        evidence = "、".join(matched)
        if profile_value == "unknown":
            results.append(decision(field, "unknown", unknown_reason, f"{evidence}；{remarks}"))
        else:
            results.append(
                decision(
                    field,
                    "unknown",
                    "备注条件需要结合证件或完整经历人工复核。",
                    f"{evidence}；{remarks}",
                )
            )
    return results


def evaluate_supplement_score(fact: dict[str, Any], profile_value: str) -> dict[str, str] | None:
    if fact["sourceKind"] != "supplement":
        return None
    evidence = "补充录用要求报考者参加中央机关及其直属机构2026年度考试录用公务员笔试。"
    if profile_value == "unknown":
        return decision(
            "writtenExamScore",
            "unknown",
            "补录要求已有2026年度国考笔试成绩，但本地画像尚未确认。",
            evidence,
        )
    if profile_value in ("是", "yes", "有"):
        return decision("writtenExamScore", "pass", "画像已确认具备本年度国考笔试成绩。", evidence)
    return decision("writtenExamScore", "fail", "没有本年度国考笔试成绩，不能参加补录。", evidence)


def evaluate_fact(
    fact: dict[str, Any],
    profile: dict[str, Any],
    interview: dict[str, Any] | None,
    run_id: str,
) -> dict[str, Any]:
    basic = profile["basic"]
    experience = profile["experience"]
    requirements = fact["requirements"]
    decisions = [
        decision("age", "pass", "画像年龄26岁，满足国考一般年龄条件。", "age=26"),
        evaluate_gender(requirements["remarks"], basic.get("gender", "unknown")),
        evaluate_education(requirements["education"]),
        evaluate_degree(requirements["degree"], basic.get("degree", "unknown")),
        evaluate_major(
            requirements["major"],
            basic.get("major", ""),
            basic.get("majorCode", ""),
        ),
        evaluate_political(
            requirements["politicalStatus"],
            basic.get("politicalStatus", "unknown"),
        ),
        evaluate_grassroots(
            requirements["grassrootsYears"],
            experience.get("grassrootsYears", "unknown"),
        ),
        evaluate_service_project(
            requirements["serviceProject"],
            experience.get("veteranOrServiceProgram", "unknown"),
        ),
        evaluate_fresh_graduate(
            fact,
            basic.get("freshGraduateStatus", "unknown"),
        ),
    ]
    decisions.extend(evaluate_remarks(fact, profile))
    supplement_score = evaluate_supplement_score(
        fact,
        experience.get("hasRelevantWrittenExamScore", "unknown"),
    )
    if supplement_score:
        decisions.append(supplement_score)

    failures = [item for item in decisions if item["result"] == "fail"]
    unknowns = [item for item in decisions if item["result"] == "unknown"]
    if failures:
        eligibility = "ineligible"
    elif unknowns:
        eligibility = "needs_confirmation"
    else:
        eligibility = "eligible"

    return {
        "id": fact["id"],
        "domain": DOMAIN,
        "cycle": CYCLE,
        "runId": run_id,
        "factId": fact["id"],
        "positionCode": fact["positionCode"],
        "eligibility": eligibility,
        "qualificationDecisions": decisions,
        "failedFields": [item["field"] for item in failures],
        "unknownFields": [item["field"] for item in unknowns],
        "interviewReference": interview,
    }


def public_position(
    fact: dict[str, Any],
    decision_row: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    failures = [
        item
        for item in decision_row["qualificationDecisions"]
        if item["result"] == "fail"
    ]
    unknowns = [
        item
        for item in decision_row["qualificationDecisions"]
        if item["result"] == "unknown"
    ]
    pass_count = sum(
        item["result"] == "pass" for item in decision_row["qualificationDecisions"]
    )
    total = len(decision_row["qualificationDecisions"]) or 1
    score = round(pass_count / total * 100)
    interview = decision_row.get("interviewReference")
    references = []
    if interview:
        references.append(
            {
                "year": CYCLE,
                "minimumInterviewScore": interview.get("minimumInterviewScore"),
                "candidateCount": interview.get("candidateCount"),
                "sourceName": "国家公务员局2026年度进入面试人员名单",
                "sourceUrl": INTERVIEW_URL,
            }
        )
    return {
        "id": fact["id"],
        "title": fact["title"],
        "organization": fact["organization"],
        "department": fact["department"],
        "category": "公务员",
        "recruitmentClass": "国考",
        "cycle": CYCLE,
        "sourceKind": fact["sourceKind"],
        "positionCode": fact["positionCode"],
        "recruitCount": fact["recruitCount"],
        "region": fact["region"],
        "regionGroup": fact["regionGroup"],
        "settlementRegion": fact["settlementRegion"],
        "status": fact["status"],
        "phase": fact["phase"],
        "responsibilities": fact["responsibilities"],
        "educationRequirement": fact["requirements"]["education"],
        "degreeRequirement": fact["requirements"]["degree"],
        "majorRequirement": fact["requirements"]["major"],
        "politicalRequirement": fact["requirements"]["politicalStatus"],
        "grassrootsRequirement": fact["requirements"]["grassrootsYears"],
        "serviceProjectRequirement": fact["requirements"]["serviceProject"],
        "freshGraduateRequirement": next(
            (
                item["evidence"]
                for item in decision_row["qualificationDecisions"]
                if item["field"] == "freshGraduateStatus"
            ),
            "",
        ),
        "remarks": fact["requirements"]["remarks"],
        "registrationStartAt": fact["registration"]["start"],
        "registrationEndAt": fact["registration"]["end"],
        "eligibility": decision_row["eligibility"],
        "matchScore": score,
        "matchLevel": (
            "可报"
            if decision_row["eligibility"] == "eligible"
            else "待确认"
            if decision_row["eligibility"] == "needs_confirmation"
            else "不符合"
        ),
        "matchReasons": [
            item["reason"]
            for item in decision_row["qualificationDecisions"]
            if item["result"] == "pass"
        ],
        "riskReminders": [item["reason"] for item in failures + unknowns],
        "qualificationDecisions": decision_row["qualificationDecisions"],
        "historicalReferences": references,
        "benefits": ["官方职位表未载明具体工资福利。"],
        "housingReference": "官方职位表仅载明工作地点和落户地点，未承诺住房保障。",
        "householdReference": (
            f"职位表载明落户地点：{fact['settlementRegion']}。"
            if fact["settlementRegion"]
            else "官方职位表未载明落户地点。"
        ),
        "officialOnlyNotice": "资格结论仅依据官方职位表和本地画像；待确认项需向招录机关核实。",
        "sourceName": fact["source"]["name"],
        "sourceUrl": fact["source"]["url"],
        "portalUrl": fact["source"]["portalUrl"],
        "departmentWebsite": fact["contact"]["website"],
        "consultationPhones": fact["contact"]["phones"],
        "capturedAt": generated_at,
        "artifact": fact["artifact"],
    }


def excluded_projection(
    fact: dict[str, Any],
    decision_row: dict[str, Any],
) -> dict[str, Any]:
    failed = [
        item
        for item in decision_row["qualificationDecisions"]
        if item["result"] == "fail"
    ]
    return {
        "id": fact["id"],
        "positionCode": fact["positionCode"],
        "title": fact["title"],
        "organization": fact["organization"],
        "region": fact["region"],
        "sourceKind": fact["sourceKind"],
        "failedFields": decision_row["failedFields"],
        "reasons": [item["reason"] for item in failed],
        "sourceUrl": fact["source"]["url"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, default=PROFILE_PATH)
    parser.add_argument("--official-dir", type=Path, default=OFFICIAL_DIR)
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    generated_at = now_iso()
    run_id = args.run_id or f"national-{CYCLE}-{datetime.now(CHINA_TZ).strftime('%Y%m%dT%H%M%S')}"
    profile = read_json(args.profile)
    profile_hash = sha256_bytes(
        json.dumps(profile, ensure_ascii=False, sort_keys=True).encode("utf-8")
    )

    main_path = args.official_dir / "main.zip"
    supplement_path = args.official_dir / "supplement.zip"
    interview_path = args.official_dir / "interview.xlsx"
    for required in (main_path, supplement_path, interview_path):
        if not required.exists():
            raise FileNotFoundError(f"Missing official attachment: {required}")

    main_facts, main_metrics = parse_main(main_path)
    supplement_facts, supplement_metrics = parse_supplement(supplement_path)
    interview_scores, interview_rows = parse_interview_scores(interview_path)
    facts = [*main_facts, *supplement_facts]

    deduplicated: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for fact in facts:
        key = (fact["sourceKind"], fact["departmentCode"], fact["positionCode"])
        if key in seen:
            duplicates.append(fact)
        else:
            seen.add(key)
            deduplicated.append(fact)

    decisions = [
        evaluate_fact(
            fact,
            profile,
            interview_scores.get(fact["positionCode"]),
            run_id,
        )
        for fact in deduplicated
    ]
    decision_by_id = {row["factId"]: row for row in decisions}
    projections = [
        public_position(fact, decision_by_id[fact["id"]], generated_at)
        for fact in deduplicated
    ]

    eligible = [
        row for row in projections if row["eligibility"] == "eligible"
    ]
    pending = [
        row for row in projections if row["eligibility"] == "needs_confirmation"
    ]
    excluded = [
        excluded_projection(fact, decision_by_id[fact["id"]])
        for fact in deduplicated
        if decision_by_id[fact["id"]]["eligibility"] == "ineligible"
    ]

    current_actionable: list[dict[str, Any]] = []
    inactive_eligible = eligible
    source_rows = main_metrics.get("sourceRows", 0) + supplement_metrics.get("sourceRows", 0)
    skipped_rows = main_metrics.get("skippedRows", 0) + supplement_metrics.get("skippedRows", 0)
    parse_errors = main_metrics.get("parseErrors", 0) + supplement_metrics.get("parseErrors", 0)
    valid_rows = len(deduplicated)

    audit = {
        "sourceRows": source_rows,
        "validRows": valid_rows,
        "duplicateRows": len(duplicates),
        "skippedRows": skipped_rows,
        "parseErrors": parse_errors,
        "eligible": len(eligible),
        "ineligible": len(excluded),
        "needsConfirmation": len(pending),
        "currentActionable": len(current_actionable),
        "inactiveEligible": len(inactive_eligible),
        "interviewRosterRows": interview_rows,
        "interviewPositionCodes": len(interview_scores),
        "conservation": {
            "sourceRowsEqualsParsedOutcomes": source_rows
            == valid_rows + len(duplicates) + skipped_rows + parse_errors,
            "validRowsEqualsQualificationOutcomes": valid_rows
            == len(eligible) + len(excluded) + len(pending),
            "eligibleEqualsTimingOutcomes": len(eligible)
            == len(current_actionable) + len(inactive_eligible),
        },
    }
    if not all(audit["conservation"].values()):
        raise ValueError(f"National scan conservation failed: {audit}")

    run_dir = LOCAL_JOB_DIR / "runs" / run_id / DOMAIN
    decision_path = run_dir / "decisions.jsonl"
    catalog_count = write_jsonl(CATALOG_PATH, deduplicated)
    decision_count = write_jsonl(decision_path, decisions)

    domain = {
        "schemaVersion": "2.0",
        "domain": DOMAIN,
        "label": "国考",
        "cycle": CYCLE,
        "generatedAt": generated_at,
        "runId": run_id,
        "completeness": "complete",
        "profileSnapshot": {
            "hash": profile_hash,
            "updatedAt": profile.get("updatedAt", ""),
            "unknownFields": [
                "degree",
                "graduationYear",
                "freshGraduateStatus",
                "householdRegistration",
                "studentOrigin",
                "politicalStatus",
                "grassrootsYears",
                "workYears",
                "english",
                "computer",
                "professional",
                "hasRelevantWrittenExamScore",
            ],
        },
        "sourceScope": [
            "国家公务员局2026年度招考简章全部四个工作表",
            "国家公务员局2026年度补充录用职位表全部岗位",
            "国家公务员局2026年度进入面试人员名单全部记录",
        ],
        "sources": [
            {
                "id": "national-2026-main",
                "name": "中央机关及其直属机构2026年度考试录用公务员招考简章",
                "url": MAIN_URL,
                "portalUrl": PORTAL_URL,
                "checkedAt": generated_at,
                "artifact": {
                    "path": str(main_path.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256_file(main_path),
                    "rows": main_metrics.get("sourceRows", 0),
                },
            },
            {
                "id": "national-2026-supplement",
                "name": "中央机关及其直属机构2026年度补充录用职位表",
                "url": SUPPLEMENT_URL,
                "portalUrl": PORTAL_URL,
                "checkedAt": generated_at,
                "artifact": {
                    "path": str(supplement_path.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256_file(supplement_path),
                    "rows": supplement_metrics.get("sourceRows", 0),
                },
            },
            {
                "id": "national-2026-interview",
                "name": "中央机关及其直属机构2026年度进入面试人员名单",
                "url": INTERVIEW_URL,
                "portalUrl": PORTAL_URL,
                "checkedAt": generated_at,
                "artifact": {
                    "path": str(interview_path.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256_file(interview_path),
                    "rows": interview_rows,
                },
            },
        ],
        "catalog": {
            "path": str(CATALOG_PATH.relative_to(ROOT)).replace("\\", "/"),
            "rowCount": catalog_count,
            "profileIndependent": True,
        },
        "decisions": {
            "path": str(decision_path.relative_to(ROOT)).replace("\\", "/"),
            "rowCount": decision_count,
            "triState": ["eligible", "ineligible", "needs_confirmation"],
        },
        "positions": current_actionable,
        "referencePositions": inactive_eligible,
        "pendingVerification": pending,
        "excluded": excluded,
        "audit": audit,
        "notes": [
            "本文件没有迁移旧筛选结果，所有事实均由本次保存的2026官方附件重新解析。",
            "报名时效与资格判定分离：当前可报名为空，已截止但资格明确通过的岗位进入历史参考。",
            "画像字段未知时输出待确认，不把未知自动当作符合，也不从全量事实目录中删除。",
        ],
    }
    write_json(DOMAIN_PATH, domain)
    write_json(
        args.official_dir / "metadata.json",
        {
            "checkedAt": generated_at,
            "domain": DOMAIN,
            "cycle": CYCLE,
            "attachments": domain["sources"],
        },
    )
    write_json(
        run_dir / "audit.json",
        {
            "domain": DOMAIN,
            "cycle": CYCLE,
            "generatedAt": generated_at,
            "runId": run_id,
            "audit": audit,
        },
    )

    print(
        json.dumps(
            {
                "domain": DOMAIN,
                "runId": run_id,
                "catalogRows": catalog_count,
                "eligible": len(eligible),
                "needsConfirmation": len(pending),
                "ineligible": len(excluded),
                "currentActionable": len(current_actionable),
                "audit": audit["conservation"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
