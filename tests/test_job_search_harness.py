from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "job_search_harness_module",
    ROOT / "scripts" / "job_search_harness.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
JobSearchHarness = MODULE.JobSearchHarness
StageResult = MODULE.StageResult


class FakeRunner:
    def __init__(self, outcomes=None):
        self.outcomes = {key: list(value) for key, value in (outcomes or {}).items()}
        self.calls: list[str] = []

    def __call__(self, stage, environment, root):
        stage_id = stage["id"]
        self.calls.append(stage_id)
        outcomes = self.outcomes.get(stage_id, [])
        if outcomes:
            return outcomes.pop(0)
        return StageResult(
            0,
            payload={
                "status": "completed",
                "summary": f"{stage['name']} completed",
            },
        )


class JobSearchHarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.copy_job_search_docs()

    def tearDown(self):
        self.temp.cleanup()

    def copy_job_search_docs(self):
        manifest = self.root / "docs" / "harnesses" / "job-search" / "manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_bytes((ROOT / "docs" / "harnesses" / "job-search" / "manifest.json").read_bytes())
        prompts = self.root / "docs" / "harnesses" / "job-search" / "prompts"
        shutil.copytree(ROOT / "docs" / "harnesses" / "job-search" / "prompts", prompts)

    def harness(self, runner):
        return JobSearchHarness(self.root, runner=runner)

    def create_fallback_artifacts(self):
        index = self.root / "data" / "jobs" / "index.json"
        catalog = self.root / "data" / "jobs" / "catalog" / "positions.jsonl"
        index.parent.mkdir(parents=True, exist_ok=True)
        catalog.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("{}\n", encoding="utf-8")
        catalog.write_text("{}\n", encoding="utf-8")

    def test_four_stage_flow_writes_report_and_collects_sub_agent_outputs(self):
        runner = FakeRunner(
            {
                "01": [
                    StageResult(
                        0,
                        payload={
                            "status": "completed",
                            "summary": "sources checked",
                            "subAgentOutputs": [
                                {
                                    "id": "civil-service-source-finder",
                                    "status": "completed",
                                }
                            ],
                        },
                    )
                ]
            }
        )
        harness = self.harness(runner)
        harness.init("job-test")

        execution = harness.run("job-test")

        self.assertEqual(execution["status"], "all_passed")
        self.assertEqual(runner.calls, ["01", "02", "03", "04"])
        self.assertEqual(
            execution["subAgentOutputs"],
            [{"id": "civil-service-source-finder", "status": "completed"}],
        )
        self.assertFalse(harness.validate("job-test"))
        report = self.root / "docs" / "runs" / "job-search" / "job-test" / "job-search-report.json"
        self.assertTrue(report.is_file())
        self.assertEqual(json.loads(report.read_text(encoding="utf-8"))["status"], "all_passed")

    def test_failed_stage_retries_same_stage_only(self):
        runner = FakeRunner(
            {
                "03": [
                    StageResult(1, stderr="parser failed once"),
                    StageResult(1, stderr="parser failed twice"),
                    StageResult(0, payload={"status": "completed", "summary": "parser recovered"}),
                ]
            }
        )
        harness = self.harness(runner)
        harness.init("job-retry")

        execution = harness.run("job-retry")

        self.assertEqual(execution["status"], "all_passed")
        self.assertEqual(runner.calls, ["01", "02", "03", "03", "03", "04"])
        self.assertEqual(
            [step["attempt"] for step in execution["steps"] if step["stageId"] == "03"],
            [1, 2, 3],
        )

    def test_download_failure_uses_stale_fallback_when_previous_outputs_exist(self):
        self.create_fallback_artifacts()
        runner = FakeRunner({"02": [StageResult(1, stderr="network unavailable")]})
        harness = self.harness(runner)
        harness.init("job-fallback")

        execution = harness.run("job-fallback")

        self.assertEqual(execution["status"], "awaiting_review")
        self.assertEqual(runner.calls, ["01", "02", "03", "04"])
        self.assertEqual(execution["fallbacks"][0]["status"], "stale_fallback")
        report = self.root / "docs" / "runs" / "job-search" / "job-fallback" / "job-search-report.json"
        self.assertEqual(
            json.loads(report.read_text(encoding="utf-8"))["fallbacks"][0]["status"],
            "stale_fallback",
        )

    def test_download_failure_without_fallback_artifacts_finishes_has_bugs(self):
        runner = FakeRunner(
            {
                "02": [
                    StageResult(1, stderr="network unavailable"),
                    StageResult(1, stderr="network unavailable"),
                    StageResult(1, stderr="network unavailable"),
                    StageResult(1, stderr="network unavailable"),
                ]
            }
        )
        harness = self.harness(runner)
        harness.init("job-no-fallback")

        execution = harness.run("job-no-fallback")

        self.assertEqual(execution["status"], "has_bugs")
        self.assertEqual(runner.calls, ["01", "02", "02", "02", "02"])

    def test_parse_stage_can_record_llm_extractor_sub_agent_result(self):
        runner = FakeRunner(
            {
                "03": [
                    StageResult(
                        0,
                        payload={
                            "status": "completed",
                            "summary": "python parser used llm extractor for one sheet",
                            "subAgentOutputs": [
                                {
                                    "id": "llm-table-extractor",
                                    "status": "completed",
                                    "rows": 2,
                                }
                            ],
                        },
                    )
                ]
            }
        )
        harness = self.harness(runner)
        harness.init("job-llm")

        execution = harness.run("job-llm")

        self.assertEqual(execution["status"], "all_passed")
        self.assertIn(
            {"id": "llm-table-extractor", "status": "completed", "rows": 2},
            execution["subAgentOutputs"],
        )


if __name__ == "__main__":
    unittest.main()
