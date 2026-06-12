from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents" / "skills" / "job-filter" / "scripts" / "job_pipeline.py"
SPEC = importlib.util.spec_from_file_location("job_pipeline", SCRIPT)
assert SPEC and SPEC.loader
pipeline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pipeline)


def xlsx_bytes(rows: list[list[str]]) -> bytes:
    shared: list[str] = []
    indexes: dict[str, int] = {}

    def shared_index(value: str) -> int:
        if value not in indexes:
            indexes[value] = len(shared)
            shared.append(value)
        return indexes[value]

    sheet_rows = []
    for row_number, row in enumerate(rows, start=1):
        cells = []
        for column_number, value in enumerate(row, start=1):
            column = ""
            number = column_number
            while number:
                number, remainder = divmod(number - 1, 26)
                column = chr(65 + remainder) + column
            cells.append(
                f'<c r="{column}{row_number}" t="s"><v>{shared_index(value)}</v></c>'
            )
        sheet_rows.append(f'<row r="{row_number}">{"".join(cells)}</row>')

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as handle:
        path = Path(handle.name)
    try:
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                "xl/sharedStrings.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                + "".join(f"<si><t>{value}</t></si>" for value in shared)
                + "</sst>",
            )
            archive.writestr(
                "xl/workbook.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="职位表" sheetId="1" r:id="rId1"/></sheets></workbook>',
            )
            archive.writestr(
                "xl/_rels/workbook.xml.rels",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Target="worksheets/sheet1.xml" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/>'
                "</Relationships>",
            )
            archive.writestr(
                "xl/worksheets/sheet1.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                f'<sheetData>{"".join(sheet_rows)}</sheetData></worksheet>',
            )
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)


class JobPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = {
            "basic": {
                "education": "本科",
                "degree": "学士",
                "major": "计算机科学与技术",
                "majorCode": "080901",
                "freshGraduateStatus": False,
                "politicalStatus": "中共党员",
            },
            "experience": {
                "grassrootsYears": "unknown",
                "veteranOrServiceProgram": "unknown",
                "workYears": "unknown",
            },
            "qualifications": {
                "english": "unknown",
                "professional": "unknown",
            },
        }

    def position(self, **requirements):
        return {
            "requirements": {
                "major": "计算机类",
                "education": "本科及以上",
                "degree": "学士及以上",
                "politicalStatus": "中共党员",
                "grassrootsYears": "不限",
                "serviceProject": "不限",
                "remarks": "",
                **requirements,
            },
            "registration": {
                "opensAt": "2025-10-15T08:00:00+08:00",
                "closesAt": "2025-10-24T18:00:00+08:00",
            },
        }

    def test_screening_passes_known_profile_and_marks_historical(self):
        result = pipeline.evaluate_position(
            self.position(),
            self.profile,
            datetime(2026, 6, 12, tzinfo=timezone.utc),
        )
        self.assertEqual(result["eligibility"], "eligible")
        self.assertEqual(result["timingStatus"], "historical")

    def test_unknown_requirement_is_not_treated_as_eligible(self):
        result = pipeline.evaluate_position(
            self.position(grassrootsYears="二年"),
            self.profile,
            datetime(2025, 10, 20, tzinfo=timezone.utc),
        )
        self.assertEqual(result["eligibility"], "needs_confirmation")
        self.assertIn("grassrootsYears", result["confirmationFields"])
        self.assertEqual(result["timingStatus"], "active")

    def test_non_matching_major_is_excluded(self):
        result = pipeline.evaluate_position(
            self.position(major="法学类"),
            self.profile,
            datetime(2025, 10, 20, tzinfo=timezone.utc),
        )
        self.assertEqual(result["eligibility"], "ineligible")

    def test_non_official_download_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-official"):
            pipeline.download_attachment(
                {
                    "id": "bad",
                    "url": "https://example.com/jobs.xlsx",
                    "path": "data/jobs/sources/bad.xlsx",
                }
            )

    def test_existing_hash_mismatch_triggers_download(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "jobs.xlsx"
            path.write_bytes(b"old")
            attachment = {
                "id": "test",
                "url": "https://scs.gov.cn/jobs.xlsx",
                "path": str(path),
                "sha256": "0" * 64,
            }
            with mock.patch.object(pipeline, "ROOT", Path("/")):
                with mock.patch("urllib.request.urlopen", side_effect=RuntimeError("download attempted")):
                    with self.assertRaisesRegex(RuntimeError, "download attempted"):
                        pipeline.download_attachment(attachment)

    def test_four_exam_adapters_share_normalized_contract(self):
        rows = [
            ["说明"],
            ["招录机关", "职位名称", "职位代码", "工作地点", "专业要求", "学历要求"],
            ["测试单位", "技术岗位", "1001", "河北省石家庄市", "计算机类", "本科及以上"],
        ]
        with tempfile.TemporaryDirectory() as directory:
            original_root = pipeline.ROOT
            pipeline.ROOT = Path(directory)
            try:
                for exam_id in ("national", "beijing", "tianjin", "hebei"):
                    relative = Path("data/jobs/sources") / exam_id / "2026" / "jobs.xlsx"
                    path = pipeline.ROOT / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(xlsx_bytes(rows))
                    source = {
                        "examId": exam_id,
                        "label": exam_id,
                        "cycle": "2026",
                        "region": "河北",
                        "portalUrl": "https://www.gov.cn/",
                        "registration": {
                            "opensAt": "2025-01-01T00:00:00+08:00",
                            "closesAt": "2025-01-02T00:00:00+08:00",
                        },
                        "attachments": [
                            {
                                "id": f"{exam_id}-positions",
                                "kind": "positions",
                                "url": "https://www.gov.cn/jobs.xlsx",
                                "path": relative.as_posix(),
                            }
                        ],
                    }
                    positions, errors = pipeline.parse_source(source)
                    self.assertEqual(errors, [])
                    self.assertEqual(len(positions), 1)
                    self.assertEqual(positions[0]["examId"], exam_id)
                    self.assertEqual(positions[0]["positionCode"], "1001")
            finally:
                pipeline.ROOT = original_root


if __name__ == "__main__":
    unittest.main()
