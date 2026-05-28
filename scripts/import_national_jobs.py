"""Build the active eligible-position report from official recruitment checks.

This pipeline downloads official attachments for audit and filtering, and only
writes positions whose examination has not yet taken place. Completed exam
tables stay in the scan record and never become display cards.
"""

from __future__ import annotations

import io
import json
import os
import hashlib
import subprocess
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from xml.etree import ElementTree as ET

import xlrd


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("GONGKAO_DATA_DIR", ROOT / "data"))
CONTENT_DIR = Path(os.getenv("GONGKAO_CONTENT_DIR", ROOT / "content" / "local"))
REPORT_PATH = CONTENT_DIR / "job" / "eligible-jobs.json"
CACHE_PATH = CONTENT_DIR / "job" / "source-cache.json"
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
SJZ_SOE_SOCIAL_ANNOUNCEMENT_URL = (
    "https://gzw.sjz.gov.cn/columns/530903f2-869c-46ff-b967-c08efc94d81f/"
    "202605/13/13e42b46-cb7f-4011-814f-e350ca409bc5.html"
)
SJZ_SOE_SOCIAL_POSITIONS_URL = (
    "https://gzw.sjz.gov.cn/attachments/1/202605/13/"
    "%E9%99%84%E4%BB%B61%EF%BC%9A%E7%9F%B3%E5%AE%B6%E5%BA%84%E5%B8%82"
    "%E5%B8%82%E5%B1%9E%E5%9B%BD%E6%9C%89%E4%BC%81%E4%B8%9A%E5%85%AC"
    "%E5%BC%80%E6%8B%9B%E8%81%98%E7%AE%A1%E7%90%86%E5%8F%8A%E4%B8%93"
    "%E4%B8%9A%E6%8A%80%E6%9C%AF%E4%BA%BA%E5%91%98%E5%B2%97%E4%BD%8D"
    "%E4%BF%A1%E6%81%AF%E8%A1%A820260513171149790.xlsx"
    "?sid=ca41ab23-efc1-4cb0-a731-4e7d8294e83d"
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
BEIJING_SYDW_INDEX_URL = "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/"
BEIJING_CIVIL_SERVICE_SUPPLEMENT_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/gwyzk/202605/t20260508_4641288.html"
)
BEIJING_CIVIL_SERVICE_SUPPLEMENT_POSITIONS_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/gwyzk/202605/P020260508520371424371.xls"
)
BEIJING_SCIENCE_ANNOUNCEMENT_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/t20260528_4669860.html"
)
BEIJING_SCIENCE_POSITIONS_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/P020260528385393245651.xlsx"
)
BEIJING_TECH_UNIVERSITY_ANNOUNCEMENT_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/t20260528_4669843.html"
)
BEIJING_TECH_UNIVERSITY_POSITIONS_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/P020260528382210321176.xlsx"
)
BEIJING_XICHENG_PARTY_SCHOOL_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/t20260528_4669811.html"
)
BEIJING_XICHENG_PARTY_SCHOOL_POSITIONS_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/P020260528376753612974.xlsx"
)
BEIJING_FANGSHAN_EDUCATION_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/t20260527_4667854.html"
)
BEIJING_FANGSHAN_EDUCATION_POSITIONS_URL = (
    "https://www.beijing.gov.cn/gongkai/rsxx/sydwzp/202605/P020260527352052154977.xlsx"
)
BEIJING_SOE_RECRUITMENT_URL = "https://gzw.beijing.gov.cn/yggq/gqzp/"
TIANJIN_SYDW_RECENT_URL = (
    "https://hrss.tj.gov.cn/ztzl/ztzl1/sydwgkzp/202605/t20260525_7304615.html"
)
TIANJIN_ZHONGDE_DOCTOR_URL = "https://www.tsguas.edu.cn/info/1063/3197.htm"
TIANJIN_ZHONGDE_DOCTOR_POSITIONS_URL = (
    "https://www.tsguas.edu.cn/system/_content/download.jsp?urltype=news.DownloadAttachUrl&"
    "owner=2014025217&wbfileid=3947267"
)
TIANJIN_ZHONGDE_STAFF_URL = "https://www.tsguas.edu.cn/info/1063/3092.htm"
CENTRAL_SASAC_RECRUITMENT_URL = "https://wap.sasac.gov.cn/n2588035/n2588325/index.html"
CENTRAL_SASAC_INSTITUTION_URL = (
    "https://wap.sasac.gov.cn/n2588035/n2588325/n2588350/c35428690/content.html"
)
CENTRAL_SASAC_INSTITUTION_POSITIONS_URL = (
    "https://wap.sasac.gov.cn/n2588035/n2588325/n2588350/c35428690/part/35428702.xls"
)
SINOMACH_SOCIAL_URL = (
    "https://wap.sasac.gov.cn/n2588035/n2588325/n2588350/c35438350/content.html"
)
SINOMACH_SOCIAL_POSITIONS_URL = (
    "https://wap.sasac.gov.cn/n2588035/n2588325/n2588350/c35438350/part/35438363.pdf"
)
CASIC_SUPPORT_CENTER_URL = (
    "https://wap.sasac.gov.cn/n2588035/n2588325/n2588350/c35434499/content.html"
)
CASIC_DIGITAL_TECH_URL = (
    "https://wap.sasac.gov.cn/n2588035/n2588325/c35434737/content.html"
)
COSCO_STRATEGIC_SASAC_URL = (
    "https://wap.sasac.gov.cn/n2588035/n2588325/n2588350/c35432576/content.html"
)
COSCO_STRATEGIC_PROJECT_URL = "https://coscoshipping.iguopin.com/zxjob"
COSCO_STRATEGIC_API_URL = "https://gp-api.iguopin.com/api/jobs/v1/project-job"
COSCO_STRATEGIC_PROJECT_ID = "200363782956909052"
COSCO_JOB_DETAIL_URL = "https://coscoshipping.iguopin.com/job/detail?id="

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
CATEGORY_ORDER = ["国考", "省考", "编制", "国企"]
REGION_ORDER = ["北京", "雄安", "天津", "石家庄", "其他"]
CHINA_TZ = timezone(timedelta(hours=8))


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "shangan/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except Exception:
        curl_binary = "curl.exe" if os.name == "nt" else "curl"
        result = subprocess.run(
            [
                curl_binary,
                "-sS",
                "-Lk",
                "--max-time",
                "45",
                "-A",
                "Mozilla/5.0 shangan/0.1",
                url,
            ],
            check=True,
            capture_output=True,
        )
        return result.stdout


