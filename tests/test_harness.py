from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("harness_module", ROOT / "scripts" / "harness.py")
assert SPEC and SPEC.loader
HARNESS_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HARNESS_MODULE
SPEC.loader.exec_module(HARNESS_MODULE)
Harness = HARNESS_MODULE.Harness
RunnerResult = HARNESS_MODULE.RunnerResult
command_runner = HARNESS_MODULE.command_runner


class FakeRunner:
    def __init__(self, outcomes=None, mutate=None, crash=None):
        self.outcomes = {key: list(value) for key, value in (outcomes or {}).items()}
        self.mutate = mutate or {}
        self.crash = {key: list(value) for key, value in (crash or {}).items()}
        self.calls = []

    def __call__(self, prompt, environment, output_path, schema_path):
        stage = environment["HARNESS_STAGE_ID"]
        self.calls.append(stage)
        crashes = self.crash.get(stage, [])
        if crashes:
            should_crash = crashes.pop(0)
            if should_crash:
                return RunnerResult(7, "", "simulated failure", None)
        mutation = self.mutate.get(stage)
        if mutation:
            target = Path(environment["HARNESS_ROOT"]) / mutation
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"changed by {stage}\n", encoding="utf-8")
        statuses = self.outcomes.get(stage, [])
        status = statuses.pop(0) if statuses else (
            "all_passed" if stage == "08" else "completed"
        )
        handoff = {
            "schemaVersion": "1.0",
            "handoffId": f"{environment['HARNESS_EXECUTION_ID']}-{stage}-{len(self.calls)}",
            "createdAt": "2026-06-12T00:00:00Z",
            "stageId": stage,
            "status": status,
            "fromAgent": f"stage-{stage}",
            "toAgent": "next",
            "task": {
                "id": "REQ-test",
                "title": "Harness test",
                "objective": "Exercise the state machine",
            },
            "summary": f"{stage} returned {status}",
            "scope": {
                "ownedPaths": ["allowed/**"],
                "excludedPaths": ["forbidden/**"],
            },
            "artifacts": [],
            "checks": [],
            "blockers": [],
            "nextActions": [],
            "notes": [],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(handoff), encoding="utf-8")
        return RunnerResult(0, "{}", "", handoff)


class HarnessTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self._copy_contract()
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "core.autocrlf", "false"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.root, check=True)
        (self.root / ".gitignore").write_text("docs/runs/\n", encoding="utf-8")
        (self.root / "allowed").mkdir()
        (self.root / "allowed" / "base.txt").write_text("base\n", encoding="utf-8")
        (self.root / "forbidden").mkdir()
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "fixture"], cwd=self.root, check=True)
        self.requirement = {
            "id": "REQ-test",
            "title": "Harness test",
            "objective": "Exercise the state machine",
            "ownedPaths": ["allowed/**"],
            "excludedPaths": ["forbidden/**"],
        }

    def tearDown(self):
        self.temp.cleanup()

    def _copy_contract(self):
        for relative in (
            "docs/harnesses/eight-stage/manifest.json",
            "schemas/harness-execution.schema.json",
            "schemas/agent-handoff.schema.json",
        ):
            source = ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        manifest = json.loads((self.root / "docs/harnesses/eight-stage/manifest.json").read_text(encoding="utf-8"))
        for stage in manifest["stages"]:
            prompt = self.root / stage["prompt"]
            prompt.parent.mkdir(parents=True, exist_ok=True)
            prompt.write_text(f"# Stage {stage['id']}\n", encoding="utf-8")

    def init_execution(self, runner, execution_id="run-test"):
        harness = Harness(self.root, runner=runner)
        harness.init(self.requirement, execution_id)
        return harness

    def test_happy_path_persists_artifacts_and_finishes_all_passed(self):
        runner = FakeRunner()
        harness = self.init_execution(runner)

        execution = harness.run("run-test")

        self.assertEqual(execution["status"], "all_passed")
        self.assertEqual(runner.calls, ["01", "02", "03", "04", "05", "06", "08"])
        self.assertFalse(harness.validate("run-test"))
        run_dir = self.root / "docs" / "runs" / "run-test"
        self.assertTrue((run_dir / "requirement.json").is_file())
        self.assertTrue((run_dir / "evidence" / "final-acceptance.json").is_file())
        self.assertEqual(len(list((run_dir / "handoffs").glob("*.json"))), 7)
        self.assertEqual(len(list((run_dir / "evidence").glob("*.json"))), 8)

    def test_validation_failure_enters_repair_and_reruns_checks(self):
        runner = FakeRunner(outcomes={"03": ["has_bugs", "completed"]})
        harness = self.init_execution(runner)

        execution = harness.run("run-test")

        self.assertEqual(execution["status"], "all_passed")
        self.assertEqual(
            runner.calls,
            ["01", "02", "03", "07", "03", "05", "06", "08"],
        )
        self.assertEqual(execution["repairRound"], 1)

    def test_three_failed_repair_rounds_finish_has_bugs(self):
        runner = FakeRunner(
            outcomes={"03": ["has_bugs", "has_bugs", "has_bugs", "has_bugs"]}
        )
        harness = self.init_execution(runner)

        execution = harness.run("run-test")

        self.assertEqual(execution["status"], "has_bugs")
        self.assertEqual(execution["repairRound"], 3)
        self.assertEqual(runner.calls.count("07"), 3)
        self.assertEqual(runner.calls[-1], "08")

    def test_runner_failure_pauses_and_resume_retries_stage(self):
        runner = FakeRunner(crash={"02": [True, False]})
        harness = self.init_execution(runner)

        paused = harness.run("run-test")
        self.assertEqual(paused["status"], "paused")
        self.assertEqual(paused["currentStage"], "02")

        resumed = harness.run("run-test", resume=True)
        self.assertEqual(resumed["status"], "all_passed")
        self.assertEqual(runner.calls[:3], ["01", "02", "02"])
        self.assertEqual(
            [step["attempt"] for step in resumed["steps"] if step["stageId"] == "02"],
            [1, 2],
        )

    def test_non_validation_failure_cannot_be_hidden_by_final_acceptance(self):
        runner = FakeRunner(outcomes={"02": ["has_bugs"]})
        harness = self.init_execution(runner)

        execution = harness.run("run-test")

        self.assertEqual(execution["status"], "has_bugs")
        self.assertEqual(runner.calls[-1], "08")

    def test_unauthorized_write_is_audited_and_repaired(self):
        runner = FakeRunner(mutate={"05": "forbidden/change.txt"})
        harness = self.init_execution(runner)

        execution = harness.run("run-test")

        first_structure_check = next(
            step for step in execution["steps"] if step["stageId"] == "05"
        )
        self.assertEqual(execution["status"], "has_bugs")
        self.assertEqual(first_structure_check["status"], "failed")
        self.assertEqual(
            first_structure_check["writeAudit"]["violations"],
            ["forbidden/change.txt"],
        )
        self.assertIn("07", runner.calls)

    def test_excluded_path_wins_even_if_owned(self):
        self.requirement["ownedPaths"].append("forbidden/**")
        runner = FakeRunner(mutate={"03": "forbidden/change.txt"})
        harness = self.init_execution(runner)

        execution = harness.run("run-test")

        first_validation = next(
            step for step in execution["steps"] if step["stageId"] == "03"
        )
        self.assertEqual(
            first_validation["writeAudit"]["violations"],
            ["forbidden/change.txt"],
        )
        self.assertEqual(execution["status"], "has_bugs")

    def test_command_runner_supports_injected_fake_command(self):
        script = (
            "import json,os,sys,pathlib;"
            "prompt=sys.stdin.read();"
            "p=pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]);"
            "p.parent.mkdir(parents=True,exist_ok=True);"
            "p.write_text(json.dumps({'stage':os.environ['HARNESS_STAGE_ID'],'prompt':prompt}),"
            "encoding='utf-8')"
        )
        runner = command_runner([sys.executable, "-c", script])
        output = self.root / "runner-output.json"

        result = runner(
            "中文 prompt",
            {"HARNESS_ROOT": str(self.root), "HARNESS_STAGE_ID": "03"},
            output,
            self.root / "schemas" / "agent-handoff.schema.json",
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(
            result.handoff,
            {"stage": "03", "prompt": "中文 prompt"},
        )

    def test_validate_reports_tampered_handoff(self):
        runner = FakeRunner(crash={"01": [True]})
        harness = self.init_execution(runner)
        harness.run("run-test")
        bad = self.root / "docs" / "runs" / "run-test" / "handoffs" / "bad.json"
        bad.write_text("{}\n", encoding="utf-8")

        errors = harness.validate("run-test")

        self.assertTrue(any("bad.json" in error for error in errors))

    def test_status_reports_checkpoint(self):
        runner = FakeRunner(crash={"01": [True]})
        harness = self.init_execution(runner)
        harness.run("run-test")

        status = harness.status("run-test")

        self.assertEqual(status["status"], "paused")
        self.assertEqual(status["currentStage"], "01")
        self.assertEqual(status["completedSteps"], 1)


if __name__ == "__main__":
    unittest.main()
