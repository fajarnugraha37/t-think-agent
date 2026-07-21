#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))
from tthink_runtime import validate_schema
from tthink_sessions import discover_work_items, entry_payload, format_entry_menu

SPEC = importlib.util.spec_from_file_location("t_thinkctl", ROOT / "bin/t-thinkctl.py")
CTL = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(CTL)


def call(function, args: argparse.Namespace, expect: int = 0) -> str:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        code = function(args)
    if code != expect:
        raise RuntimeError(f"exit {code}, expected {expect}: {output.getvalue()}")
    return output.getvalue()


def check(ok: bool, message: str, issues: list[str]) -> None:
    if not ok:
        issues.append(message)


def init_args(repo: Path, work_id: str) -> argparse.Namespace:
    return argparse.Namespace(
        work_id=work_id,
        base=Path(".t-think"),
        repository_root=repo,
        profile="economy",
        lane="standard",
        approval_ref=None,
        signal=[],
        task=f"Implement {work_id}",
    )


def resume_args(repo: Path, work_id: str, **overrides) -> argparse.Namespace:
    values = dict(
        work_id=work_id,
        file=None,
        repository_root=repo,
        session_id=None,
        platform="cli",
        read_only=False,
        takeover_stale=False,
        stale_after_seconds=900,
        format="json",
    )
    values.update(overrides)
    return argparse.Namespace(**values)


def write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=110), encoding="utf-8")


