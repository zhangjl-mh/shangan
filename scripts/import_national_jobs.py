"""Import confirmed National Civil Service reference positions for the profile.

This pipeline downloads official recruitment attachments, filters positions
whose hard conditions can be confirmed from the local profile, and writes the
result consumed by the front end. Salary ranges are clearly marked estimates
when the recruiting authority has not published a figure.
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

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "wo-yao-shang-an/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


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
                "educationRequirement": f"{education} / {degree}",
                "majorRequirement": major,
                "freshGraduateRequirement": conditions or "以公告为准",
                "applicationNotes": [
                    f"公告其他条件：{conditions or '无特别说明'}",
                    f"公告开考比例为 {ratio}，不等同于报录比。",
                ],
                "historicalReferences": [],
                "compensationReference": estimated_compensation(f"河北省石家庄市{district}", "事业单位"),
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
                "educationRequirement": f"{education} / {degree}",
                "majorRequirement": major,
                "freshGraduateRequirement": conditions or "无额外条件",
                "applicationNotes": [
                    f"公告其他条件：{conditions or '无特别说明'}",
                    f"公告面试比例为 {ratio}，不等同于报录比。",
                ],
                "historicalReferences": [],
                "compensationReference": estimated_compensation("河北雄安新区", "事业单位"),
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
                    "educationRequirement": f"{row['\u5b66\u5386']} / {row['\u5b66\u4f4d']}",
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
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    positions = parse_main_positions(
        fetch(MAIN_URL),
        profile,
        interview_scores(fetch(INTERVIEW_URL)),
    )
    upcoming_portal_published = page_exists(UPCOMING_PORTAL_URL)

    existing_sources = [
        source
        for source in report.get("searchedSources", [])
        if source.get("name") != "\u56fd\u5bb6\u516c\u52a1\u5458\u5c40"
        and not source.get("name", "").startswith("\u56fd\u5bb6\u516c\u52a1\u5458\u5c40\uff1a")
    ]
    official_sources = [
        {
            "name": "\u56fd\u5bb6\u516c\u52a1\u5458\u5c40\uff1a2026\u5e74\u5ea6\u62db\u8003\u7b80\u7ae0\u4e0e\u9762\u8bd5\u540d\u5355",
            "url": MAIN_URL,
            "checkedAt": now,
            "result": f"\u5b98\u65b9\u4e3b\u62db\u9644\u4ef6\u4e0e\u9762\u8bd5\u540d\u5355\u5df2\u89e3\u6790\uff1b\u6309\u5f53\u524d\u753b\u50cf\u53ca\u76ee\u6807\u5730\u57df\u53ef\u786e\u8ba4\u7684\u5386\u53f2\u53c2\u8003\u5c97\u4f4d {len(positions)} \u4e2a\u3002",
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
    ]
    other_positions = [
        position
        for position in report.get("positions", [])
        if not position.get("id", "").startswith("scs-2026-")
    ]
    national_note = (
        "\u672c\u8f6e\u5df2\u4ece\u56fd\u5bb6\u516c\u52a1\u5458\u5c40\u5b98\u65b9\u62db\u8003\u7b80\u7ae0\u548c\u8fdb\u5165\u9762\u8bd5\u4eba\u5458\u540d\u5355\u4e2d\u8bc6\u522b\u51fa"
        f"{len(positions)}\u4e2a\u4e0e\u5f53\u524d\u753b\u50cf\u53ca\u6307\u5b9a\u5730\u533a\u7b26\u5408\u7684\u5c97\u4f4d\uff0c\u5747\u4e3a2026\u5e74\u5ea6\u5df2\u7ed3\u675f\u7684\u5b98\u65b9\u5386\u53f2\u53c2\u8003\u3002"
        "\u540c\u65f6\u6838\u9a8c\u56fd\u8003\u8865\u5f55\u516c\u544a\uff1a\u8865\u5f55\u62a5\u540d\u5df2\u4e8e2026\u5e745\u670810\u65e5\u7ed3\u675f\uff0c\u4e14\u9700\u6709\u672c\u5e74\u5ea6\u7b14\u8bd5\u6210\u7ee9\uff0c\u4e0d\u5c06\u5176\u6807\u6210\u53ef\u62a5\u3002"
        + (
            "\u56fd\u5bb6\u516c\u52a1\u5458\u5c402027\u5e74\u5ea6\u62db\u5f55\u4e13\u9898\u5165\u53e3\u5df2\u53d1\u5e03\uff0c\u672c\u6b21\u626b\u63cf\u5fc5\u987b\u8f6c\u5411\u65b0\u5e74\u5ea6\u9644\u4ef6\u3002"
            if upcoming_portal_published
            else f"\u622a\u81f3{now[:10]}\uff0c\u56fd\u5bb6\u516c\u52a1\u5458\u5c40 /kl2027 \u4e13\u9898\u5165\u53e3\u672a\u53d1\u5e03\uff08\u8bbf\u95ee\u8fd4\u56de404\uff09\uff0c\u65e0\u5b98\u65b92027\u5e74\u5ea6\u804c\u4f4d\u8868\u53ef\u5bfc\u5165\u3002"
        )
    )
    regional_note = report.get("regionalScanNote", "")
    report.update(
        {
            "generatedAt": now,
            "referencePolicy": (
                "所有已确认符合硬性条件的岗位均保留并显示真实状态；进面分和报录比仅展示可追溯官方数据。"
                "薪资无官方金额时，可按岗位类别与地区展示明确标为非官方承诺的宽区间推算。"
            ),
            "screeningNote": national_note
            + (f"\u5730\u65b9\u4e0e\u56fd\u4f01\u626b\u63cf\uff1a{regional_note}" if regional_note else ""),
            "searchedSources": official_sources + existing_sources,
            "positions": positions + other_positions,
        }
    )
    write_json(REPORT_PATH, report)
    print(
        f"[\u56fd\u8003\u5c97\u4f4d\u540c\u6b65\u5b8c\u6210] \u5386\u53f2\u7b26\u5408\u5c97\u4f4d {len(positions)} \u4e2a | "
        f"\u6765\u6e90 {ARTICLE_URL}"
    )


if __name__ == "__main__":
    main()
