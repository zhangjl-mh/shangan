#!/usr/bin/env python3
"""Executable eight-stage project Harness."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import shlex
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Iterable, Sequence

from jsonschema import Draft202012Validator, FormatChecker


TERMINAL_STATUSES = {"all_passed", "has_bugs", "awaiting_review"}
VALIDATION_STAGES = {"03", "05", "06"}
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


def validate_json(value: Any, schema_path: Path) -> list[str]:
    schema = read_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: "
        f"{error.message}"
        for error in sorted(validator.iter_errors(value), key=lambda item: list(item.path))
    ]


def normalize_path(value: str) -> str:
    path = value.replace("\\", "/").strip()
    while path.startswith("./"):
        path = path[2:]
    return path.rstrip("/") or "."


def matches_path(path: str, pattern: str) -> bool:
    path = normalize_path(path)
    pattern = normalize_path(pattern)
    if pattern in {"", "."}:
        return True
    if any(character in pattern for character in "*?["):
        return fnmatch.fnmatchcase(path, pattern) or fnmatch.fnmatchcase(
            path, pattern.rstrip("/") + "/**"
        )
    return path == pattern or path.startswith(pattern + "/")


def file_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_snapshot(root: Path) -> dict[str, dict[str, str | None]]:
    process = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        message = process.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git status failed: {message}")

    fields = process.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    snapshot: dict[str, dict[str, str | None]] = {}
    index = 0
    while index < len(fields):
        entry = fields[index]
        index += 1
        if not entry:
            continue
        status = entry[:2]
        path = normalize_path(entry[3:])
        if "R" in status or "C" in status:
            if index >= len(fields):
                raise RuntimeError("malformed git status rename entry")
            original_path = normalize_path(fields[index])
            index += 1
            snapshot[original_path] = {
                "status": f"{status}:source",
                "sha256": file_digest(root / Path(original_path)),
            }
        snapshot[path] = {
            "status": status,
            "sha256": file_digest(root / Path(path)),
        }
    return snapshot


def changed_paths(
    before: dict[str, dict[str, str | None]],
    after: dict[str, dict[str, str | None]],
) -> list[str]:
    return sorted(
        path
        for path in set(before) | set(after)
        if before.get(path) != after.get(path)
    )


@dataclass
class RunnerResult:
    exit_code: int
    stdout: str
    stderr: str
    handoff: dict[str, Any] | None


Runner = Callable[[str, dict[str, str], Path, Path], RunnerResult]


def command_runner(command: Sequence[str]) -> Runner:
    def run(
        prompt: str,
        environment: dict[str, str],
        output_path: Path,
        schema_path: Path,
    ) -> RunnerResult:
        working_directory = environment.get(
            "HARNESS_WORKING_DIRECTORY", environment["HARNESS_ROOT"]
        )
        args = [
            *command,
            "--json",
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(output_path),
            "-C",
            working_directory,
            "-",
        ]
        process = subprocess.run(
            args,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=working_directory,
            env={**os.environ, "PYTHONUTF8": "1", **environment},
            capture_output=True,
            check=False,
        )
        handoff = None
        if output_path.is_file():
            try:
                handoff = read_json(output_path)
            except (OSError, ValueError, json.JSONDecodeError):
                handoff = None
        return RunnerResult(
            exit_code=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
            handoff=handoff,
        )

    return run


class Harness:
    def __init__(
        self,
        root: Path,
        runner: Runner | None = None,
        runner_command: Sequence[str] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.manifest_path = self.root / "docs" / "harnesses" / "eight-stage" / "manifest.json"
        self.manifest = read_json(self.manifest_path)
        configured_root = self.root / self.manifest.get("workingDirectory", ".")
        self.working_directory = configured_root.resolve()
        self.run_root = self.root / self.manifest["runDirectory"]
        artifacts = self.manifest["artifacts"]
        self.execution_schema = self.root / artifacts["executionSchema"]
        self.handoff_schema = self.root / artifacts["handoffSchema"]
        self.stages = {stage["id"]: stage for stage in self.manifest["stages"]}
        execution = self.manifest["execution"]
        self.max_repair_rounds = int(execution["maxRepairRounds"])
        self.repair_stage = execution["repairStage"]
        self.repair_rerun_stages = list(execution["repairRerunStages"])
        self.completion_stage = execution["completionStage"]
        if runner is not None:
            self.runner = runner
        else:
            command = list(runner_command or self._runner_from_environment())
            self.runner = command_runner(command)

    @staticmethod
    def _runner_from_environment() -> list[str]:
        configured = os.environ.get("HARNESS_RUNNER")
        if configured:
            return shlex.split(configured)
        return ["codex.cmd" if os.name == "nt" else "codex", "exec"]

    def execution_directory(self, execution_id: str) -> Path:
        if not execution_id or any(
            character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
            for character in execution_id
        ):
            raise ValueError("execution id may contain only letters, numbers, '-' and '_'")
        return self.run_root / execution_id

    def load_execution(self, execution_id: str) -> dict[str, Any]:
        path = self.execution_directory(execution_id) / "execution.json"
        if not path.is_file():
            raise FileNotFoundError(f"execution not found: {execution_id}")
        return read_json(path)

    def save_execution(self, execution: dict[str, Any]) -> None:
        execution["updatedAt"] = utc_now()
        write_json(
            self.execution_directory(execution["executionId"]) / "execution.json",
            execution,
        )

    def init(
        self,
        requirement: dict[str, Any],
        execution_id: str | None = None,
    ) -> dict[str, Any]:
        normalized = self._normalize_requirement(requirement)
        execution_id = execution_id or (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            + "-"
            + uuid.uuid4().hex[:8]
        )
        run_directory = self.execution_directory(execution_id)
        if run_directory.exists():
            raise FileExistsError(f"execution already exists: {execution_id}")
        for name in ("prompts", "logs", "handoffs", "evidence"):
            (run_directory / name).mkdir(parents=True, exist_ok=True)
        write_json(run_directory / "requirement.json", normalized)
        now = utc_now()
        initial_stages = [
            stage["id"]
            for stage in self.manifest["stages"]
            if stage["id"] != self.repair_stage
        ]
        execution = {
            "schemaVersion": "1.0",
            "executionId": execution_id,
            "taskId": normalized["id"],
            "harness": {
                "name": self.manifest["name"],
                "version": self.manifest["version"],
            },
            "startedAt": now,
            "updatedAt": now,
            "finishedAt": None,
            "status": "initialized",
            "workingDirectory": str(self.working_directory),
            "requirement": normalized,
            "currentStage": "01",
            "repairRound": 0,
            "repairMode": False,
            "pendingStages": initial_stages,
            "steps": [],
            "ownershipViolations": [],
            "errors": [],
            "artifacts": ["requirement.json"],
        }
        self.save_execution(execution)
        errors = validate_json(execution, self.execution_schema)
        if errors:
            raise ValueError("invalid initialized execution: " + "; ".join(errors))
        return execution

    def _normalize_requirement(self, value: dict[str, Any]) -> dict[str, Any]:
        requirement_id = str(value.get("id") or value.get("requirementId") or "").strip()
        if not requirement_id:
            raise ValueError("requirement id is required")
        title = str(value.get("title") or "").strip()
        objective = str(value.get("objective") or "").strip()
        owned = value.get("ownedPaths")
        excluded = value.get("excludedPaths", [])
        if not title or not objective:
            raise ValueError("requirement title and objective are required")
        if not isinstance(owned, list) or not owned:
            raise ValueError("requirement ownedPaths must be a non-empty array")
        if not isinstance(excluded, list):
            raise ValueError("requirement excludedPaths must be an array")
        normalized = dict(value)
        normalized.update(
            {
                "id": requirement_id,
                "title": title,
                "objective": objective,
                "ownedPaths": [normalize_path(str(path)) for path in owned],
                "excludedPaths": [normalize_path(str(path)) for path in excluded],
            }
        )
        return normalized

    def run(self, execution_id: str, resume: bool = False) -> dict[str, Any]:
        execution = self.load_execution(execution_id)
        if execution["status"] in TERMINAL_STATUSES:
            return execution
        if execution["status"] == "paused" and not resume:
            raise RuntimeError("execution is paused; use resume")
        execution["status"] = "running"
        self.save_execution(execution)

        while execution.get("currentStage"):
            stage_id = execution["currentStage"]
            outcome = self._execute_stage(execution, stage_id)
            if outcome == "runner_failure":
                execution["status"] = "paused"
                self.save_execution(execution)
                return execution
            self._advance(execution, stage_id, outcome)
            self.save_execution(execution)
            if execution["status"] in TERMINAL_STATUSES:
                break
        return execution

    def _execute_stage(self, execution: dict[str, Any], stage_id: str) -> str:
        stage = self.stages[stage_id]
        run_directory = self.execution_directory(execution["executionId"])
        attempt = 1 + sum(
            1 for step in execution["steps"] if step["stageId"] == stage_id
        )
        stem = f"{stage_id}-{attempt:02d}"
        prompt_path = run_directory / "prompts" / f"{stem}.md"
        log_path = run_directory / "logs" / f"{stem}.json"
        handoff_path = run_directory / "handoffs" / f"{stem}.json"
        audit_path = run_directory / "evidence" / f"{stem}-write-audit.json"
        prompt = self._build_prompt(execution, stage_id)
        prompt_path.write_text(prompt, encoding="utf-8")

        before = git_snapshot(self.root)
        started_at = utc_now()
        environment = {
            "HARNESS_ROOT": str(self.root),
            "HARNESS_WORKING_DIRECTORY": str(self.working_directory),
            "HARNESS_EXECUTION_ID": execution["executionId"],
            "HARNESS_EXECUTION_DIR": str(run_directory),
            "HARNESS_STAGE_ID": stage_id,
            "HARNESS_REPAIR_ROUND": str(execution["repairRound"]),
        }
        try:
            result = self.runner(prompt, environment, handoff_path, self.handoff_schema)
        except Exception as exc:  # runner failures must remain resumable
            result = RunnerResult(1, "", f"{type(exc).__name__}: {exc}", None)
        after = git_snapshot(self.root)
        paths = changed_paths(before, after)
        violations = self._audit_paths(execution["requirement"], paths)
        if violations:
            execution["ownershipViolations"].append(
                {
                    "stageId": stage_id,
                    "attempt": attempt,
                    "paths": violations,
                }
            )
        write_json(
            audit_path,
            {
                "stageId": stage_id,
                "attempt": attempt,
                "changedPaths": paths,
                "violations": violations,
                "status": "failed" if violations else "passed",
            },
        )
        write_json(
            log_path,
            {
                "commandExitCode": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
            },
        )

        handoff_errors: list[str] = []
        if result.handoff is None:
            handoff_errors.append("runner did not produce a JSON handoff")
        else:
            handoff_errors.extend(validate_json(result.handoff, self.handoff_schema))
            if result.handoff.get("task", {}).get("id") != execution["taskId"]:
                handoff_errors.append("handoff task.id does not match execution taskId")
            if result.handoff.get("stageId") != stage_id:
                handoff_errors.append("handoff stageId does not match current stage")
            if not handoff_path.is_file():
                write_json(handoff_path, result.handoff)

        runner_failed = result.exit_code != 0 or bool(handoff_errors)
        status = "failed" if runner_failed or violations else result.handoff["status"]
        if violations and result.handoff is not None:
            result.handoff["status"] = "has_bugs"
            result.handoff.setdefault("blockers", []).extend(
                f"unauthorized write: {path}" for path in violations
            )
            write_json(handoff_path, result.handoff)

        step = {
            "name": stage["name"],
            "stageId": stage_id,
            "attempt": attempt,
            "repairRound": execution["repairRound"],
            "status": status,
            "startedAt": started_at,
            "finishedAt": utc_now(),
            "exitCode": result.exit_code,
            "summary": (
                "; ".join(handoff_errors)
                if handoff_errors
                else (result.handoff or {}).get("summary", result.stderr.strip())
            ),
            "artifacts": [
                str(prompt_path.relative_to(run_directory)).replace("\\", "/"),
                str(log_path.relative_to(run_directory)).replace("\\", "/"),
                str(audit_path.relative_to(run_directory)).replace("\\", "/"),
            ]
            + (
                [str(handoff_path.relative_to(run_directory)).replace("\\", "/")]
                if handoff_path.is_file()
                else []
            ),
            "writeAudit": {
                "changedPaths": paths,
                "violations": violations,
            },
        }
        execution["steps"].append(step)
        execution["artifacts"].extend(
            artifact
            for artifact in step["artifacts"]
            if artifact not in execution["artifacts"]
        )
        if runner_failed:
            execution["errors"].append(
                {
                    "step": stage_id,
                    "message": "stage runner failed",
                    "details": step["summary"],
                }
            )
            return "runner_failure"
        return "failed" if violations or status in {"has_bugs", "awaiting_review"} else "passed"

    def _audit_paths(
        self, requirement: dict[str, Any], paths: Iterable[str]
    ) -> list[str]:
        owned = requirement["ownedPaths"]
        excluded = requirement["excludedPaths"]
        run_prefix = normalize_path(self.manifest["runDirectory"])
        violations = []
        for path in paths:
            if matches_path(path, run_prefix):
                continue
            allowed = any(matches_path(path, pattern) for pattern in owned)
            denied = any(matches_path(path, pattern) for pattern in excluded)
            if denied or not allowed:
                violations.append(path)
        return violations

    def _advance(
        self, execution: dict[str, Any], stage_id: str, outcome: str
    ) -> None:
        if outcome == "failed" and self._last_handoff_status(execution) == "awaiting_review":
            self._finish(execution, "awaiting_review")
            return

        if stage_id == self.completion_stage:
            final_status = self._last_handoff_status(execution)
            if final_status == "all_passed" and not self._unresolved_failures(execution):
                status = "all_passed"
            elif final_status == "awaiting_review":
                status = "awaiting_review"
            else:
                status = "has_bugs"
            self._finish(execution, status)
            self._write_final_evidence(execution)
            return

        if stage_id == self.repair_stage:
            execution["repairMode"] = True
            execution["pendingStages"] = list(self.repair_rerun_stages)
            execution["currentStage"] = execution["pendingStages"][0]
            return

        if stage_id in VALIDATION_STAGES and outcome == "failed":
            if execution["repairRound"] >= self.max_repair_rounds:
                execution["pendingStages"] = [self.completion_stage]
                execution["currentStage"] = self.completion_stage
            else:
                execution["repairRound"] += 1
                execution["pendingStages"] = [self.repair_stage]
                execution["currentStage"] = self.repair_stage
            return

        if execution.get("repairMode") and stage_id in self.repair_rerun_stages:
            pending = execution["pendingStages"]
            if pending and pending[0] == stage_id:
                pending.pop(0)
            if pending:
                execution["currentStage"] = pending[0]
            else:
                execution["repairMode"] = False
                execution["pendingStages"] = [self.completion_stage]
                execution["currentStage"] = self.completion_stage
            return

        pending = execution["pendingStages"]
        if pending and pending[0] == stage_id:
            pending.pop(0)
        execution["currentStage"] = pending[0] if pending else self.completion_stage

    @staticmethod
    def _last_handoff_status(execution: dict[str, Any]) -> str:
        return execution["steps"][-1]["status"]

    def _unresolved_failures(self, execution: dict[str, Any]) -> bool:
        if execution.get("ownershipViolations"):
            return True
        latest: dict[str, str] = {}
        for step in execution["steps"]:
            latest[step["stageId"]] = step["status"]
        if any(
            latest.get(stage) not in SUCCESS_STATUSES for stage in VALIDATION_STAGES
        ):
            return True
        return any(
            stage in latest and latest[stage] not in SUCCESS_STATUSES
            for stage in ("01", "02", "04")
        )

    @staticmethod
    def _finish(execution: dict[str, Any], status: str) -> None:
        execution["status"] = status
        execution["currentStage"] = None
        execution["pendingStages"] = []
        execution["finishedAt"] = utc_now()
        execution["result"] = {
            "exitCode": 0 if status == "all_passed" else 1,
            "summary": f"execution finished with status {status}",
        }

    def _write_final_evidence(self, execution: dict[str, Any]) -> None:
        run_directory = self.execution_directory(execution["executionId"])
        path = run_directory / "evidence" / "final-acceptance.json"
        latest_checks: dict[str, dict[str, Any]] = {}
        for step in execution["steps"]:
            if step["stageId"] in VALIDATION_STAGES:
                latest_checks[step["stageId"]] = {
                    "status": step["status"],
                    "attempt": step["attempt"],
                    "repairRound": step["repairRound"],
                    "artifacts": step["artifacts"],
                }
        write_json(
            path,
            {
                "executionId": execution["executionId"],
                "taskId": execution["taskId"],
                "generatedAt": utc_now(),
                "status": execution["status"],
                "repairRound": execution["repairRound"],
                "checks": latest_checks,
                "ownershipViolations": execution["ownershipViolations"],
            },
        )
        artifact = str(path.relative_to(run_directory)).replace("\\", "/")
        if artifact not in execution["artifacts"]:
            execution["artifacts"].append(artifact)

    def _build_prompt(self, execution: dict[str, Any], stage_id: str) -> str:
        stage = self.stages[stage_id]
        stage_prompt = (self.root / stage["prompt"]).read_text(encoding="utf-8-sig")
        previous = [
            {
                "stageId": step["stageId"],
                "status": step["status"],
                "summary": step.get("summary", ""),
            }
            for step in execution["steps"][-6:]
        ]
        return (
            f"{stage_prompt.rstrip()}\n\n"
            "# Harness runtime context\n\n"
            f"- executionId: `{execution['executionId']}`\n"
            f"- stageId: `{stage_id}`\n"
            f"- repairRound: `{execution['repairRound']}`\n"
            f"- runDirectory: `{self.manifest['runDirectory']}/{execution['executionId']}`\n\n"
            "## Requirement\n\n"
            f"```json\n{json.dumps(execution['requirement'], ensure_ascii=False, indent=2)}\n```\n\n"
            "## Recent stages\n\n"
            f"```json\n{json.dumps(previous, ensure_ascii=False, indent=2)}\n```\n\n"
            "Return exactly one JSON object matching the configured handoff schema. "
            f"`stageId` must be `{stage_id}` and `task.id` must be "
            f"`{execution['taskId']}`.\n"
        )

    def validate(self, execution_id: str) -> list[str]:
        execution = self.load_execution(execution_id)
        run_directory = self.execution_directory(execution_id)
        errors = [
            f"execution.json: {message}"
            for message in validate_json(execution, self.execution_schema)
        ]
        for handoff_path in sorted((run_directory / "handoffs").glob("*.json")):
            try:
                handoff = read_json(handoff_path)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(f"{handoff_path.name}: {exc}")
                continue
            errors.extend(
                f"{handoff_path.name}: {message}"
                for message in validate_json(handoff, self.handoff_schema)
            )
            expected_stage = handoff_path.stem.split("-", 1)[0]
            if handoff.get("stageId") != expected_stage:
                errors.append(
                    f"{handoff_path.name}: stageId does not match artifact name"
                )
            if handoff.get("task", {}).get("id") != execution["taskId"]:
                errors.append(
                    f"{handoff_path.name}: task.id does not match execution taskId"
                )
        for step in execution["steps"]:
            for artifact in step.get("artifacts", []):
                if not (run_directory / artifact).is_file():
                    errors.append(f"missing artifact: {artifact}")
        for artifact in execution.get("artifacts", []):
            if not (run_directory / artifact).is_file():
                errors.append(f"missing execution artifact: {artifact}")
        return errors

    def status(self, execution_id: str) -> dict[str, Any]:
        execution = self.load_execution(execution_id)
        return {
            "executionId": execution["executionId"],
            "taskId": execution["taskId"],
            "status": execution["status"],
            "currentStage": execution.get("currentStage"),
            "repairRound": execution.get("repairRound", 0),
            "completedSteps": len(execution["steps"]),
            "updatedAt": execution["updatedAt"],
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=os.environ.get("HARNESS_ROOT", str(Path(__file__).resolve().parents[1])),
        help="repository root (default: repository containing this script)",
    )
    parser.add_argument(
        "--runner",
        default=None,
        help="runner command; defaults to HARNESS_RUNNER or 'codex.cmd exec'",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="create a persisted execution")
    init_parser.add_argument("--requirement", type=Path, help="requirement JSON file")
    init_parser.add_argument("--execution-id")
    init_parser.add_argument("--id")
    init_parser.add_argument("--title")
    init_parser.add_argument("--objective")
    init_parser.add_argument("--owned-path", action="append", default=[])
    init_parser.add_argument("--excluded-path", action="append", default=[])

    for name in ("run", "resume", "status", "validate"):
        command_parser = subparsers.add_parser(name)
        command_parser.add_argument("execution_id")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    runner_command = (
        shlex.split(args.runner) if args.runner else None
    )
    try:
        harness = Harness(Path(args.root), runner_command=runner_command)
        if args.command == "init":
            if args.requirement:
                requirement = read_json(args.requirement)
            else:
                requirement = {
                    "id": args.id,
                    "title": args.title,
                    "objective": args.objective,
                    "ownedPaths": args.owned_path,
                    "excludedPaths": args.excluded_path,
                }
            result = harness.init(requirement, args.execution_id)
            print(json.dumps(harness.status(result["executionId"]), ensure_ascii=False))
            return 0
        if args.command in {"run", "resume"}:
            result = harness.run(args.execution_id, resume=args.command == "resume")
            print(json.dumps(harness.status(args.execution_id), ensure_ascii=False))
            return 0 if result["status"] == "all_passed" else 1
        if args.command == "status":
            print(json.dumps(harness.status(args.execution_id), ensure_ascii=False))
            return 0
        errors = harness.validate(args.execution_id)
        if errors:
            for error in errors:
                print(f"[ERROR] {error}", file=sys.stderr)
            return 1
        print(f"[OK] execution {args.execution_id} is valid")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