def main() -> int:
    issues: list[str] = []
    passed: list[str] = []
    with tempfile.TemporaryDirectory() as temporary:
        repo = Path(temporary)
        before = set(repo.rglob("*"))
        empty = entry_payload(repo, limit=3)
        empty_menu = format_entry_menu(empty)
        check("● Start a new task" in empty_menu, "empty entry menu lacks start action", issues)
        check(not (repo / ".t-think").exists(), "entry created .t-think", issues)
        check(before == set(repo.rglob("*")), "entry mutated repository", issues)
        passed.append("read-only root session entry")

        work_ids = ["TASK-001", "TASK-002", "TASK-003", "TASK-004", "TASK-DONE"]
        for work_id in work_ids:
            call(CTL.init_work_item, init_args(repo, work_id))
        base_time = datetime(2026, 7, 22, tzinfo=timezone.utc)
        for index, work_id in enumerate(work_ids):
            state_path = repo / ".t-think" / work_id / "state.yaml"
            state = yaml.safe_load(state_path.read_text())
            state["last_activity_at"] = (base_time + timedelta(minutes=index)).isoformat()
            state["human_gate_pending"] = False
            state["work_status"] = "completed" if work_id == "TASK-DONE" else "interrupted"
            if work_id == "TASK-DONE":
                state["current_state"] = "COMPLETED"
            write_yaml(state_path, state)
            checkpoint_path = state_path.parent / "session/resume.yaml"
            checkpoint = yaml.safe_load(checkpoint_path.read_text())
            checkpoint["checkpointed_at"] = state["last_activity_at"]
            checkpoint["status"] = state["work_status"]
            checkpoint["current_phase"] = state["current_state"]
            checkpoint["next_action"] = {"type": "resume_test", "description": f"Continue {work_id}"}
            write_yaml(checkpoint_path, checkpoint)

        payload = entry_payload(repo, limit=3)
        recent_ids = [item["work_id"] for item in payload["recent_work_items"]]
        check(recent_ids == ["TASK-004", "TASK-003", "TASK-002"], f"recent order mismatch: {recent_ids}", issues)
        check(payload["show_all"] is True, "Show all missing with four unfinished items", issues)
        check(payload["unfinished_count"] == 4, "completed item included as unfinished", issues)
        menu = format_entry_menu(payload)
        check(menu.count("○ Continue") == 3, "menu does not cap recent items at three", issues)
        check("○ Show all unfinished work items" in menu, "menu lacks Show all", issues)
        passed.append("three newest unfinished items and Show all")

        items = discover_work_items(repo)
        check(len(items) == 5, "catalogue did not discover every work item", issues)
        check(sum(item["status"] != "completed" for item in items) == 4, "unfinished catalogue count mismatch", issues)
        passed.append("filesystem-derived work-item catalogue")

        target = repo / ".t-think/TASK-004/state.yaml"
        resumed = json.loads(call(CTL.resume_command, resume_args(repo, "TASK-004", session_id="SESSION-A", platform="opencode")))
        check(resumed["session_id"] == "SESSION-A", "resume did not acquire requested lease", issues)
        try:
            call(CTL.resume_command, resume_args(repo, "TASK-004", session_id="SESSION-B", platform="codex"))
            issues.append("concurrent lease was not blocked")
        except RuntimeError as error:
            check("active in session SESSION-A" in str(error), "wrong concurrent lease error", issues)
        state_before_readonly = target.read_bytes()
        activity_before_readonly = (target.parent / "session/activity.jsonl").read_bytes()
        readonly = json.loads(call(CTL.resume_command, resume_args(repo, "TASK-004", read_only=True)))
        check(readonly["read_only"] is True and readonly["session_id"] is None, "read-only resume acquired lease", issues)
        check(target.read_bytes() == state_before_readonly, "read-only resume modified state", issues)
        check((target.parent / "session/activity.jsonl").read_bytes() == activity_before_readonly, "read-only resume modified journal", issues)
        call(CTL.heartbeat_command, argparse.Namespace(file=target, session_id="SESSION-A"))
        call(CTL.release_command, argparse.Namespace(file=target, session_id="SESSION-A", reason="test_end"))
        passed.append("lease exclusion, heartbeat, read-only inspection, and release")

        # Legacy work items remain read-only until a mutating resume performs migration.
        legacy = repo / ".t-think/TASK-001/state.yaml"
        legacy_state = yaml.safe_load(legacy.read_text())
        legacy_state["schema_version"] = "2.3.0"
        for key in ("work_status", "last_activity_at", "current_session_id", "checkpoint_path", "activity_path", "lease_path", "session_generation"):
            legacy_state.pop(key, None)
        write_yaml(legacy, legacy_state)
        import shutil
        shutil.rmtree(legacy.parent / "session")
        legacy_before = legacy.read_bytes()
        readonly_legacy = json.loads(call(CTL.resume_command, resume_args(repo, "TASK-001", read_only=True)))
        check(readonly_legacy["read_only"] is True, "legacy read-only inspection failed", issues)
        check(legacy.read_bytes() == legacy_before and not (legacy.parent / "session").exists(), "read-only legacy inspection performed migration", issues)
        migrated = json.loads(call(CTL.resume_command, resume_args(repo, "TASK-001", session_id="LEGACY-SESSION")))
        migrated_state = yaml.safe_load(legacy.read_text())
        check(migrated_state["schema_version"] == "2.4.0", "mutating resume did not migrate legacy schema", issues)
        check((legacy.parent / "session/resume.yaml").is_file(), "legacy migration did not create checkpoint", issues)
        call(CTL.release_command, argparse.Namespace(file=legacy, session_id="LEGACY-SESSION", reason="legacy_test_end"))
        passed.append("write-free legacy inspection and mutating migration")

        state = yaml.safe_load(target.read_text())
        state.update(
            current_state="IMPLEMENTATION_REVIEW",
            active_skill="t-implementation-review",
            active_agent="t-think",
            human_gate_pending=False,
            work_status="active",
        )
        write_yaml(target, state)
        delegation_output = call(
            CTL.prepare_delegation,
            argparse.Namespace(
                file=target,
                objective="Review implementation correctness independently",
                track="technical_review",
                criterion=["Find material correctness defects"],
                attempt=1,
                artifact_input=[],
                approved_write_target=[],
                generated_output=[],
                ignored_file_approval_ref=None,
                out=None,
            ),
        ).strip()
        packet = yaml.safe_load(Path(delegation_output).read_text())
        invocation = packet["identity"]["invocation_id"]
        recovered = json.loads(call(CTL.resume_command, resume_args(repo, "TASK-004", session_id="SESSION-C", platform="claude")))
        check(recovered["status"] == "interrupted", "orphaned delegation did not mark interrupted", issues)
        check(
            recovered["interrupted_delegation"] and recovered["interrupted_delegation"]["invocation_id"] == invocation,
            "orphaned invocation not identified",
            issues,
        )
        check(recovered["next_action"]["type"] == "rerun_interrupted_delegation", "replacement delegation not required", issues)
        passed.append("orphaned delegation recovery without false completion")

        # A valid completed result clears the in-flight delegation and advances track bookkeeping.
        result_path = repo / packet["output_contract"]["result_path"]
        artifact_path = repo / packet["output_contract"]["artifact_path"]
        boundary_path = repo / packet["output_contract"]["boundary_report_path"]
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        boundary_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("status: PASS\n", encoding="utf-8")
        boundary = {
            "schema_version": "1.0.0",
            "invocation_id": invocation,
            "agent": "t-reviewer",
            "status": "PASS",
            "source_changes": [],
            "governance_artifact_changes": [artifact_path.relative_to(repo).as_posix()],
            "generated_output_changes": [],
            "outside_workspace_access": [],
            "ignored_file_access": [],
            "violations": [],
        }
        write_yaml(boundary_path, boundary)
        import hashlib
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        result = {
            "schema_version": "2.0.0",
            "invocation_id": invocation,
            "agent": "t-reviewer",
            "phase": "IMPLEMENTATION_REVIEW",
            "skill": "t-technical-review",
            "status": "COMPLETED",
            "artifact": {"path": artifact_path.relative_to(repo).as_posix(), "sha256": digest(artifact_path)},
            "claim_counts": {"FACT": 1, "INFERENCE": 0, "ASSUMPTION": 0, "UNKNOWN": 0, "CONFLICT": 0},
            "evidence": {"referenced": 1, "missing": 0},
            "unresolved_items": [],
            "recommended_transition": {"state": "IMPLEMENTATION_REVIEW", "gate": None},
            "validation": {"schema_passed": True, "semantic_checks_passed": True},
            "boundary_report": {"path": boundary_path.relative_to(repo).as_posix(), "sha256": digest(boundary_path), "status": "PASS"},
            "track": "technical_review",
        }
        write_yaml(result_path, result)
        recorded = json.loads(call(CTL.record_result_command, argparse.Namespace(file=target, result=result_path)))
        check("technical_review" in recorded["completed_tracks"], "record-result did not complete the track", issues)
        check(recorded["inflight_delegation"] is None, "record-result did not clear in-flight delegation", issues)
        check("self_review" in recorded["remaining_tracks"], "record-result lost remaining tracks", issues)
        passed.append("validated result recording and remaining-track reconstruction")

        # Stale lease takeover is explicit, never automatic.
        lease_path = target.parent / "session/lease.yaml"
        lease = yaml.safe_load(lease_path.read_text())
        lease["last_heartbeat_at"] = "2000-01-01T00:00:00+00:00"
        lease["status"] = "active"
        write_yaml(lease_path, lease)
        try:
            call(CTL.resume_command, resume_args(repo, "TASK-004", session_id="SESSION-D"))
            issues.append("stale lease was taken over without explicit flag")
        except RuntimeError as error:
            check("explicit --takeover-stale is required" in str(error), "wrong stale lease error", issues)
        takeover = json.loads(call(CTL.resume_command, resume_args(repo, "TASK-004", session_id="SESSION-D", takeover_stale=True)))
        check(takeover["session_id"] == "SESSION-D", "explicit stale takeover failed", issues)
        passed.append("explicit-only stale lease takeover")

        checkpoint = yaml.safe_load((target.parent / "session/resume.yaml").read_text())
        lease = yaml.safe_load((target.parent / "session/lease.yaml").read_text())
        check(not validate_schema(checkpoint, "session-resume.schema.json"), "resume checkpoint schema invalid", issues)
        check(not validate_schema(lease, "session-lease.schema.json"), "lease schema invalid", issues)
        events = [json.loads(line) for line in (target.parent / "session/activity.jsonl").read_text().splitlines() if line]
        for event in events:
            check(not validate_schema(event, "session-activity-event.schema.json"), f"activity event invalid: {event}", issues)
        check(any(event["event"] == "work_item_resumed" for event in events), "resume not journaled", issues)
        passed.append("validated checkpoint, lease, and append-only journal")

    report = {"status": "FAIL" if issues else "PASS", "passed_contracts": passed, "issues": issues}
    (ROOT / "reports/session-continuity-contract-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