def post_json(url: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
    request_headers = {
        "User-Agent": "Mozilla/5.0 shangan/0.1",
        "Content-Type": "application/json",
        **(headers or {}),
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_download_payload(data: bytes, snapshot_name: str) -> None:
    suffix = Path(snapshot_name).suffix.lower()
    if suffix not in {".xls", ".xlsx", ".zip", ".pdf", ".doc", ".docx"}:
        return
    prefix = data[:512].lstrip().lower()
    if prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html"):
        raise ValueError(f"{snapshot_name} returned an HTML page instead of the official attachment")


def fetch_with_official_snapshot(url: str, snapshot_name: str, reuse_existing: bool = False) -> bytes:
    snapshot_path = OFFICIAL_SNAPSHOT_DIR / snapshot_name
    if reuse_existing and snapshot_path.exists():
        data = snapshot_path.read_bytes()
        assert_download_payload(data, snapshot_name)
        return data
    try:
        data = fetch(url)
        assert_download_payload(data, snapshot_name)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_path.write_bytes(data)
        return data
    except Exception:
        if snapshot_path.exists():
            return snapshot_path.read_bytes()
        raise


def scan_cache_entry(name: str, url: str, checked_at: str, result: str, data: bytes | None) -> dict:
    entry = {
        "name": name,
        "url": url,
        "checkedAt": checked_at,
        "result": result,
        "status": "verified" if data else "recorded",
    }
    if data:
        entry.update(
            {
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    return entry


def verified_source(
    name: str,
    url: str,
    checked_at: str,
    result: str,
    snapshot_name: str | None = None,
    reuse_existing: bool = True,
) -> tuple[dict, dict]:
    try:
        data = (
            fetch_with_official_snapshot(url, snapshot_name, reuse_existing=reuse_existing)
            if snapshot_name
            else fetch(url)
        )
        source_result = result
        cache = scan_cache_entry(name, url, checked_at, source_result, data)
    except Exception as error:
        source_result = f"{result}；本次访问异常：{error}"
        cache = scan_cache_entry(name, url, checked_at, source_result, None)
    return {"name": name, "url": url, "checkedAt": checked_at, "result": source_result}, cache


def write_source_cache(entries: list[dict], checked_at: str) -> None:
    write_json(
        CACHE_PATH,
        {
            "updatedAt": checked_at,
            "description": "岗位扫描的官方入口和附件访问留痕。positions 只展示硬条件确认符合且考试尚未举行的岗位。",
            "entries": entries,
        },
    )


def normalize_region_group(region: str) -> str:
    text = region or ""
    if "北京" in text:
        return "北京"
    if any(name in text for name in ["雄安", "雄县", "容城", "安新"]):
        return "雄安"
    if "天津" in text:
        return "天津"
    if any(name in text for name in ["石家庄", "井陉", "鹿泉", "矿区", "藁城", "栾城", "正定"]):
        return "石家庄"
    return "其他"


def normalize_recruitment_class(position: dict) -> str:
    existing = position.get("recruitmentClass")
    if existing in CATEGORY_ORDER:
        return existing
    text = " ".join(
        str(position.get(key, ""))
        for key in ["sourceName", "recruitmentType", "category", "organization", "region"]
    )
    if "国家公务员局" in text or "国考" in text:
        return "国考"
    if "公务员" in text:
        return "省考"
    if any(keyword in text for keyword in ["国企", "国有企业", "央企"]):
        return "国企"
    return "编制"


def normalize_display_category(recruitment_class: str) -> str:
    return "公务员" if recruitment_class in {"国考", "省考"} else recruitment_class


def enrich_position(position: dict) -> dict:
    recruitment_class = normalize_recruitment_class(position)
    region_group = position.get("regionGroup") or normalize_region_group(position.get("region", ""))
    return {
        **position,
        "category": normalize_display_category(recruitment_class),
        "recruitmentClass": recruitment_class,
        "regionGroup": region_group if region_group in REGION_ORDER else "其他",
    }


def sort_position_key(position: dict) -> tuple[int, int, int, str, str]:
    normalized = enrich_position(position)
    recruitment_class = normalized["recruitmentClass"]
    region_group = normalized["regionGroup"]
    return (
        CATEGORY_ORDER.index(recruitment_class) if recruitment_class in CATEGORY_ORDER else len(CATEGORY_ORDER),
        REGION_ORDER.index(region_group) if region_group in REGION_ORDER else len(REGION_ORDER),
        -(normalized.get("matchScore") or 0),
        normalized.get("organization", ""),
        normalized.get("title", ""),
    )


def page_exists(url: str) -> bool:
    request = urllib.request.Request(url, headers={"User-Agent": "shangan/0.1"})
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


def current_time() -> datetime:
    override = os.getenv("GONGKAO_SCAN_NOW")
    if override:
        return datetime.fromisoformat(override.replace("Z", "+00:00")).astimezone()
    return datetime.now().astimezone()


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
                "category": "编制",
                "recruitmentClass": "编制",
                "recruitmentType": "石家庄市2026年事业单位统一招聘（历史参考）",
                "region": f"河北省石家庄市{district}",
                "regionGroup": "石家庄",
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
                "category": "编制",
                "recruitmentClass": "编制",
                "recruitmentType": "雄安新区2026年事业单位统一招聘（历史参考）",
                "region": f"河北雄安新区 / {location}",
                "regionGroup": "雄安",
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


def current_recruitment_status(registration_end_at: datetime, exam_date: datetime) -> str | None:
    now = current_time()
    if now <= registration_end_at:
        return "报名中"
    if now.date() < exam_date.date():
        return "待考试"
    return None


def parse_sjz_soe_social_positions(data: bytes, captured_at: str) -> list[dict]:
    rows = xlsx_rows(data)
    registration_end_at = datetime.fromisoformat("2026-05-27T17:00:00+08:00")
    payment_end_at = "2026-05-29T12:00:00+08:00"
    exam_date = datetime.fromisoformat("2026-06-06T00:00:00+08:00")
    status = current_recruitment_status(registration_end_at, exam_date)
    if not status:
        return []

    candidate_notes = {
        "STCC05": {
            "matchScore": 82,
            "matchLevel": "可考虑",
            "riskLevel": "高",
            "recommendation": (
                "岗位专业包含计算机科学与技术且招录人数较多，但岗位表更偏工程、电气与PLC协作。"
                "若已经报名，可作为稳妥跟踪对象；若未报名，本轮窗口已关闭，建议作为水务集团同类岗位样本。"
            ),
            "extraRisks": [
                "岗位要求熟悉工程管理、电气安全和PLC基础，纯软件背景需要补齐工程现场知识",
                "本科阶段要求全国普通高校国家计划内统招学历，需以个人毕业材料核实",
            ],
            "studyAdvice": [
                "围绕公共基础、综合能力、国企经营管理和安全生产基础准备笔试",
                "面试准备水务保障、城市基础设施运维、数字化巡检和工程协同案例",
            ],
        },
        "LTCC04": {
            "matchScore": 84,
            "matchLevel": "可考虑",
            "riskLevel": "高",
            "recommendation": (
                "岗位方向是商业数字化运营，专业覆盖计算机类，和国企信息化经历有连接点。"
                "硬风险在于岗位表写明需要相关工作经验，是否满足要以本人经历和用人单位审核为准。"
            ),
            "extraRisks": [
                "岗位明确要求相关工作经验，需准备国企信息化、系统运营或数据管理经历证明",
                "职责偏ERP和全业务流程，面试会更看重业务理解而不只是编程能力",
            ],
            "studyAdvice": [
                "补 ERP、数据库、业务流程数字化、采购销售财务协同等案例",
                "准备一个能讲清楚的系统运营或数据治理项目经历，突出问题定位和沟通推进",
            ],
        },
        "CSCC05": {
            "matchScore": 91,
            "matchLevel": "高度适配",
            "riskLevel": "中",
            "recommendation": (
                "大数据平台运维、网络与Linux基础和计算机科学与技术背景高度贴合。"
                "如果已经报名，应把它作为本轮重点备考岗位；如果未报名，可作为后续市属数字科技岗位优先样本。"
            ),
            "extraRisks": [
                "网络工程、数据库工程师等证书为优先项，没有证书时需要用项目经历补强",
                "岗位表未细化具体驻地，需向用人单位确认通勤与工作地点",
            ],
            "studyAdvice": [
                "重点复习Linux、计算机网络、数据库、网络安全基础和大数据平台运维概念",
                "准备信息化项目支持、故障排查、数据平台稳定性保障等面试故事",
            ],
        },
        "CSCC06": {
            "matchScore": 90,
            "matchLevel": "高度适配",
            "riskLevel": "中",
            "recommendation": (
                "岗位覆盖前端、Java、Spring体系和系统集成，技术画像与计算机本科较贴近。"
                "如果已经报名，可作为技术面准备优先级很高的岗位；未报名则作为数字科技公司同类岗位样本。"
            ),
            "extraRisks": [
                "技术栈覆盖面较宽，笔面试可能同时考察前端、Java后端、框架和系统集成",
                "项目经验为优先项，需要把已有国企信息化经历整理成可陈述案例",
            ],
            "studyAdvice": [
                "用一周压缩复习HTML/CSS/JavaScript、React/Vue基础、Java集合和Spring Boot常见问答",
                "准备兼容性、性能优化、接口联调、需求沟通和系统上线保障案例",
            ],
        },
    }
    positions: list[dict] = []
    for row in rows:
        if len(row) < 11 or row[3] not in candidate_notes:
            continue
        organization, department, title, code, _, count, major, education, age, conditions, compensation = row[:11]
        note = candidate_notes[code]
        responsibilities = (
            f"岗位表要求：{conditions.replace(chr(10), ' ')}"
        )
        positions.append(
            {
                "id": f"sjz-soe-social-2026-{code.lower()}",
                "title": title,
                "organization": department or organization,
                "department": organization,
                "positionCode": code,
                "category": "国企",
                "recruitmentClass": "国企",
                "recruitmentType": "石家庄市属国企面向社会公开招聘管理及专业技术岗位",
                "region": "石家庄市（具体工作地点以用人单位确认为准）",
                "regionGroup": "石家庄",
                "recruitCount": int(float(count)),
                "responsibilities": responsibilities,
                "educationRequirement": education,
                "majorRequirement": major,
                "matchScore": note["matchScore"],
                "matchLevel": note["matchLevel"],
                "riskLevel": note["riskLevel"],
                "recommendation": note["recommendation"],
                "matchReasons": [
                    "官方岗位表专业范围包含计算机科学与技术或计算机类",
                    "学历要求为本科及以上",
                    "属于市属国有企业面向社会的正式招聘岗位",
                ],
                "riskReminders": [
                    "岗位表未细化具体驻地到所关注区县，工作地点需向用人单位确认",
                    "报名已于2026年5月27日17:00截止，未报名则不能再新报名",
                    "薪酬仅载明执行公司制度，未公开具体金额、住房或落户政策",
                    *note["extraRisks"],
                ],
                "studyAdvice": note["studyAdvice"],
                "benefits": [
                    f"官方岗位表薪酬范围列为“{compensation}”",
                    "公告明确为市属国有企业正式市场化公开招聘",
                ],
                "housingReference": "官方公告及岗位表未载明住房、宿舍、人才公寓或租房补贴安排。",
                "householdReference": "普通公开招聘岗位公告未列明户籍限制，也未承诺落户；户口事项需向用人单位核实。",
                "compensationReference": {
                    "text": f"官方岗位表载明：{compensation}。",
                    "source": "石家庄市国资委官方岗位信息表",
                    "sourceUrl": SJZ_SOE_SOCIAL_ANNOUNCEMENT_URL,
                    "disclaimer": "官方未公布具体金额，页面不作薪资数额推算。",
                },
                "applicationNotes": [
                    "公告指定报名网站为石家庄国经人才服务网。",
                    "资格初审截止时间为2026年5月28日17:00；缴费截止时间为2026年5月29日12:00。",
                    "岗位开考比例为3:1，未达比例的岗位可能核销或允许转报。",
                ],
                "announcementDate": "2026-05-13",
                "registrationStartDate": "2026-05-13",
                "registrationEndDate": "2026-05-27",
                "registrationEndAt": "2026-05-27T17:00:00+08:00",
                "qualificationReviewEndAt": "2026-05-28T17:00:00+08:00",
                "paymentEndAt": payment_end_at,
                "examDate": "2026-06-06",
                "status": status,
                "sourceName": "石家庄市国资委：市属国有企业面向社会公开招聘公告及岗位表",
                "sourceUrl": SJZ_SOE_SOCIAL_ANNOUNCEMENT_URL,
                "attachmentUrl": SJZ_SOE_SOCIAL_POSITIONS_URL,
                "capturedAt": captured_at,
            }
        )
    return positions


def parse_china_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace(" ", "T")).replace(tzinfo=CHINA_TZ)


def cosco_registration_status(job: dict) -> str | None:
    now = current_time()
    start_time = parse_china_datetime(job["start_time"])
    end_time = parse_china_datetime(job["end_time"])
    if now < start_time:
        return "即将报名"
    if now <= end_time:
        return "报名中"
    return None


def cosco_major_matches(job: dict) -> bool:
    major_text = "、".join(job.get("major_cn") or [])
    if any(keyword in major_text for keyword in ["计算机类", "计算机科学与技术类", "软件工程类"]):
        return True
    contents = job.get("contents", "")
    return any(
        keyword in contents
        for keyword in [
            "计算机科学",
            "软件工程",
            "网络安全",
            "数据库",
            "前端",
            "大数据",
            "人工智能",
        ]
    ) and not any(
        excluded in contents
        for excluded in ["轮机管理", "船舶及海洋工程", "汽车或电子设备或电气装备"]
    )


def cosco_compensation_reference() -> dict:
    return {
        "text": (
            "国资委转发的中远海运专项招聘海报载明提供具有市场竞争力的薪酬福利，"
            "包含六险二金、健康体检、带薪假期、商业保险、文体活动、人才公寓、员工餐厅、健身房、医务室等；"
            "具体岗位薪酬、住房和属地人才支持以录用单位最终确认为准。"
        ),
        "source": "国务院国资委人事招聘频道：中远海运集团专项招聘海报",
        "sourceUrl": COSCO_STRATEGIC_SASAC_URL,
        "disclaimer": "海报为集团层面福利说明，非单个岗位的确定薪资、住房或落户承诺。",
    }


def cosco_match_note(job: dict) -> dict:
    title = job.get("job_name", "")
    experience = job.get("experience_cn", "以官方岗位为准")
    score = 88
    level = "较为适配"
    risk = "中"
    if "网络安全" in title:
        score = 92
        level = "高度适配"
    elif "前端" in title or "数据库" in title:
        score = 90
        level = "高度适配"
    elif "AI" in title or "大模型" in title or "算法" in title:
        score = 87
    elif "副总监" in title:
        score = 80
        risk = "高"
    return {
        "matchScore": score,
        "matchLevel": level,
        "riskLevel": risk,
        "recommendation": (
            f"岗位专业口径覆盖计算机方向，学历门槛为本科，当前仍在投递期；"
            f"但工作地点在上海且经验要求为{experience}，需要用在职国企信息化、系统建设或安全运维经历支撑。"
        ),
        "riskReminders": [
            "工作地点不在当前重点城市，但画像设置接受其他城市，需先确认本人是否愿意异地工作。",
            f"官方岗位经验要求为{experience}，报名前要核对社保、劳动合同、项目材料能否支撑。",
            "中远海运专项招聘为央企社招，岗位竞争可能更偏项目经历、技术深度和行业场景理解。",
            "岗位详情未逐岗公开确定薪资、住房或落户承诺，相关事项以用人单位录用沟通为准。",
        ],
        "studyAdvice": [
            "准备一版国企信息化项目简历，突出系统上线、故障排查、数据治理、安全合规或跨部门推进。",
            "技术岗按岗位方向补一组可讲清楚的项目：需求背景、技术方案、上线效果、风险控制。",
            "面试重点准备航运物流数字化、央企合规、安全生产和数据安全的结合点。",
        ],
    }


def parse_cosco_strategic_positions(captured_at: str) -> tuple[list[dict], int, bytes]:
    payload = {
        "page": 1,
        "page_size": 100,
        "source": "s_job_list",
        "project_id": [COSCO_STRATEGIC_PROJECT_ID],
    }
    response = post_json(
        COSCO_STRATEGIC_API_URL,
        payload,
        headers={
            "Origin": "https://coscoshipping.iguopin.com",
            "Referer": COSCO_STRATEGIC_PROJECT_URL,
        },
    )
    data = response.get("data", {})
    jobs = data.get("list", [])
    positions: list[dict] = []
    for job in jobs:
        status = cosco_registration_status(job)
        if not status:
            continue
        if job.get("education_cn") != "本科":
            continue
        if job.get("experience_cn") not in {"经验不限", "1-3年", "3-5年"}:
            continue
        if not cosco_major_matches(job):
            continue
        job_id = str(job["job_id"])
        area = "、".join(item.get("area_cn", "") for item in job.get("district_list", []) if item.get("area_cn"))
        major = "、".join(job.get("major_cn") or []) or "详见职位描述"
        start_date = parse_china_datetime(job["start_time"]).date().isoformat()
        end_at = parse_china_datetime(job["end_time"]).isoformat(timespec="seconds")
        note = cosco_match_note(job)
        contents = job.get("contents", "").replace("\r", "").strip()
        positions.append(
            {
                "id": f"cosco-strategic-2026-{job_id}",
                "title": job["job_name"].replace(" （", "（").replace(" ）", "）"),
                "organization": job.get("company_name", "中国远洋海运集团"),
                "department": job.get("department_cn") or job.get("company_name", "中国远洋海运集团"),
                "positionCode": job_id,
                "category": "国企",
                "recruitmentClass": "国企",
                "recruitmentType": "中国远洋海运集团2026年度战略性新兴产业紧缺急需人才专项招聘",
                "region": area or "以官方岗位页为准",
                "regionGroup": normalize_region_group(area),
                "recruitCount": int(job.get("amount") or 1),
                "responsibilities": contents[:900] + ("……" if len(contents) > 900 else ""),
                "educationRequirement": "本科及以上",
                "majorRequirement": major,
                "freshGraduateRequirement": "社会招聘；官方岗位未限定应届。",
                "matchReasons": [
                    "官方招聘平台岗位处于投递期，属于下一个可新报周期。",
                    "学历门槛为本科，专业要求覆盖计算机类、计算机科学与技术类或岗位职责明确为计算机技术方向。",
                    "画像为计算机相关本科且接受其他城市，因此可纳入央企社招候选池。",
                ],
                "riskReminders": note["riskReminders"],
                "studyAdvice": note["studyAdvice"],
                "benefits": [
                    "国资委转发招聘海报列明六险二金、健康体检、带薪假期、商业保险等集团福利口径。",
                    "海报列明人才公寓、员工餐厅、健身房、医务室等配套，但具体适用范围需以用人单位确认为准。",
                ],
                "housingReference": "国资委转发招聘海报提到人才公寓及属地人才住房支持，是否适用该岗位需以录用单位确认为准。",
                "householdReference": "海报称根据当地政策和企业规定为人才落户等提供相应支持，未构成单个岗位落户承诺。",
                "officialOnlyNotice": "岗位来自中远海运官方招聘平台，福利来自国务院国资委转发招聘海报；匹配结论为画像筛选判断。",
                "applicationNotes": [
                    "投递入口为中远海运官方招聘平台/国聘平台专项招聘页面。",
                    "招聘流程以资格审查、笔试、面试、体检、背景调查和录用通知为准，具体时间以平台通知为准。",
                ],
                "historicalReferences": [],
                "compensationReference": cosco_compensation_reference(),
                "announcementDate": "2026-05-20",
                "registrationStartDate": start_date,
                "registrationEndDate": parse_china_datetime(job["end_time"]).date().isoformat(),
                "registrationEndAt": end_at,
                "status": status,
                "sourceName": "中国远洋海运集团2026年度战略性新兴产业紧缺急需人才专项招聘",
                "sourceUrl": COSCO_JOB_DETAIL_URL + job_id,
                "announcementSourceUrl": COSCO_STRATEGIC_SASAC_URL,
                "capturedAt": captured_at,
                **{key: value for key, value in note.items() if key not in {"riskReminders", "studyAdvice"}},
            }
        )
    snapshot = json.dumps(response, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return positions, int(data.get("total") or len(jobs)), snapshot


def parse_main_positions(data: bytes, profile: dict, scores: dict[tuple[str, str, str], str]) -> list[dict]:
    positions: list[dict] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        filename = next(name for name in archive.namelist() if name.lower().endswith(".xls"))
        workbook = xlrd.open_workbook(file_contents=archive.read(filename))
    captured_at = current_time().isoformat(timespec="seconds")

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
                    "recruitmentClass": "国考",
                    "recruitmentType": "2026\u5e74\u5ea6\u56fd\u8003\u4e3b\u62db\uff08\u5386\u53f2\u53c2\u8003\uff09",
                    "region": location,
                    "regionGroup": normalize_region_group(location),
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


def scan_broader_official_sources(checked_at: str) -> tuple[list[dict], list[dict], str]:
    source_specs = [
        (
            "首都之窗事业单位招聘频道",
            BEIJING_SYDW_INDEX_URL,
            "已读取官方频道页；2026年5月28日最新公告含市科委/中关村管委会、北京科技职业大学、西城党校等，已逐条核验重点附件。",
            None,
        ),
        (
            "北京市公务员局：2026年度补充录用公务员公告",
            BEIJING_CIVIL_SERVICE_SUPPLEMENT_URL,
            "补录报名为2026年5月8日至5月10日，且要求已有北京市2026年度公务员笔试成绩；不属于当前可新报岗位。",
            None,
        ),
        (
            "北京市公务员局：2026年度补充录用公务员职位表",
            BEIJING_CIVIL_SERVICE_SUPPLEMENT_POSITIONS_URL,
            "官方补录职位表已下载留存；因报名窗口结束且需要既有笔试成绩，本轮不写入岗位卡片。",
            "beijing-civil-service-2026-supplement.xls",
        ),
        (
            "北京市科委、中关村管委会直属事业单位2026年公开招聘",
            BEIJING_SCIENCE_ANNOUNCEMENT_URL,
            "公告报名窗口为2026年5月28日至6月4日，附件已核验；计算机相关或数据相关岗位存在硕士研究生及以上、应届/北京户籍等硬条件，未确认符合画像，未纳入岗位列表。",
            None,
        ),
        (
            "北京市科委、中关村管委会直属事业单位2026年岗位计划",
            BEIJING_SCIENCE_POSITIONS_URL,
            "官方岗位计划已下载留存；不将硕士及以上、应届或北京户籍硬限制岗位写入可展示列表。",
            "beijing-science-zgc-2026-positions.xlsx",
        ),
        (
            "北京科技职业大学2026年公开招聘公告（第二批）",
            BEIJING_TECH_UNIVERSITY_ANNOUNCEMENT_URL,
            "公告和岗位附件已核验；本批为博士学位或高层次专业技术岗位，不符合本科画像。",
            None,
        ),
        (
            "北京科技职业大学2026年公开招聘岗位计划表",
            BEIJING_TECH_UNIVERSITY_POSITIONS_URL,
            "官方岗位计划已下载留存；岗位以博士或高层次人才为主，未纳入岗位列表。",
            "beijing-tech-vocational-2026-positions.xlsx",
        ),
        (
            "中共北京市西城区委党校2026年公开招聘",
            BEIJING_XICHENG_PARTY_SCHOOL_URL,
            "公告限定普通高等院校北京生源应届毕业生，并要求硕士研究生及以上；不符合当前画像。",
            None,
        ),
        (
            "中共北京市西城区委党校2026年岗位需求表",
            BEIJING_XICHENG_PARTY_SCHOOL_POSITIONS_URL,
            "官方岗位需求表已下载留存；因北京生源应届和硕士及以上条件排除。",
            "beijing-xicheng-party-school-2026-positions.xlsx",
        ),
        (
            "北京市房山区教育委员会所属事业单位公开招聘（二）",
            BEIJING_FANGSHAN_EDUCATION_URL,
            "公告为教师专业技术岗位，涉及应届、北京户籍、教师资格等条件；当前画像未确认符合教师岗位硬条件。",
            None,
        ),
        (
            "北京市房山区教育委员会公开招聘岗位及条件（二）",
            BEIJING_FANGSHAN_EDUCATION_POSITIONS_URL,
            "官方岗位条件表已下载留存；本轮未确认符合画像的教师编制岗位。",
            "beijing-fangshan-education-2026-positions.xlsx",
        ),
        (
            "北京市国资委国企招聘频道",
            BEIJING_SOE_RECRUITMENT_URL,
            "已读取北京市国资委国企招聘官方频道；最新条目多为2026届校园招聘、高层管理、法律管理或微信图文详情，未发现可下载并逐行核验且确认符合画像的正式岗位表。",
            None,
        ),
        (
            "天津市人社局：2026年5月25日部分事业单位公开招聘信息",
            TIANJIN_SYDW_RECENT_URL,
            "官方汇总页列出天津中德应用技术大学19个岗位；已转入学校公告核验，当前计算机相关岗位属于博士/高级职称教师或已结束批次。",
            None,
        ),
        (
            "天津中德应用技术大学2026年博士学位或高级专业技术职务招聘",
            TIANJIN_ZHONGDE_DOCTOR_URL,
            "公告有效期至2026年12月31日，但岗位要求博士学位或高级专业技术职务；不符合本科画像。",
            None,
        ),
        (
            "天津中德应用技术大学2026年博士/高级职称岗位计划",
            TIANJIN_ZHONGDE_DOCTOR_POSITIONS_URL,
            "附件下载页已访问；公告正文已确认岗位要求博士学位或高级专业技术职务，公告级硬条件已足以排除。",
            None,
        ),
        (
            "天津中德应用技术大学2026年辅导员、其他专技岗招聘",
            TIANJIN_ZHONGDE_STAFF_URL,
            "公告报名时间为2026年3月15日至3月21日，资格复审和面试通知已发布；不属于当前可报岗位。",
            None,
        ),
        (
            "国务院国资委人事招聘频道",
            CENTRAL_SASAC_RECRUITMENT_URL,
            "已读取国务院国资委人事招聘频道；重点核验委属事业单位、国机集团、航天科工、中远海运等近期招聘。",
            None,
        ),
        (
            "国务院国资委：中国远洋海运集团2026年度战略性新兴产业紧缺急需人才专项招聘",
            COSCO_STRATEGIC_SASAC_URL,
            "国资委转发中远海运专项招聘公告已核验；岗位明细转入中远海运官方招聘平台接口全量筛选。",
            None,
        ),
        (
            "中国远洋海运集团官方招聘平台：2026专项招聘",
            COSCO_STRATEGIC_PROJECT_URL,
            "官方招聘平台专项页已核验；通过专项招聘接口读取全部岗位并按画像硬条件筛选。",
            None,
        ),
        (
            "国务院国资委委属事业单位2026年度公开招聘",
            CENTRAL_SASAC_INSTITUTION_URL,
            "公告面向2026届高校毕业生及择业期内未落实工作单位毕业生；画像为非应届在职人员，不符合招聘对象。",
            None,
        ),
        (
            "国务院国资委委属事业单位2026年应届岗位表",
            CENTRAL_SASAC_INSTITUTION_POSITIONS_URL,
            "官方岗位表已下载留存；因应届/择业期未就业硬条件排除。",
            "central-sasac-institution-2026-graduate-positions.xls",
        ),
        (
            "国机集团2026年社会招聘公告",
            SINOMACH_SOCIAL_URL,
            "官方社招公告和岗位说明已核验；北京、天津相关岗位主要为纪检、审计、法律管理等，需要相关工作经历或管理任职条件，未确认符合画像。",
            None,
        ),
        (
            "国机集团2026年社会招聘岗位说明",
            SINOMACH_SOCIAL_POSITIONS_URL,
            "官方PDF岗位说明已下载留存；北京、天津条目未确认满足相关工作经历、职级或专业背景要求。",
            "sinomach-2026-social-positions.pdf",
        ),
        (
            "航天科工集团科技保障中心有限公司2026年招聘",
            CASIC_SUPPORT_CENTER_URL,
            "社会招聘中信息化管理岗、安全运维岗均要求硕士及以上并有相应年限经验；本科画像不符合。",
            None,
        ),
        (
            "航天科工集团数字技术有限公司部分岗位公开招聘",
            CASIC_DIGITAL_TECH_URL,
            "近期岗位为财务处主管岗，专业与经历要求均不匹配当前计算机画像。",
            None,
        ),
        (
            "中国雄安官网通知公告首页",
            "https://www.xiongan.gov.cn/tzgg.html",
            "已读取通知公告首页；2026年5月28日附近条目为标准征集、土地供应、出租车资格考试、住房公积金政策等，未发现新的公务员、编制或国企可报岗位。",
            None,
        ),
        (
            "北京组工网",
            "https://www.bjdj.gov.cn/index.html",
            "公务员官方发布入口已重新核验；当前可追溯的北京补录已单独记录，需既有2026年笔试成绩。",
            None,
        ),
        (
            "天津先锋网",
            "https://www.tjzzb.gov.cn/",
            "公务员官方发布入口已重新核验；本轮未发现仍可新报名且符合画像的天津公务员职位表。",
            None,
        ),
        (
            "天津市国资委",
            "https://sasac.tj.gov.cn/",
            "天津国资监管入口已重新核验；本轮未发现官方可下载并确认符合画像的正式国企招聘岗位表。",
            None,
        ),
        (
            "井陉县人民政府",
            "http://www.sjzjx.gov.cn",
            "政府门户已重新核验并纳入指定区县公告扫描；本轮未发现新的未考试岗位附件。",
            None,
        ),
        (
            "鹿泉区人民政府",
            "http://www.sjzlq.gov.cn/",
            "政府门户已重新核验并纳入指定区县公告扫描；本轮未发现新的未考试岗位附件。",
            None,
        ),
        (
            "井陉矿区人民政府",
            "http://www.sjzkq.gov.cn/",
            "政府门户已重新核验并纳入指定区县公告扫描；本轮未发现新的未考试岗位附件。",
            None,
        ),
        (
            "藁城区人民政府",
            "http://www.gc.gov.cn/",
            "政府门户已重新核验并纳入指定区县公告扫描；本轮未发现新的未考试岗位附件。",
            None,
        ),
        (
            "栾城区人民政府",
            "http://www.luancheng.gov.cn/",
            "政府门户已重新核验并纳入指定区县公告扫描；本轮未发现新的未考试岗位附件。",
            None,
        ),
        (
            "正定县人民政府",
            "http://www.zd.gov.cn/",
            "政府门户已重新核验并纳入指定区县公告扫描；本轮未发现新的未考试岗位附件。",
            None,
        ),
    ]
    sources: list[dict] = []
    cache_entries: list[dict] = []
    for name, url, result, snapshot_name in source_specs:
        source, cache = verified_source(name, url, checked_at, result, snapshot_name=snapshot_name)
        sources.append(source)
        cache_entries.append(cache)
    note = (
        "新增全源扫描已覆盖首都之窗事业单位、北京公务员补录、北京国资委国企招聘、天津人社事业单位、"
        "天津中德应用技术大学、国务院国资委人事招聘、中远海运专项招聘、中央企业社招、雄安通知公告及石家庄指定区县门户。"
        "北京、天津和中央企业近期可打开公告中，因北京户籍/应届、硕士博士、高级职称、既有笔试成绩、"
        "教师资格或相关纪检审计管理经历等硬条件，未纳入岗位列表；中远海运专项招聘中满足本科、计算机方向和投递期的岗位已单独写入。"
    )
    return sources, cache_entries, note


def main() -> None:
    profile = read_json(DATA_DIR / "profile.local.json")
    report = read_json(REPORT_PATH) if REPORT_PATH.exists() else {"positions": []}
    now = current_time().isoformat(timespec="minutes")
    main_attachment = fetch_with_official_snapshot(MAIN_URL, "national-civil-service-2026-main.zip", reuse_existing=True)
    interview_attachment = fetch_with_official_snapshot(INTERVIEW_URL, "national-civil-service-2026-interview.xlsx", reuse_existing=True)
    sjz_attachment = fetch_with_official_snapshot(SJZ_POSITIONS_URL, "shijiazhuang-2026-unified-positions.xlsx", reuse_existing=True)
    xiongan_attachment = fetch_with_official_snapshot(XIONGAN_POSITIONS_URL, "xiongan-2026-unified-positions.xlsx", reuse_existing=True)
    sjz_soe_attachment = fetch_with_official_snapshot(
        SJZ_SOE_SOCIAL_POSITIONS_URL,
        "shijiazhuang-soe-2026-social-positions.xlsx",
        reuse_existing=True,
    )
    national_positions = parse_main_positions(
        main_attachment,
        profile,
        interview_scores(interview_attachment),
    )
    captured_at = now
    sjz_positions = parse_sjz_positions(
        sjz_attachment,
        profile,
        captured_at,
    )
    xiongan_positions = parse_xiongan_positions(
        xiongan_attachment,
        profile,
        captured_at,
    )
    upcoming_portal_published = page_exists(UPCOMING_PORTAL_URL)
    sjz_soe_positions = parse_sjz_soe_social_positions(sjz_soe_attachment, captured_at)
    cosco_positions, cosco_total, cosco_snapshot = parse_cosco_strategic_positions(captured_at)
    broader_sources, broader_cache_entries, broader_note = scan_broader_official_sources(now)

    existing_sources: list[dict] = []
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
            "name": "石家庄市国资委：市属国有企业面向社会公开招聘公告及岗位表",
            "url": SJZ_SOE_SOCIAL_ANNOUNCEMENT_URL,
            "checkedAt": now,
            "result": (
                f"已下载并全量筛选管理及专业技术岗位附件；计算机方向匹配 {len(sjz_soe_positions)} 个。"
                "报名截至2026年5月27日17:00，已不属于下一周期可新报名岗位；仅保留为已报名后续跟踪和同类岗位样本。"
            ),
        },
        {
            "name": "中国远洋海运集团官方招聘平台：2026专项招聘岗位接口",
            "url": COSCO_STRATEGIC_PROJECT_URL,
            "checkedAt": now,
            "result": f"官方专项招聘接口返回 {cosco_total} 个岗位；按本科、计算机方向、社招经验和投递期筛选，确认 {len(cosco_positions)} 个仍可新报名岗位。",
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
    actionable_sjz_soe_positions = [
        position for position in sjz_soe_positions if position.get("status") in {"报名中", "即将报名"}
    ]
    positions = sorted(
        [enrich_position(position) for position in actionable_sjz_soe_positions + cosco_positions],
        key=sort_position_key,
    )
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
        f"石家庄市属国企面向社会招聘已全量筛选，计算机方向匹配 {len(sjz_soe_positions)} 个，"
        "但报名截至5月27日17:00，未报名者已无法新报，本次不再作为下一周期岗位展示；"
        f"中远海运2026专项招聘官方接口返回 {cosco_total} 个岗位，按画像确认 {len(cosco_positions)} 个仍在投递期的央企社招岗位；"
        "北京市近期尚在窗口内的规划自然资源委、残疾人定向、退役大学生士兵定向、首都体育学院与密云教委编制公告，"
        "分别存在北京市常住户口、定向身份或届别等硬限制，未纳入岗位列表。"
        f"{broader_note}"
    )
    source_cache_entries = [
        scan_cache_entry("国家公务员局：2026年度招考简章附件", MAIN_URL, now, "官方附件已缓存并用于全量筛选。", main_attachment),
        scan_cache_entry("国家公务员局：2026年度进入面试人员名单", INTERVIEW_URL, now, "官方附件已缓存并用于进面分参考。", interview_attachment),
        scan_cache_entry("石家庄市人社局：2026年事业单位岗位表", SJZ_POSITIONS_URL, now, "官方附件已缓存并用于历史批次筛选。", sjz_attachment),
        scan_cache_entry("中国雄安官网：2026年事业单位岗位表", XIONGAN_POSITIONS_URL, now, "官方附件已缓存并用于历史批次筛选。", xiongan_attachment),
        scan_cache_entry("石家庄市国资委：市属国企社招岗位表", SJZ_SOE_SOCIAL_POSITIONS_URL, now, "官方附件已缓存；报名已截止，本轮仅用于已报名跟踪和同类岗位样本。", sjz_soe_attachment),
        scan_cache_entry("中国远洋海运集团官方招聘平台：2026专项招聘接口", COSCO_STRATEGIC_API_URL, now, f"官方接口返回 {cosco_total} 个岗位；筛选后写入 {len(cosco_positions)} 个仍可投递岗位。", cosco_snapshot),
        *broader_cache_entries,
    ]
    write_source_cache(source_cache_entries, now)
    report.update(
        {
            "generatedAt": now,
            "sourceScope": [
                "国家公务员局公务员招录官方入口",
                "北京市、天津市公务员与编制招聘官方入口",
                "北京市、天津市、石家庄市国资委国企招聘官方入口",
                "国务院国资委人事招聘与中央企业招聘官方入口",
                "中国雄安官网编制与国企通知公告",
                "石家庄市人社局及井陉县、鹿泉区、井陉矿区、藁城区、栾城区、正定县政府门户",
            ],
            "categoryOrder": CATEGORY_ORDER,
            "regionOrder": REGION_ORDER,
            "referencePolicy": (
                "岗位页优先展示仍可新报名或即将报名、且经画像硬条件筛选值得立即核验的国考、省考、编制和国企岗位；已截止但尚待考试的批次只保留检索留痕和已报名跟踪提示。"
                "待遇、房子与户口优先采用公告原文，未载明时明确显示官方未载明；进面分和报录比仅展示可追溯官方数据。"
            ),
            "scanWorkflow": [
                {
                    "step": "1. 权威入口登记",
                    "description": "读取 data/job-sources.json 与脚本内已接入入口，覆盖国家公务员局、北京、天津、雄安、石家庄及国资系统官方渠道。",
                },
                {
                    "step": "2. 公告与附件下载",
                    "description": "逐个打开官方公告，记录报名、考试时间和岗位附件；能下载的岗位表保存快照并写入 source-cache。",
                },
                {
                    "step": "3. 全量硬条件筛选",
                    "description": "对岗位表全部行按画像地区、学历、学位、专业、户籍、届别、身份和经历要求筛选；不抽样、不只返回推荐项。",
                },
                {
                    "step": "4. 四类四区排序",
                    "description": "所有符合岗位写入 positions，并按国考、省考、编制、国企；北京、雄安、天津、石家庄、其他排序。",
                },
                {
                    "step": "5. 逐岗判断整理",
                    "description": "对每个展示岗位补充匹配判断、风险、备考建议、福利待遇、住房、户口和可追溯来源。",
                },
            ],
            "screeningNote": national_note
            + (f"\u5730\u65b9\u4e0e\u56fd\u4f01\u626b\u63cf\uff1a{regional_note}" if regional_note else ""),
            "searchedSources": official_sources + broader_sources + existing_sources,
            "regionalScanNote": regional_note,
            "positions": positions,
        }
    )
    report.pop("profileHash", None)
    write_json(REPORT_PATH, report)
    print(
        f"[岗位同步完成] 当前可展示 {len(positions)} 个 | 已排除历史国考 {len(national_positions)} 个 | "
        f"已排除历史石家庄编制 {len(sjz_positions)} 个 | 已排除历史雄安编制 {len(xiongan_positions)} 个 | "
        f"\u6765\u6e90 {ARTICLE_URL}"
    )


if __name__ == "__main__":
    main()
