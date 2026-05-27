"""Build the active eligible-position report from official recruitment checks.

This pipeline downloads official attachments for audit and filtering, but only
writes positions that are still open or about to open. Expired tables stay in
the scan record and never become display cards.
"""

from __future__ import annotations

import io
import json
import os
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError
from xml.etree import ElementTree as ET

import xlrd


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("GONGKAO_DATA_DIR", ROOT / "data"))
CONTENT_DIR = Path(os.getenv("GONGKAO_CONTENT_DIR", ROOT / "content" / "local"))
REPORT_PATH = CONTENT_DIR / "job" / "eligible-jobs.json"
OFFICIAL_SNAPSHOT_DIR = ROOT / "content" / "official" / "job" / "source-files"

MAIN_RESOURCE_ID = "8a81f6d19780e4080199e13f881f0153"
INTERVIEW_RESOURCE_ID = "8a81f6d09bb1deaf019bbfaf036b0011"
SUPPLEMENT_RESOURCE_ID = "8a81f6d09bb1deaf019e004d392d0964"
DOWNLOAD_BASE = "http://dl.scs.gov.cn/download/"
MAIN_URL = DOWNLOAD_BASE + MAIN_RESOURCE_ID
INTERVIEW_URL = DOWNLOAD_BASE + INTERVIEW_RESOURCE_ID
SUPPLEMENT_URL = DOWNLOAD_BASE + SUPPLEMENT_RESOURCE_ID
ARTICLE_URL = (
    "http://bm.scs.gov.cn/pp/gkweb/core/web/ui/business/home/gkhome.html"
)
UPCOMING_PORTAL_URL = "http://bm.scs.gov.cn/kl2027"
SJZ_ANNOUNCEMENT_URL = (
    "https://rsj.sjz.gov.cn/columns/cb3d71c6-1f88-4881-99e5-3ca252d801b0/"
    "202602/05/7a0b5bc0-3c38-4c0a-b742-69b9644acdf1.html"
)
SJZ_POSITIONS_URL = (
    "https://rsj.sjz.gov.cn/attachments/1/202602/05/"
    "1.%E7%9F%B3%E5%AE%B6%E5%BA%84%E5%B8%822026%E5%B9%B4%E4%BA%8B%E4%B8%9A"
    "%E5%8D%95%E4%BD%8D%E5%85%AC%E5%BC%80%E6%8B%9B%E8%81%98%EF%BC%88%E7"
    "%BB%9F%E4%B8%80%E6%8B%9B%E8%81%98%EF%BC%89%E5%B2%97%E4%BD%8D%E4%BF"
    "%A1%E6%81%AF%E8%A1%A820260205085141726.xlsx"
)
XIONGAN_ANNOUNCEMENT_URL = (
    "https://www.xiongan.gov.cn/20260205/135b7cfce4064382b7604b1e6963ff66/c.html"
)
XIONGAN_POSITIONS_URL = (
    "https://www.xiongan.gov.cn/20260205/135b7cfce4064382b7604b1e6963ff66/"
    "c5c1a0aa746241bfb5ebdb929c6f92f8.xlsx"
)
BEIJING_PLANNING_ANNOUNCEMENT_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/t20260526_4666099.html"
)
BEIJING_DISABLED_ANNOUNCEMENT_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/t20260526_4667242.html"
)
BEIJING_VETERAN_ANNOUNCEMENT_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/t20260525_4664125.html"
)
BEIJING_CUPES_ANNOUNCEMENT_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/t20260525_4664117.html"
)
BEIJING_MIYUN_ANNOUNCEMENT_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/t20260525_4664084.html"
)
SJZ_LATEST_SELECTION_URL = (
    "https://rsj.sjz.gov.cn/columns/cb3d71c6-1f88-4881-99e5-3ca252d801b0/"
    "202605/14/f64e89fc-bf91-477d-a601-17e45727dfd6.html"
)

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "wo-yao-shang-an/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_with_official_snapshot(url: str, snapshot_name: str) -> bytes:
    snapshot_path = OFFICIAL_SNAPSHOT_DIR / snapshot_name
    try:
        data = fetch(url)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_bytes(data)
        return data
    except Exception:
        if snapshot_path.exists():
            return snapshot_path.read_bytes()
        raise


