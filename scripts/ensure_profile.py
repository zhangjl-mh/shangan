"""Create the local candidate profile interactively when it does not exist."""

from __future__ import annotations

import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("GONGKAO_DATA_DIR", ROOT / "data"))
PROFILE_PATH = DATA_DIR / "profile.local.json"

DEFAULT_REGIONS = [
    "北京",
    "天津",
    "雄安新区",
    "石家庄市井陉县",
    "石家庄市鹿泉区",
    "石家庄市井陉矿区",
    "石家庄市藁城区",
    "石家庄市栾城区",
    "石家庄市正定县",
]
DEFAULT_UNIT_TYPES = ["公务员", "事业单位", "国有企业"]
DEFAULT_JOB_TYPES = ["信息化", "综合管理", "技术类"]


def ask(label: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    try:
        answer = input(f"{label}{hint}：").strip()
    except EOFError as error:
        raise SystemExit("未检测到本地画像，且当前终端无法交互输入。请在交互终端重新执行扫描。") from error
    return answer or default


def ask_integer(label: str) -> int | None:
    answer = ask(label)
    if not answer:
        return None
    try:
        return int(answer)
    except ValueError as error:
        raise SystemExit(f"{label}必须填写整数。") from error


def ask_boolean(label: str) -> bool | None:
    answer = ask(f"{label}（是/否，可留空）")
    if not answer:
        return None
    if answer in {"是", "y", "Y", "yes", "Yes", "true", "True"}:
        return True
    if answer in {"否", "n", "N", "no", "No", "false", "False"}:
        return False
    raise SystemExit(f"{label}请填写“是”或“否”。")


def ask_list(label: str, default: list[str] | None = None) -> list[str]:
    default_text = "、".join(default or [])
    answer = ask(f"{label}（用逗号分隔）", default_text)
    normalized = answer.replace("，", ",").replace("、", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def build_profile() -> dict:
    print("尚未找到 data/profile.local.json，请先建立用于岗位筛选的本地画像。")
    print("未填写的资格不会被推定为符合，后续可在网页画像设置中继续修改。\n")
    graduation_year = ask_integer("毕业年份")
    return {
        "basic": {
            "name": ask("姓名（可留空）"),
            "gender": ask("性别"),
            "age": ask_integer("年龄（可留空）"),
            "education": ask("学历", "本科"),
            "degree": ask("学位"),
            "major": ask("专业"),
            "graduationYear": graduation_year,
            "isFreshGraduate": ask_boolean("是否应届"),
            "politicalStatus": ask("政治面貌"),
        },
        "qualification": {
            "englishLevel": ask("英语等级（无则填无）", "无"),
            "computerLevel": ask("计算机等级（可留空）"),
            "certificates": ask_list("证书（可留空）"),
            "grassrootsExperience": ask_boolean("是否有基层工作经历"),
            "householdRegistration": ask("户籍（可留空）"),
            "studentOrigin": ask("生源地（可留空）"),
        },
        "employment": {
            "currentUnitType": ask("当前单位类型（可留空）"),
            "workStatus": ask("工作状态（可留空）"),
        },
        "target": {
            "targetRegions": ask_list("目标地区", DEFAULT_REGIONS),
            "targetUnitTypes": ask_list("目标单位类型", DEFAULT_UNIT_TYPES),
            "targetJobTypes": ask_list("目标岗位类型", DEFAULT_JOB_TYPES),
            "acceptGrassroots": ask_boolean("是否接受基层岗位"),
            "acceptOtherCity": ask_boolean("是否接受异地"),
        },
        "study": {
            "dailyStudyHours": ask_integer("每天学习小时数（可留空）"),
            "shenlunLevel": ask("申论基础（可留空）"),
            "xingceLevel": ask("行测基础（可留空）"),
            "weakModules": ask_list("薄弱模块（可留空）"),
            "examDate": ask("考试日期 YYYY-MM-DD（可留空）"),
        },
    }


def main() -> None:
    if PROFILE_PATH.exists():
        print(f"[画像已就绪] {PROFILE_PATH}")
        return

    profile = build_profile()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n[画像已创建] {PROFILE_PATH}")


if __name__ == "__main__":
    main()
