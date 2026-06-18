#!/usr/bin/env python3
"""Minimal on-demand Harness for job-search runs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence


TERMINAL_STATUSES = {"all_passed", "awaiting_review", "has_bugs"}
SUCCESS_STATUSES = {"completed", "all_passed"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def normalize_path(value: str) -> str:
    path = value.replace("\\", "/").strip()
    while path.startswith("./"):
        path = path[2:]
    return path.rstrip("/") or "."


def parse_json_line(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


@dataclass
class StageResult:
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    payload: dict[str, Any] | None = None


Runner = Callable[[dict[str, Any], dict[str, str], Path], StageResult]


def command_runner(stage: dict[str, Any], environment: dict[str, str], root: Path) -> StageResult:
    command = list(stage.get("command") or [])
    if not command:
        return StageResult(
            0,
            payload={
                "status": "completed",
                "summary": "No command configured; prompt-guided stage recorded.",
            },
        )

    if command and command[0] == "python":
        command[0] = sys.executable
    process = subprocess.run(
        command,
        cwd=root,
        env={**os.environ, "PYTHONUTF8": "1", **environment},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    payload = parse_json_line(process.stdout)
    return StageResult(process.returncode, process.stdout, process.stderr, payload)


class JobSearchHarness:
    def __init__(
        self,
        root: Path,
        runner: Runner | None = None,
        manifest_path: Path | None = None,
    ) -> None:
        self.root = root.resolve()
        self.manifest_path = (
            manifest_path
            or self.root / "docs" / "harnesses" / "job-search" / "manifest.json"
        )
        self.manifest = read_json(self.manifest_path)
        self.run_root = self.root / self.manifest["runDirectory"]
        self.max_retry_rounds = int(self.manifest.get("maxRetryRounds", 3))
        self.runner = runner or command_runner
        self.stages = list(self.manifest["stages"])
        self.stage_by_id = {stage["id"]: stage for stage in self.stages}
        if len(self.stage_by_id) != len(self.stages):
            raise ValueError("job-search stages must have unique ids")

    def execution_directory(self, execution_id: str) -> Path:
        if not execution_id or any(
            character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for character in execution_id
        ):
            raise ValueError("execution id may contain only letters, numbers, '-' and '_'")
        return self.run_root / execution_id

    def init(self, execution_id: str | None = None) -> dict[str, Any]:
        execution_id = execution_id or (
            "JOB-"
            + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            + "-"
            + uuid.uuid4().hex[:8]
        )
        run_directory = self.execution_directory(execution_id)
        if run_directory.exists():
            raise FileExistsError(f"execution already exists: {execution_id}")
        for directory in ("logs", "prompts", "stage-results"):
            (run_directory / directory).mkdir(parents=True, exist_ok=True)

        now = utc_now()
        execution = {
            "schemaVersion": "1.0",
            "executionId": execution_id,
            "harness": {
                "name": self.manifest["name"],
                "version": self.manifest.get("version", ""),
                "manifest": normalize_path(str(self.manifest_path.relative_to(self.root))),
            },
            "startedAt": now,
            "updatedAt": now,
            "finishedAt": None,
            "status": "initialized",
            "currentStage": self.stages[0]["id"],
            "maxRetryRounds": self.max_retry_rounds,
            "steps": [],
            "fallbacks": [],
            "subAgentOutputs": [],
            "artifacts": [],
            "errors": [],
        }
        self.save_execution(execution)
        return execution

    def load_execution(self, execution_id: str) -> dict[str, Any]:
        path = self.execution_directory(execution_id) / "execution.json"
        if not path.is_file():
            raise FileNotFoundError(f"job-search execution not found: {execution_id}")
        return read_json(path)

    def save_execution(self, execution: dict[str, Any]) -> None:
        execution["updatedAt"] = utc_now()
        write_json(self.execution_directory(execution["executionId"]) / "execution.json", execution)

    def run(self, execution_id: str, resume: bool = False) -> dict[str, Any]:
        execution = self.load_execution(execution_id)
        if execution["status"] in TERMINAL_STATUSES:
            return execution
        if execution["status"] == "paused" and not resume:
            raise RuntimeError("execution is paused; use resume")

        execution["status"] = "running"
        self.save_execution(execution)
        while execution.get("currentStage"):
            stage = self.stage_by_id[execution["currentStage"]]
            outcome = self.execute_stage(execution, stage)
            self.save_execution(execution)
            if execution["status"] in TERMINAL_STATUSES:
                break
            if outcome == "retry":
                continue
            if outcome == "failed":
                self.finish(execution, "has_bugs")
                self.save_execution(execution)
                break
            self.advance(execution, stage["id"])
            if not execution.get("currentStage"):
                final_status = "awaiting_review" if execution["fallbacks"] else "all_passed"
                self.finish(execution, final_status)
                self.save_execution(execution)
                break
            self.save_execution(execution)
        return execution

    def execute_stage(self, execution: dict[str, Any], stage: dict[str, Any]) -> str:
        run_directory = self.execution_directory(execution["executionId"])
        attempt = 1 + sum(
            1 for step in execution["steps"] if step["stageId"] == stage["id"]
        )
        prompt_path = self.write_prompt(execution, stage, attempt)
        started_at = utc_now()
        environment = {
            "JOB_SEARCH_EXECUTION_ID": execution["executionId"],
            "JOB_SEARCH_RUN_DIR": str(run_directory),
            "JOB_SEARCH_STAGE_ID": stage["id"],
            "JOB_SEARCH_STAGE_NAME": stage["name"],
        }
        result = self.runner(stage, environment, self.root)
        payload = result.payload or {}
        if result.exit_code == 0 and not payload:
            payload = {
                "status": "completed",
                "summary": result.stdout.strip() or f"{stage['name']} completed",
            }

        failed = result.exit_code != 0 or payload.get("status") == "has_bugs"
        fallback = None
        if failed and stage.get("fallbackOnFailure") and self.fallback_available():
            failed = False
            fallback = {
                "stageId": stage["id"],
                "stageName": stage["name"],
                "status": self.manifest["fallbackPolicy"]["fallbackStatus"],
                "reason": result.stderr.strip() or result.stdout.strip() or "stage command failed",
                "artifacts": self.manifest["fallbackPolicy"]["requiredArtifacts"],
            }
            execution["fallbacks"].append(fallback)
            payload = {
                "status": "completed",
                "summary": "Used last successful job artifacts after download failure.",
                "fallback": fallback,
            }

        status = "failed" if failed else payload.get("status", "completed")
        sub_agent_outputs = payload.get("subAgentOutputs", [])
        if isinstance(sub_agent_outputs, list):
            execution["subAgentOutputs"].extend(sub_agent_outputs)

        result_path = run_directory / "stage-results" / f"{stage['id']}-{attempt:02d}.json"
        log_path = run_directory / "logs" / f"{stage['id']}-{attempt:02d}.json"
        write_json(
            result_path,
            {
                "stageId": stage["id"],
                "stageName": stage["name"],
                "attempt": attempt,
                "status": status,
                "payload": payload,
                "fallback": fallback,
            },
        )
        write_json(
            log_path,
            {
                "exitCode": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

        step = {
            "stageId": stage["id"],
            "name": stage["name"],
            "agent": stage.get("agent", ""),
            "attempt": attempt,
            "status": status,
            "startedAt": started_at,
            "finishedAt": utc_now(),
            "exitCode": result.exit_code,
            "summary": payload.get("summary", result.stderr.strip()),
            "artifacts": [
                normalize_path(str(prompt_path.relative_to(run_directory))),
                normalize_path(str(result_path.relative_to(run_directory))),
                normalize_path(str(log_path.relative_to(run_directory))),
            ],
        }
        execution["steps"].append(step)
        for artifact in step["artifacts"]:
            if artifact not in execution["artifacts"]:
                execution["artifacts"].append(artifact)

        if failed:
            execution["errors"].append(
                {
                    "stageId": stage["id"],
                    "attempt": attempt,
                    "message": payload.get("summary") or result.stderr.strip() or "stage failed",
                }
            )
            return "retry" if attempt <= self.max_retry_rounds else "failed"
        if status == "awaiting_review":
            self.finish(execution, "awaiting_review")
            return "completed"
        return "completed"

    def write_prompt(self, execution: dict[str, Any], stage: dict[str, Any], attempt: int) -> Path:
        run_directory = self.execution_directory(execution["executionId"])
        source = self.root / self.manifest["agents"][stage["agent"]]["prompt"]
        prompt = source.read_text(encoding="utf-8-sig")
        sub_agents = [
            item for item in self.manifest.get("subAgents", [])
            if item.get("stageId") == stage["id"]
        ]
        text = (
            f"{prompt.rstrip()}\n\n"
            "## Harness Context\n\n"
            f"- executionId: `{execution['executionId']}`\n"
            f"- stageId: `{stage['id']}`\n"
            f"- stageName: `{stage['name']}`\n"
            f"- attempt: `{attempt}`\n"
            f"- runDirectory: `{self.manifest['runDirectory']}/{execution['executionId']}`\n"
            f"- availableSubAgents: `{json.dumps(sub_agents, ensure_ascii=False)}`\n"
        )
        path = run_directory / "prompts" / f"{stage['id']}-{attempt:02d}.md"
        path.write_text(text, encoding="utf-8")
        return path

    def fallback_available(self) -> bool:
        policy = self.manifest.get("fallbackPolicy", {})
        return all((self.root / path).is_file() for path in policy.get("requiredArtifacts", []))

    def advance(self, execution: dict[str, Any], stage_id: str) -> None:
        ids = [stage["id"] for stage in self.stages]
        index = ids.index(stage_id)
        execution["currentStage"] = ids[index + 1] if index + 1 < len(ids) else None

    def finish(self, execution: dict[str, Any], status: str) -> None:
        execution["status"] = status
        execution["currentStage"] = None
        execution["finishedAt"] = utc_now()
        execution["result"] = {
            "exitCode": 0 if status in {"all_passed", "awaiting_review"} else 1,
            "summary": f"job-search execution finished with status {status}",
        }
        self.write_report(execution)

    def write_report(self, execution: dict[str, Any]) -> None:
        run_directory = self.execution_directory(execution["executionId"])
        report_name = self.manifest.get("outputs", {}).get("reportName", "job-search-report.json")
        report_path = run_directory / report_name
        latest_steps = {
            step["stageId"]: {
                "name": step["name"],
                "status": step["status"],
                "attempt": step["attempt"],
                "summary": step.get("summary", ""),
            }
            for step in execution["steps"]
        }
        write_json(
            report_path,
            {
                "schemaVersion": "1.0",
                "executionId": execution["executionId"],
                "generatedAt": utc_now(),
                "status": execution["status"],
                "steps": latest_steps,
                "fallbacks": execution["fallbacks"],
                "subAgentOutputs": execution["subAgentOutputs"],
                "outputs": self.manifest.get("outputs", {}),
                "errors": execution["errors"],
            },
        )
        artifact = normalize_path(str(report_path.relative_to(run_directory)))
        if artifact not in execution["artifacts"]:
            execution["artifacts"].append(artifact)

    def validate(self, execution_id: str) -> list[str]:
        errors: list[str] = []
        execution = self.load_execution(execution_id)
        run_directory = self.execution_directory(execution_id)
        stage_ids = [stage["id"] for stage in self.stages]
        if execution.get("harness", {}).get("name") != self.manifest["name"]:
            errors.append("execution harness name does not match manifest")
        for stage in self.stages:
            prompt = self.root / self.manifest["agents"][stage["agent"]]["prompt"]
            if not prompt.is_file():
                errors.append(f"missing prompt: {normalize_path(str(prompt.relative_to(self.root)))}")
        for step in execution.get("steps", []):
            if step.get("stageId") not in stage_ids:
                errors.append(f"unknown stage in execution: {step.get('stageId')}")
            for artifact in step.get("artifacts", []):
                if not (run_directory / artifact).is_file():
                    errors.append(f"missing artifact: {artifact}")
        if execution["status"] == "all_passed":
            latest = {step["stageId"]: step["status"] for step in execution["steps"]}
            for stage_id in stage_ids:
                if latest.get(stage_id) not in SUCCESS_STATUSES:
                    errors.append(f"stage {stage_id} did not pass")
        report_name = self.manifest.get("outputs", {}).get("reportName", "job-search-report.json")
        if execution["status"] in TERMINAL_STATUSES and not (run_directory / report_name).is_file():
            errors.append(f"missing report: {report_name}")
        return errors

    def status(self, execution_id: str) -> dict[str, Any]:
        execution = self.load_execution(execution_id)
        return {
            "executionId": execution["executionId"],
            "status": execution["status"],
            "currentStage": execution.get("currentStage"),
            "completedSteps": len(execution.get("steps", [])),
            "fallbacks": len(execution.get("fallbacks", [])),
            "updatedAt": execution["updatedAt"],
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(Path(__file__).resolve().parents[1]),
        help="repository root",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--execution-id")

    all_parser = subparsers.add_parser("all")
    all_parser.add_argument("--execution-id")

    for name in ("run", "resume", "status", "validate"):
        command_parser = subparsers.add_parser(name)
        command_parser.add_argument("execution_id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        harness = JobSearchHarness(Path(args.root))
        if args.command == "init":
            execution = harness.init(args.execution_id)
            print(json.dumps(harness.status(execution["executionId"]), ensure_ascii=False))
            return 0
        if args.command == "all":
            execution = harness.init(args.execution_id)
            result = harness.run(execution["executionId"])
            print(json.dumps(harness.status(result["executionId"]), ensure_ascii=False))
            return 0 if result["status"] in {"all_passed", "awaiting_review"} else 1
        if args.command in {"run", "resume"}:
            result = harness.run(args.execution_id, resume=args.command == "resume")
            print(json.dumps(harness.status(args.execution_id), ensure_ascii=False))
            return 0 if result["status"] in {"all_passed", "awaiting_review"} else 1
        if args.command == "status":
            print(json.dumps(harness.status(args.execution_id), ensure_ascii=False))
            return 0
        errors = harness.validate(args.execution_id)
        if errors:
            for error in errors:
                print(f"[ERROR] {error}", file=sys.stderr)
            return 1
        print(f"[OK] job-search execution {args.execution_id} is valid")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