def page_exists(url: str) -> bool:
    request = urllib.request.Request(url, headers={"User-Agent": "wo-yao-shang-an/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status == 200
    except HTTPError as error:
        if error.code == 404:
            return False
        raise


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, contents: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(contents, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def xlsx_rows(data: bytes) -> list[list[str]]:
    def column_index(reference: str) -> int:
        value = 0
        for character in reference:
            if not character.isalpha():
                break
            value = value * 26 + ord(character.upper()) - 64
        return value - 1

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = [
                "".join(node.text or "" for node in item.findall(".//a:t", NS))
                for item in root.findall("a:si", NS)
            ]

        root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: list[list[str]] = []
        for row_node in root.findall(".//a:sheetData/a:row", NS):
            cells: dict[int, str] = {}
            for cell in row_node.findall("a:c", NS):
                value_node = cell.find("a:v", NS)
                value = "" if value_node is None else value_node.text or ""
                if cell.attrib.get("t") == "s" and value:
                    value = shared[int(value)]
                cells[column_index(cell.attrib["r"])] = value.strip()
            rows.append([cells.get(index, "") for index in range(max(cells, default=-1) + 1)])
        return rows


def interview_scores(data: bytes) -> dict[tuple[str, str, str], str]:
    rows = xlsx_rows(data)
    scores: dict[tuple[str, str, str], str] = {}
    for row in rows[1:]:
        if len(row) < 8:
            continue
        key = (row[2], row[4], row[6])
        scores.setdefault(key, row[7])
    return scores


def allowed_location(location: str) -> bool:
    exact_districts = [
        "\u6cb3\u5317\u7701\u77f3\u5bb6\u5e84\u5e02\u4e95\u9649\u53bf",
        "\u6cb3\u5317\u7701\u77f3\u5bb6\u5e84\u5e02\u9e7f\u6cc9\u533a",
        "\u6cb3\u5317\u7701\u77f3\u5bb6\u5e84\u5e02\u4e95\u9649\u77ff\u533a",
        "\u6cb3\u5317\u7701\u77f3\u5bb6\u5e84\u5e02\u85c1\u57ce\u533a",
        "\u6cb3\u5317\u7701\u77f3\u5bb6\u5e84\u5e02\u683e\u57ce\u533a",
        "\u6cb3\u5317\u7701\u77f3\u5bb6\u5e84\u5e02\u6b63\u5b9a\u53bf",
        "\u6cb3\u5317\u7701\u4fdd\u5b9a\u5e02\u5bb9\u57ce\u53bf",
    ]
    return (
        location.startswith("\u5317\u4eac\u5e02")
        or location.startswith("\u5929\u6d25\u5e02")
        or any(district in location for district in exact_districts)
        or any(area in location for area in ["\u6cb3\u5317\u7701\u4fdd\u5b9a\u5e02\u96c4\u53bf", "\u6cb3\u5317\u7701\u4fdd\u5b9a\u5e02\u5b89\u65b0\u53bf"])
    )


def profile_confirms(row: dict[str, str], profile: dict) -> bool:
    basic = profile["basic"]
    qualifications = profile["qualification"]
    note = row["\u5907\u6ce8"]
    major = row["\u4e13\u4e1a"]

    if not allowed_location(row["\u5de5\u4f5c\u5730\u70b9"]):
        return False
    if not (
        "\u8ba1\u7b97\u673a\u7c7b" in major
        or "\u8ba1\u7b97\u673a\u79d1\u5b66\u4e0e\u6280\u672f" in major
    ):
        return False
    if "\u672c\u79d1" not in row["\u5b66\u5386"] or basic.get("education") != "\u672c\u79d1":
        return False
    if "\u5e94\u5c4a" in note or "2026\u5c4a" in note:
        return False
    if row["\u653f\u6cbb\u9762\u8c8c"] == "\u4e2d\u5171\u515a\u5458" and basic.get("politicalStatus") not in {
        "\u515a\u5458",
        "\u4e2d\u5171\u515a\u5458",
    }:
        return False
    if row["\u57fa\u5c42\u5de5\u4f5c\u6700\u4f4e\u5e74\u9650"] != "\u65e0\u9650\u5236":
        return False
    if "\u5973\u6027" in note or "\u9650\u5973" in note:
        return False
    if "\u7537\u6027" in note and basic.get("gender") != "\u7537":
        return False
    required_degree = row["\u5b66\u4f4d"]
    if required_degree and basic.get("degree") != "\u5b66\u58eb":
        return False
    if any(
        marker in note
        for marker in [
            "CET",
            "\u5927\u5b66\u82f1\u8bed",
            "\u82f1\u8bed\u56db\u7ea7",
            "\u82f1\u8bed\u516d\u7ea7",
            "\u96c5\u601d",
            "\u6258\u798f",
        ]
    ) and qualifications.get("englishLevel") in {"", "\u65e0"}:
        return False
    return True


def describe_work(row: dict[str, str]) -> str:
    official_summary = row["职位简介"].rstrip("。")
    if "税务局" in row["用人司局"] or "税务" in official_summary:
        inferred = (
            "结合税务机关职能推断，日常工作可能涉及税费征管、纳税缴费服务、"
            "申报数据核验及电子税务系统应用"
        )
    else:
        inferred = "结合招录单位职能推断，日常工作围绕该公告职责开展"
    return f"公告说明：{official_summary}。{inferred}；具体分工以单位安排为准。"


def estimated_compensation(location: str, category: str = "公务员") -> dict[str, str]:
    if location.startswith("北京市"):
        range_text = "参考税前年综合收入约 12 万至 20 万元"
    elif location.startswith("天津市"):
        range_text = "参考税前年综合收入约 10 万至 16 万元"
    elif category == "事业单位":
        range_text = "参考税前年综合收入约 6 万至 11 万元"
    else:
        range_text = "参考税前年综合收入约 7 万至 12 万元"
    return {
        "text": f"{range_text}。依据公务员岗位类别、工作地区与常见津补贴结构作宽区间推算。",
        "source": "岗位类别与工作地区推算",
        "disclaimer": "推算区间，非招录机关公布待遇，不作为报考或录用后的薪酬承诺。",
    }


def major_matches(major_requirement: str) -> bool:
    compact = major_requirement.replace(" ", "").replace("\n", "")
    return (
        not compact
        or "不限" in compact
        or "计算机类" in compact
        or "计算机科学与技术" in compact
    )


def other_conditions_confirmed(conditions: str, profile: dict) -> bool:
    compact = conditions.replace(" ", "").replace("\n", "")
    basic = profile["basic"]
    certificates = " ".join(profile.get("qualification", {}).get("certificates", []))
    if any(text in compact for text in ["应届高校毕业生", "高校毕业生（含择业期内）", "限女性"]):
        return False
    if "男性" in compact and basic.get("gender") != "男":
        return False
    if "中共党员" in compact and basic.get("politicalStatus") not in {"党员", "中共党员"}:
        return False
    if any(text in compact for text in ["教师资格", "执业证", "资格证书", "资格证"]) and not certificates:
        return False
    if any(text in compact for text in ["退役大学生士兵", "服务基层项目", "随军家属"]):
        return False
    if any(text in compact for text in ["工作经历", "工作经验"]):
        return False
    if "30周岁及以下" in compact and (basic.get("age") is None or basic["age"] > 30):
        return False
    return True


def describe_institution_work(unit: str, position: str) -> str:
    if "数据" in unit or "信息" in unit or "互联网" in unit or "网络" in unit:
        work = "信息系统运行维护、数据整理分析、网络信息服务及相关综合管理"
    elif "公共资源交易" in unit:
        work = "公共资源交易平台业务支持、数据管理和综合服务"
    elif "政务服务" in unit or "机关事务" in unit:
        work = "政务服务信息化支持、机关综合事务与数据管理"
    else:
        work = f"{unit}的{position}相关综合管理或技术支持"
    return f"岗位表未提供职责正文。根据单位名称与岗位类别推断，工作通常涉及{work}；具体以用人单位分工为准。"


def education_requirement(education: str, degree: str) -> str:
    return " / ".join(item for item in [education, degree] if item) or "以公告为准"


def judgement_fields(
    category: str,
    major: str,
    status: str,
    conditions: str = "",
    has_score: bool = False,
) -> dict:
    exact_major = "计算机类" in major or "计算机科学与技术" in major
    score = 92 if category == "公务员" and exact_major else 89 if exact_major else 83
    risk_level = "高" if status in {"已截止", "已结束"} else "中"
    reasons = [
        "专业要求覆盖计算机类或计算机科学与技术",
        "学历学位条件为本科、学士可覆盖范围",
        "工作地区属于当前关注区域",
    ]
    risks = ["该批公告报名已结束，仅适合作为下一轮同类岗位参照"] if risk_level == "高" else []
    if "最低服务期限" in conditions:
        risks.append("公告包含最低服务期限，录用后短期内调整地域的灵活性有限")
    study_advice = (
        ["持续关注下一年度国考职位表", "重点准备行测与申论，并积累税收征管、数字政务相关时政"]
        if category == "公务员"
        else ["关注同地区事业单位统一招聘公告", "按综合管理类或自然科学专技类笔试大纲安排刷题"]
    )
    return {
        "matchScore": score,
        "matchLevel": "高度适配" if score >= 90 else "较为适配",
        "riskLevel": risk_level,
        "recommendation": (
            "报考条件与方向较适配，可作为下一轮同类岗位重点关注对象；当前公告已结束，不能直接报名。"
        ),
        "matchReasons": reasons,
        "riskReminders": risks or ["公告条件需在报名前再次以职位表原文核验"],
        "studyAdvice": study_advice,
        "benefits": ["薪酬、社会保险和住房公积金执行录用单位政策，公告未列明的待遇不可视为承诺。"],
        "housingReference": "官方招聘材料未载明人才住房、配租或住房补贴安排。",
        "householdReference": "官方招聘材料未载明落户承诺，户口事项以录用后属地与单位政策为准。",
        "officialOnlyNotice": "岗位条件与考试数据来自官方附件；匹配结论、工作归纳和薪资区间为辅助判断信息。",
    }


def parse_sjz_positions(data: bytes, profile: dict, captured_at: str) -> list[dict]:
    rows = xlsx_rows(data)
    districts = ["井陉县", "鹿泉区", "井陉矿区", "藁城区", "栾城区", "正定县"]
    positions: list[dict] = []
    for row_number, row in enumerate(rows[3:], start=4):
        if len(row) < 11 or not any(district in " ".join(row) for district in districts):
            continue
        supervisor, unit, _, exam_category, title, education, degree, major, conditions, ratio, count = row[:11]
        if not major_matches(major) or not other_conditions_confirmed(conditions, profile):
            continue
        district = next(name for name in districts if name in " ".join(row))
        positions.append(
            {
                "id": f"sjz-sydw-2026-{row_number}",
                "title": title,
                "organization": unit,
                "department": supervisor,
                "category": "事业单位",
                "recruitmentType": "石家庄市2026年事业单位统一招聘（历史参考）",
                "region": f"河北省石家庄市{district}",
                "recruitCount": int(float(count)),
                "responsibilities": describe_institution_work(unit, title),
                "educationRequirement": education_requirement(education, degree),
                "majorRequirement": major,
                "freshGraduateRequirement": conditions or "以公告为准",
                "applicationNotes": [
                    f"公告其他条件：{conditions or '无特别说明'}",
                    f"公告开考比例为 {ratio}，不等同于报录比。",
                ],
                "historicalReferences": [],
                "compensationReference": estimated_compensation(f"河北省石家庄市{district}", "事业单位"),
                **judgement_fields("事业单位", major, "已结束", conditions),
                "status": "已结束",
                "sourceName": "石家庄市人社局：2026年事业单位公开招聘岗位信息表",
                "sourceUrl": SJZ_ANNOUNCEMENT_URL,
                "capturedAt": captured_at,
            }
        )
    return positions


def parse_xiongan_positions(data: bytes, profile: dict, captured_at: str) -> list[dict]:
    rows = xlsx_rows(data)
    positions: list[dict] = []
    for row in rows[4:]:
        if len(row) < 16:
            continue
        number, supervisor, unit, _, title, code, _, exam_category, count, ratio, major, education, degree, conditions, location, _ = row[:16]
        if not number.isdigit() or not major_matches(major) or not other_conditions_confirmed(conditions, profile):
            continue
        positions.append(
            {
                "id": f"xiongan-sydw-2026-{code}",
                "title": title.replace("\n", ""),
                "organization": unit,
                "department": supervisor,
                "positionCode": code,
                "category": "事业单位",
                "recruitmentType": "雄安新区2026年事业单位统一招聘（历史参考）",
                "region": f"河北雄安新区 / {location}",
                "recruitCount": int(float(count)),
                "responsibilities": describe_institution_work(unit, title.replace("\n", "")),
                "educationRequirement": education_requirement(education, degree),
                "majorRequirement": major,
                "freshGraduateRequirement": conditions or "无额外条件",
                "applicationNotes": [
                    f"公告其他条件：{conditions or '无特别说明'}",
                    f"公告面试比例为 {ratio}，不等同于报录比。",
                ],
                "historicalReferences": [],
                "compensationReference": estimated_compensation("河北雄安新区", "事业单位"),
                **judgement_fields("事业单位", major, "已结束", conditions),
                "status": "已结束",
                "sourceName": "中国雄安官网：2026年事业单位公开招聘岗位信息表",
                "sourceUrl": XIONGAN_ANNOUNCEMENT_URL,
                "capturedAt": captured_at,
            }
        )
    return positions


def parse_main_positions(data: bytes, profile: dict, scores: dict[tuple[str, str, str], str]) -> list[dict]:
    positions: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        filename = next(name for name in archive.namelist() if name.lower().endswith(".xls"))
        workbook = xlrd.open_workbook(file_contents=archive.read(filename))
    captured_at = datetime.now().astimezone().isoformat(timespec="seconds")

    for sheet in workbook.sheets():
        headers = [str(sheet.cell_value(1, index)).strip() for index in range(sheet.ncols)]
        for row_index in range(2, sheet.nrows):
            row = {
                header: str(sheet.cell_value(row_index, column_index)).strip()
                for column_index, header in enumerate(headers)
            }
            if not profile_confirms(row, profile):
                continue
            key = (
                row["\u90e8\u95e8\u540d\u79f0"],
                row["\u7528\u4eba\u53f8\u5c40"],
                row["\u804c\u4f4d\u4ee3\u7801"],
            )
            score = scores.get(key)
            interview_ratio = row["\u9762\u8bd5\u4eba\u5458\u6bd4\u4f8b"]
            location = row["\u5de5\u4f5c\u5730\u70b9"]
            positions.append(
                {
                    "id": "scs-2026-" + row["\u804c\u4f4d\u4ee3\u7801"],
                    "title": row["\u62db\u8003\u804c\u4f4d"],
                    "organization": row["\u90e8\u95e8\u540d\u79f0"],
                    "department": row["\u7528\u4eba\u53f8\u5c40"],
                    "positionCode": row["\u804c\u4f4d\u4ee3\u7801"],
                    "category": "\u516c\u52a1\u5458",
                    "recruitmentType": "2026\u5e74\u5ea6\u56fd\u8003\u4e3b\u62db\uff08\u5386\u53f2\u53c2\u8003\uff09",
                    "region": location,
                    "recruitCount": int(float(row["\u62db\u8003\u4eba\u6570"])),
                    "responsibilities": describe_work(row),
                    "educationRequirement": education_requirement(row["\u5b66\u5386"], row["\u5b66\u4f4d"]),
                    "majorRequirement": row["\u4e13\u4e1a"],
                    "freshGraduateRequirement": "\u4e0d\u9650\u5e94\u5c4a\uff08\u6839\u636e\u804c\u4f4d\u5907\u6ce8\u6838\u9a8c\uff09",
                    "applicationNotes": [
                        f"官方职位表载明面试人员比例为 {interview_ratio}，不等同于报录比。",
                        *([f"公告备注：{row['备注']}"] if row["备注"] else []),
                    ],
                    "historicalReferences": [
                        {
                            "year": "2026\u5e74\u5ea6\u56fd\u8003",
                            **({"finalEntryScore": score} if score else {}),
                            "recruitmentCount": row["\u62db\u8003\u4eba\u6570"],
                            "note": f"\u8fdb\u5165\u9762\u8bd5\u4eba\u5458\u540d\u5355\u516c\u5e03\u7684\u6700\u4f4e\u9762\u8bd5\u5206\u6570\uff1b\u804c\u4f4d\u8868\u9762\u8bd5\u4eba\u5458\u6bd4\u4f8b {interview_ratio}\uff0c\u975e\u62a5\u5f55\u6bd4\u3002",
                            "sourceName": "\u56fd\u5bb6\u516c\u52a1\u5458\u5c40\uff1a2026\u5e74\u5ea6\u8fdb\u5165\u9762\u8bd5\u4eba\u5458\u540d\u5355",
                            "sourceUrl": INTERVIEW_URL,
                        }
                    ],
                    "compensationReference": estimated_compensation(location),
                    **judgement_fields("\u516c\u52a1\u5458", row["\u4e13\u4e1a"], "\u5df2\u7ed3\u675f", row["\u5907\u6ce8"], bool(score)),
                    "status": "\u5df2\u7ed3\u675f",
                    "sourceName": "\u56fd\u5bb6\u516c\u52a1\u5458\u5c40\uff1a2026\u5e74\u5ea6\u62db\u8003\u7b80\u7ae0",
                    "sourceUrl": MAIN_URL,
                    "capturedAt": captured_at,
                }
            )
    return positions


def main() -> None:
    profile = read_json(DATA_DIR / "profile.local.json")
    report = read_json(REPORT_PATH) if REPORT_PATH.exists() else {"positions": []}
    now = datetime.now().astimezone().isoformat(timespec="minutes")
    national_positions = parse_main_positions(
        fetch(MAIN_URL),
        profile,
        interview_scores(fetch(INTERVIEW_URL)),
    )
    captured_at = now
    sjz_positions = parse_sjz_positions(
        fetch_with_official_snapshot(SJZ_POSITIONS_URL, "shijiazhuang-2026-unified-positions.xlsx"),
        profile,
        captured_at,
    )
    xiongan_positions = parse_xiongan_positions(
        fetch_with_official_snapshot(XIONGAN_POSITIONS_URL, "xiongan-2026-unified-positions.xlsx"),
        profile,
        captured_at,
    )
    upcoming_portal_published = page_exists(UPCOMING_PORTAL_URL)

    existing_sources = [
        {
            **source,
            "result": (
                "公告面向2026届高校毕业生，未纳入本轮可报岗位列表"
                if "高校毕业生" in source.get("result", "") and "届别条件" in source.get("result", "")
                else source.get("result", "")
            ),
        }
        for source in report.get("searchedSources", [])
        if source.get("name") != "\u56fd\u5bb6\u516c\u52a1\u5458\u5c40"
        and not source.get("name", "").startswith("\u56fd\u5bb6\u516c\u52a1\u5458\u5c40\uff1a")
        and not source.get("name", "").startswith("石家庄市人社局")
        and not source.get("name", "").startswith("石家庄市人事考试中心")
        and not source.get("name", "").startswith("中国雄安官网")
        and not source.get("name", "").startswith("北京市规划")
        and not source.get("name", "").startswith("北京市人社局：近期定向")
        and not source.get("name", "").startswith("首都体育学院")
        and not source.get("name", "").startswith("北京市密云区教育委员会")
        and not source.get("name", "").startswith("军队人才网")
    ]
    official_sources = [
        {
            "name": "\u56fd\u5bb6\u516c\u52a1\u5458\u5c40\uff1a2026\u5e74\u5ea6\u62db\u8003\u7b80\u7ae0\u4e0e\u9762\u8bd5\u540d\u5355",
            "url": MAIN_URL,
            "checkedAt": now,
            "result": f"\u5b98\u65b9\u4e3b\u62db\u9644\u4ef6\u4e0e\u9762\u8bd5\u540d\u5355\u5df2\u4e0b\u8f7d\u5e76\u5168\u91cf\u7b5b\u9009\uff1b\u8be5\u6279\u6b21\u5df2\u8003\u8bd5\u7ed3\u675f\uff0c\u547d\u4e2d\u7684 {len(national_positions)} \u4e2a\u5386\u53f2\u6761\u76ee\u4e0d\u8fdb\u5165\u5c97\u4f4d\u9875\u3002",
        },
        {
            "name": "\u56fd\u5bb6\u516c\u52a1\u5458\u5c40\uff1a2026\u5e74\u5ea6\u8865\u5145\u5f55\u7528\u516c\u544a\u4e0e\u804c\u4f4d\u8868",
            "url": SUPPLEMENT_URL,
            "checkedAt": now,
            "result": "\u62a5\u540d\u65f6\u95f4\u4e3a2026\u5e745\u67088\u65e5\u81f35\u670810\u65e5\uff0c\u5e76\u8981\u6c42\u53c2\u52a02026\u5e74\u5ea6\u56fd\u8003\u7b14\u8bd5\uff1b\u5f53\u524d\u5df2\u7ed3\u675f\uff0c\u4e0d\u4f5c\u4e3a\u53ef\u62a5\u5c97\u4f4d\u3002",
        },
        {
            "name": "国家公务员局：2027年度招录专题监测",
            "url": "https://www.scs.gov.cn/",
            "checkedAt": now,
            "result": (
                "国家公务员局 2027年度考试录用公务员专题入口已发布；必须下载并全量解析新年度职位附件。"
                if upcoming_portal_published
                else f"截至 {now[:10]}，官方专题入口 /kl2027 访问返回 404，暂无可导入的 2027年度职位表。"
            ),
        },
        {
            "name": "石家庄市人社局：2026年事业单位统一招聘岗位表",
            "url": SJZ_ANNOUNCEMENT_URL,
            "checkedAt": now,
            "result": f"已下载并筛选指定区县官方岗位附件；该批次笔试已结束，命中的 {len(sjz_positions)} 个历史条目不进入岗位页。",
        },
        {
            "name": "石家庄市人事考试中心：2026年公开选聘公告",
            "url": SJZ_LATEST_SELECTION_URL,
            "checkedAt": now,
            "result": "公告发布于2026年5月14日，现场报名为5月18日至22日；截至本次检索已经截止，不纳入可展示岗位。",
        },
        {
            "name": "中国雄安官网：2026年事业单位统一招聘岗位表",
            "url": XIONGAN_ANNOUNCEMENT_URL,
            "checkedAt": now,
            "result": f"已下载并筛选官方岗位附件；报名已于2026年2月13日结束且笔试已举行，命中的 {len(xiongan_positions)} 个历史条目不进入岗位页。",
        },
        {
            "name": "北京市规划和自然资源委员会所属事业单位公开招聘",
            "url": BEIJING_PLANNING_ANNOUNCEMENT_URL,
            "checkedAt": now,
            "result": "公告报名窗口为2026年5月28日至6月4日，包含计算机相关岗位；社会人员岗位载明北京市常住户口要求，未纳入符合岗位列表。",
        },
        {
            "name": "北京市人社局：近期定向编制招聘公告",
            "url": BEIJING_DISABLED_ANNOUNCEMENT_URL,
            "checkedAt": now,
            "result": "面向残疾人定向招聘，报名为2026年5月28日至6月3日；公告要求残疾人证和北京市户籍，未纳入可报岗位。",
        },
        {
            "name": "北京市人社局：近期定向编制招聘公告（退役大学生士兵）",
            "url": BEIJING_VETERAN_ANNOUNCEMENT_URL,
            "checkedAt": now,
            "result": "岗位附件已在官方公告提供，报名截至2026年6月1日17时；仅面向符合北京市定向条件的退役大学生士兵，未纳入可报岗位。",
        },
        {
            "name": "首都体育学院2026年公开招聘公告",
            "url": BEIJING_CUPES_ANNOUNCEMENT_URL,
            "checkedAt": now,
            "result": "事业编制岗位报名截至2026年6月8日18时；公告要求社会人员具有北京市常住户口，且应届口径为2025/2026届或符合条件的2024年离校未就业人员，未纳入可报岗位。",
        },
        {
            "name": "北京市密云区教育委员会2026年第二次招聘公告",
            "url": BEIJING_MIYUN_ANNOUNCEMENT_URL,
            "checkedAt": now,
            "result": "编制招聘报名截至2026年6月1日17时；公告要求社会人员具有北京市常住户口，未纳入可报岗位。",
        },
    ]
    category_map = {"事业单位": "编制", "教师": "编制", "医疗卫生": "编制", "国有企业": "国企"}
    other_positions = []
    for position in report.get("positions", []):
        if position.get("id", "").startswith(("scs-2026-", "sjz-sydw-2026-", "xiongan-sydw-2026-")):
            continue
        if position.get("status") not in {"报名中", "即将报名"}:
            continue
        normalized = {**position, "category": category_map.get(position.get("category"), position.get("category"))}
        if normalized.get("category") in {"公务员", "编制", "国企"}:
            other_positions.append(normalized)
    national_note = (
        "\u672c\u8f6e\u5df2\u4e0b\u8f7d\u5e76\u7b5b\u9009\u56fd\u5bb6\u516c\u52a1\u5458\u5c40\u5b98\u65b9\u62db\u8003\u7b80\u7ae0\u548c\u8fdb\u5165\u9762\u8bd5\u4eba\u5458\u540d\u5355\uff1b"
        f"\u5176\u4e2d\u547d\u4e2d\u753b\u50cf\u4e0e\u5730\u533a\u7684 {len(national_positions)} \u4e2a\u6761\u76ee\u5747\u5df2\u5b8c\u6210\u8003\u8bd5\uff0c\u5df2\u4ece\u5c97\u4f4d\u5c55\u793a\u4e2d\u79fb\u9664\u3002"
        "\u540c\u65f6\u6838\u9a8c\u56fd\u8003\u8865\u5f55\u516c\u544a\uff1a\u8865\u5f55\u62a5\u540d\u5df2\u4e8e2026\u5e745\u670810\u65e5\u7ed3\u675f\uff0c\u4e14\u9700\u6709\u672c\u5e74\u5ea6\u7b14\u8bd5\u6210\u7ee9\uff0c\u4e0d\u5c06\u5176\u6807\u6210\u53ef\u62a5\u3002"
        + (
            "\u56fd\u5bb6\u516c\u52a1\u5458\u5c402027\u5e74\u5ea6\u62db\u5f55\u4e13\u9898\u5165\u53e3\u5df2\u53d1\u5e03\uff0c\u672c\u6b21\u626b\u63cf\u5fc5\u987b\u8f6c\u5411\u65b0\u5e74\u5ea6\u9644\u4ef6\u3002"
            if upcoming_portal_published
            else f"\u622a\u81f3{now[:10]}\uff0c\u56fd\u5bb6\u516c\u52a1\u5458\u5c40 /kl2027 \u4e13\u9898\u5165\u53e3\u672a\u53d1\u5e03\uff08\u8bbf\u95ee\u8fd4\u56de404\uff09\uff0c\u65e0\u5b98\u65b92027\u5e74\u5ea6\u804c\u4f4d\u8868\u53ef\u5bfc\u5165\u3002"
        )
    )
    regional_note = (
        f"石家庄统一招聘官方附件命中 {len(sjz_positions)} 个条目但考试已结束，5月公开选聘也已于5月22日报名截止；"
        f"雄安统一招聘官方附件命中 {len(xiongan_positions)} 个条目但报名与笔试均已结束；"
        "北京市近期尚在窗口内的规划自然资源委、残疾人定向、退役大学生士兵定向、首都体育学院与密云教委编制公告，"
        "分别存在北京市常住户口、定向身份或届别等硬限制，未纳入岗位列表。"
    )
    report.update(
        {
            "generatedAt": now,
            "sourceScope": [
                "国家公务员局公务员招录官方入口",
                "北京市、天津市公务员与编制招聘官方入口",
                "天津市国资委及石家庄市国资委国企招聘官方入口",
                "中国雄安官网编制与国企通知公告",
                "石家庄市人社局及井陉县、鹿泉区、井陉矿区、藁城区、栾城区、正定县政府门户",
            ],
            "referencePolicy": (
                "岗位页仅展示仍在报名期或即将开放、且经画像硬条件筛选确认可报的公务员、编制和国企岗位；已考试或已结束批次只保留检索留痕。"
                "待遇、房子与户口优先采用公告原文，未载明时明确显示官方未载明；进面分和报录比仅展示可追溯官方数据。"
            ),
            "screeningNote": national_note
            + (f"\u5730\u65b9\u4e0e\u56fd\u4f01\u626b\u63cf\uff1a{regional_note}" if regional_note else ""),
            "searchedSources": official_sources + existing_sources,
            "regionalScanNote": regional_note,
            "positions": other_positions,
        }
    )
    report.pop("profileHash", None)
    write_json(REPORT_PATH, report)
    print(
        f"[岗位同步完成] 当前可展示 {len(other_positions)} 个 | 已排除历史国考 {len(national_positions)} 个 | "
        f"已排除历史石家庄编制 {len(sjz_positions)} 个 | 已排除历史雄安编制 {len(xiongan_positions)} 个 | "
        f"\u6765\u6e90 {ARTICLE_URL}"
    )


if __name__ == "__main__":
    main()
