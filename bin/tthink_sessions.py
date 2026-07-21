from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

WORK_STATUSES = (
    "active",
    "waiting_human",
    "blocked",
    "interrupted",
    "completed",
    "abandoned",
    "archived",
)
UNFINISHED_STATUSES = {"active", "waiting_human", "blocked", "interrupted"}
DEFAULT_LEASE_STALE_SECONDS = 900


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_time(value: str | None) -> datetime:
    if not value:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected object in {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, width=110), encoding="utf-8")


def repository_root_for(state: dict[str, Any]) -> Path:
    return Path(state["repository_root"]).expanduser().resolve()


def work_dir_for(state: dict[str, Any]) -> Path:
    return repository_root_for(state) / state["work_directory"]


def session_dir_for(state: dict[str, Any]) -> Path:
    return work_dir_for(state) / "session"


def session_paths(state: dict[str, Any]) -> dict[str, Path]:
    root = session_dir_for(state)
    return {
        "root": root,
        "resume": root / "resume.yaml",
        "activity": root / "activity.jsonl",
        "lease": root / "lease.yaml",
    }


def append_activity(
    state: dict[str, Any],
    event: str,
    *,
    session_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    paths = session_paths(state)
    paths["root"].mkdir(parents=True, exist_ok=True)
    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "at": now_iso(),
        "work_id": state["work_id"],
        "session_id": session_id or state.get("current_session_id"),
        "event": event,
        "phase": state["current_state"],
    }
    if details:
        record["details"] = details
    with paths["activity"].open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return record


def default_checkpoint(
    state: dict[str, Any],
    *,
    objective: str | None = None,
    next_action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    phase = state["current_state"]
    status = state.get("work_status") or ("completed" if phase == "COMPLETED" else "active")
    return {
        "schema_version": "1.0.0",
        "work_id": state["work_id"],
        "checkpoint_version": 1,
        "checkpointed_at": now_iso(),
        "current_phase": phase,
        "status": status,
        "current_session_id": state.get("current_session_id"),
        "current_objective": objective,
        "last_completed_action": None,
        "next_action": next_action,
        "inflight_delegation": None,
        "completed_tracks": [],
        "remaining_tracks": [],
        "open_findings": [],
        "pending_human_questions": [],
        "approved_write_targets": [],
        "changed_files": [],
        "verification_pending": [],
        "workspace_hygiene": {
            "status": "UNKNOWN",
            "scratch_clean": True,
            "misplaced_artifacts": [],
        },
    }


def load_checkpoint(state: dict[str, Any]) -> dict[str, Any]:
    path = session_paths(state)["resume"]
    if path.is_file():
        return load_yaml(path)
    return default_checkpoint(state)


def write_checkpoint(
    state: dict[str, Any],
    checkpoint: dict[str, Any],
    *,
    validator: Any | None = None,
) -> Path:
    checkpoint = dict(checkpoint)
    checkpoint["schema_version"] = "1.0.0"
    checkpoint["work_id"] = state["work_id"]
    checkpoint["current_phase"] = state["current_state"]
    checkpoint["status"] = state.get("work_status", checkpoint.get("status", "active"))
    checkpoint["current_session_id"] = state.get("current_session_id")
    checkpoint["checkpointed_at"] = now_iso()
    if validator is not None:
        errors = validator(checkpoint, "session-resume.schema.json")
        if errors:
            raise ValueError("Resume checkpoint invalid: " + "; ".join(errors))
    path = session_paths(state)["resume"]
    dump_yaml(path, checkpoint)
    return path


def initialize_session_files(
    state: dict[str, Any],
    *,
    objective: str | None,
    validator: Any | None = None,
) -> None:
    paths = session_paths(state)
    paths["root"].mkdir(parents=True, exist_ok=True)
    checkpoint = default_checkpoint(
        state,
        objective=objective,
        next_action={
            "type": "phase_execution",
            "description": "Complete problem alignment and its required human decision.",
            "phase": "PROBLEM_ALIGNMENT",
        },
    )
    write_checkpoint(state, checkpoint, validator=validator)
    append_activity(
        state,
        "work_item_initialized",
        details={"lane": (state.get("governance_lane") or {}).get("selected")},
    )


def infer_work_status(state: dict[str, Any]) -> str:
    if state.get("current_state") == "COMPLETED":
        return "completed"
    if state.get("work_status") in WORK_STATUSES:
        return state["work_status"]
    if state.get("human_gate_pending"):
        return "waiting_human"
    return "active"


def migrate_session_metadata(
    state: dict[str, Any],
    *,
    state_file: Path,
    validator: Any | None = None,
) -> bool:
    changed = False
    paths = session_paths(state)
    paths["root"].mkdir(parents=True, exist_ok=True)
    defaults = {
        "work_status": infer_work_status(state),
        "last_activity_at": now_iso(),
        "current_session_id": None,
        "checkpoint_path": f"{state['work_directory']}/session/resume.yaml",
        "activity_path": f"{state['work_directory']}/session/activity.jsonl",
        "lease_path": f"{state['work_directory']}/session/lease.yaml",
        "session_generation": 0,
    }
    for key, value in defaults.items():
        if key not in state:
            state[key] = value
            changed = True
    if state.get("schema_version") == "2.3.0":
        state["schema_version"] = "2.4.0"
        changed = True
    if not paths["resume"].exists():
        write_checkpoint(state, default_checkpoint(state), validator=validator)
        changed = True
    if not paths["activity"].exists():
        append_activity(state, "session_metadata_migrated")
        changed = True
    if changed:
        state_file.write_text(yaml.safe_dump(state, sort_keys=False, width=110), encoding="utf-8")
    return changed


def discover_work_items(repository_root: Path) -> list[dict[str, Any]]:
    repository_root = repository_root.expanduser().resolve()
    governance_root = repository_root / ".t-think"
    items: list[dict[str, Any]] = []
    if not governance_root.is_dir():
        return items
    for state_file in sorted(governance_root.glob("*/state.yaml")):
        try:
            state = load_yaml(state_file)
            work_id = str(state.get("work_id") or state_file.parent.name)
            checkpoint_path = state_file.parent / "session/resume.yaml"
            checkpoint = load_yaml(checkpoint_path) if checkpoint_path.is_file() else {}
            work_status = infer_work_status(state)
            last_activity = (
                state.get("last_activity_at")
                or checkpoint.get("checkpointed_at")
                or datetime.fromtimestamp(state_file.stat().st_mtime, tz=timezone.utc).isoformat()
            )
            next_action = checkpoint.get("next_action")
            items.append(
                {
                    "work_id": work_id,
                    "lane": (state.get("governance_lane") or {}).get("selected", "full"),
                    "phase": state.get("current_state", "UNKNOWN"),
                    "status": work_status,
                    "last_activity_at": last_activity,
                    "next_action": next_action,
                    "open_findings": len(checkpoint.get("open_findings", [])),
                    "state_file": state_file.relative_to(repository_root).as_posix(),
                    "valid": True,
                }
            )
        except Exception as error:
            items.append(
                {
                    "work_id": state_file.parent.name,
                    "lane": "unknown",
                    "phase": "UNKNOWN",
                    "status": "blocked",
                    "last_activity_at": datetime.fromtimestamp(
                        state_file.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                    "next_action": {"type": "repair_state", "description": str(error)},
                    "open_findings": 1,
                    "state_file": state_file.relative_to(repository_root).as_posix(),
                    "valid": False,
                }
            )
    items.sort(key=lambda item: parse_time(item["last_activity_at"]), reverse=True)
    return items


def unfinished_work_items(repository_root: Path) -> list[dict[str, Any]]:
    return [item for item in discover_work_items(repository_root) if item["status"] in UNFINISHED_STATUSES]


def entry_payload(repository_root: Path, *, limit: int = 3) -> dict[str, Any]:
    all_unfinished = unfinished_work_items(repository_root)
    recent = all_unfinished[:limit]
    return {
        "schema_version": "1.0.0",
        "question": "What do you want to do?",
        "default_action": "start_new_task",
        "recent_limit": limit,
        "unfinished_count": len(all_unfinished),
        "recent_work_items": recent,
        "show_all": len(all_unfinished) > limit,
        "actions": ["start_new_task", "continue", "show_all", "inspect_existing_work_items"],
        "filesystem_mutation": False,
    }


def format_entry_menu(payload: dict[str, Any]) -> str:
    lines = [payload["question"], "", "● Start a new task"]
    for item in payload["recent_work_items"]:
        suffix = f"{item['lane'].upper()} · {item['phase']} · {item['status']}"
        if item.get("open_findings"):
            suffix += f" · {item['open_findings']} open finding(s)"
        lines.append(f"○ Continue {item['work_id']}")
        lines.append(f"  {suffix}")
    if payload["show_all"]:
        lines.append("○ Show all unfinished work items")
    lines.append("○ Inspect existing work items")
    return "\n".join(lines)


def _lease_is_stale(lease: dict[str, Any], at: datetime | None = None) -> bool:
    now = at or datetime.now(timezone.utc)
    heartbeat = parse_time(lease.get("last_heartbeat_at"))
    stale_after = int(lease.get("stale_after_seconds", DEFAULT_LEASE_STALE_SECONDS))
    return (now - heartbeat).total_seconds() > stale_after


def acquire_lease(
    state: dict[str, Any],
    *,
    session_id: str | None,
    platform: str,
    takeover_stale: bool = False,
    stale_after_seconds: int = DEFAULT_LEASE_STALE_SECONDS,
    validator: Any | None = None,
) -> dict[str, Any]:
    paths = session_paths(state)
    paths["root"].mkdir(parents=True, exist_ok=True)
    requested = session_id or f"S-{uuid.uuid4().hex[:12].upper()}"
    existing: dict[str, Any] | None = None
    if paths["lease"].is_file():
        existing = load_yaml(paths["lease"])
        if existing.get("status") == "active" and existing.get("session_id") != requested:
            stale = _lease_is_stale(existing)
            if not stale:
                raise RuntimeError(
                    f"work item is active in session {existing.get('session_id')}; "
                    "open read-only or retry after the lease becomes stale"
                )
            if not takeover_stale:
                raise RuntimeError(
                    f"previous lease {existing.get('session_id')} is stale; explicit --takeover-stale is required"
                )
    timestamp = now_iso()
    lease = {
        "schema_version": "1.0.0",
        "work_id": state["work_id"],
        "session_id": requested,
        "platform": platform,
        "acquired_at": timestamp,
        "last_heartbeat_at": timestamp,
        "stale_after_seconds": stale_after_seconds,
        "status": "active",
        "replaced_session_id": existing.get("session_id") if existing else None,
    }
    if validator is not None:
        errors = validator(lease, "session-lease.schema.json")
        if errors:
            raise ValueError("Session lease invalid: " + "; ".join(errors))
    dump_yaml(paths["lease"], lease)
    state["current_session_id"] = requested
    state["session_generation"] = int(state.get("session_generation", 0)) + 1
    state["work_status"] = "active"
    state["last_activity_at"] = timestamp
    append_activity(
        state,
        "session_acquired",
        session_id=requested,
        details={"platform": platform, "replaced_session_id": lease["replaced_session_id"]},
    )
    return lease


def heartbeat_lease(
    state: dict[str, Any], *, session_id: str, validator: Any | None = None
) -> dict[str, Any]:
    path = session_paths(state)["lease"]
    if not path.is_file():
        raise RuntimeError("no active lease exists")
    lease = load_yaml(path)
    if lease.get("status") != "active" or lease.get("session_id") != session_id:
        raise RuntimeError("lease is not owned by this session")
    lease["last_heartbeat_at"] = now_iso()
    if validator is not None:
        errors = validator(lease, "session-lease.schema.json")
        if errors:
            raise ValueError("Session lease invalid: " + "; ".join(errors))
    dump_yaml(path, lease)
    state["last_activity_at"] = lease["last_heartbeat_at"]
    return lease


def release_lease(
    state: dict[str, Any], *, session_id: str, reason: str = "session_released"
) -> dict[str, Any]:
    path = session_paths(state)["lease"]
    if not path.is_file():
        raise RuntimeError("no lease exists")
    lease = load_yaml(path)
    if lease.get("session_id") != session_id:
        raise RuntimeError("lease is not owned by this session")
    lease["status"] = "released"
    lease["released_at"] = now_iso()
    dump_yaml(path, lease)
    state["current_session_id"] = None
    if state.get("current_state") != "COMPLETED" and state.get("work_status") == "active":
        state["work_status"] = "interrupted"
    state["last_activity_at"] = lease["released_at"]
    append_activity(state, reason, session_id=session_id)
    return lease



def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_completed_result(
    state: dict[str, Any],
    packet: dict[str, Any],
    result: dict[str, Any],
    *,
    result_path: Path,
    validator: Any | None = None,
) -> list[str]:
    errors: list[str] = []
    repository_root = repository_root_for(state)
    identity = packet.get("identity", {})
    lifecycle = packet.get("lifecycle", {})
    output_contract = packet.get("output_contract", {})
    if validator:
        errors.extend(validator(packet, "delegation-packet.schema.json"))
        errors.extend(validator(result, "subagent-result.schema.json"))
    expected_result = repository_root / str(output_contract.get("result_path", ""))
    if result_path.resolve() != expected_result.resolve():
        errors.append("result path does not match the delegation output contract")
    comparisons = (
        (result.get("invocation_id"), identity.get("invocation_id"), "result invocation_id mismatch"),
        (result.get("agent"), identity.get("target_agent"), "result agent mismatch"),
        (result.get("phase"), lifecycle.get("current_phase"), "result phase mismatch"),
        (result.get("skill"), lifecycle.get("skill"), "result skill mismatch"),
        (result.get("track"), lifecycle.get("track"), "result track mismatch"),
    )
    for actual, expected, message in comparisons:
        if actual != expected:
            errors.append(message)
    if result.get("status") != "COMPLETED":
        errors.append("result status is not COMPLETED")
    validation = result.get("validation") or {}
    if not validation or not all(validation.values()):
        errors.append("result validation flags did not all pass")
    expected_transition = lifecycle.get("expected_next_state")
    if expected_transition and (result.get("recommended_transition") or {}).get("state") != expected_transition:
        errors.append(f"result must recommend {expected_transition}")

    artifact = result.get("artifact") or {}
    artifact_ref = artifact.get("path")
    if artifact_ref:
        artifact_path = repository_root / artifact_ref
        try:
            artifact_path.resolve().relative_to(repository_root)
        except ValueError:
            errors.append("result artifact is outside repository root")
        else:
            if not artifact_path.is_file():
                errors.append("result artifact file is missing")
            elif _sha256(artifact_path) != artifact.get("sha256"):
                errors.append("result artifact digest mismatch")

    declared_boundary_ref = output_contract.get("boundary_report_path")
    reported_boundary = result.get("boundary_report") or {}
    if reported_boundary.get("path") != declared_boundary_ref:
        errors.append("boundary report path does not match delegation output contract")
    if declared_boundary_ref:
        boundary_path = repository_root / declared_boundary_ref
        if not boundary_path.is_file():
            errors.append("boundary report file is missing")
        else:
            try:
                boundary = load_yaml(boundary_path)
            except Exception as error:
                errors.append(f"boundary report cannot be parsed: {error}")
            else:
                if validator:
                    errors.extend(validator(boundary, "boundary-report.schema.json"))
                if boundary.get("invocation_id") != identity.get("invocation_id"):
                    errors.append("boundary invocation_id mismatch")
                if boundary.get("agent") != identity.get("target_agent"):
                    errors.append("boundary agent mismatch")
                if boundary.get("status") != "PASS" or reported_boundary.get("status") != "PASS":
                    errors.append("boundary report did not pass")
                if _sha256(boundary_path) != reported_boundary.get("sha256"):
                    errors.append("boundary report digest mismatch")
    return errors


def scan_delegations(state: dict[str, Any], *, validator: Any | None = None) -> dict[str, Any]:
    work_dir = work_dir_for(state)
    delegations = work_dir / "delegations"
    results = work_dir / "results"
    complete: list[dict[str, Any]] = []
    interrupted: list[dict[str, Any]] = []
    for packet_path in sorted(delegations.glob("*.yaml")) if delegations.is_dir() else []:
        try:
            packet = load_yaml(packet_path)
            invocation_id = packet["identity"]["invocation_id"]
            result_ref = packet["output_contract"]["result_path"]
            result_path = repository_root_for(state) / result_ref
            if result_path.is_file():
                result = load_yaml(result_path)
                errors = validate_completed_result(
                    state,
                    packet,
                    result,
                    result_path=result_path,
                    validator=validator,
                )
                if not errors:
                    complete.append(
                        {
                            "invocation_id": invocation_id,
                            "track": packet.get("lifecycle", {}).get("track"),
                            "phase": packet.get("lifecycle", {}).get("current_phase"),
                            "result": result_ref,
                        }
                    )
                    continue
                reason = "result exists but is not a valid completed subagent result: " + "; ".join(errors)
            else:
                reason = "no result artifact exists"
            interrupted.append(
                {
                    "invocation_id": invocation_id,
                    "track": packet.get("lifecycle", {}).get("track"),
                    "phase": packet.get("lifecycle", {}).get("current_phase"),
                    "packet": packet_path.relative_to(repository_root_for(state)).as_posix(),
                    "reason": reason,
                }
            )
        except Exception as error:
            interrupted.append(
                {
                    "invocation_id": packet_path.stem,
                    "track": None,
                    "phase": "UNKNOWN",
                    "packet": packet_path.relative_to(repository_root_for(state)).as_posix(),
                    "reason": f"invalid delegation packet: {error}",
                }
            )
    return {"completed": complete, "interrupted": interrupted}


def checkpoint_update(
    state: dict[str, Any],
    *,
    validator: Any | None = None,
    status: str | None = None,
    objective: str | None = None,
    last_action: dict[str, Any] | None = None,
    next_action: dict[str, Any] | None = None,
    inflight_delegation: dict[str, Any] | None | object = ...,
    completed_tracks: Iterable[str] | None = None,
    remaining_tracks: Iterable[str] | None = None,
    open_findings: Iterable[str] | None = None,
    pending_questions: Iterable[str] | None = None,
    approved_write_targets: Iterable[str] | None = None,
    changed_files: Iterable[str] | None = None,
    verification_pending: Iterable[str] | None = None,
    workspace_hygiene: dict[str, Any] | None = None,
    event: str = "checkpoint_updated",
    event_details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    checkpoint = load_checkpoint(state)
    checkpoint["checkpoint_version"] = int(checkpoint.get("checkpoint_version", 0)) + 1
    if status is not None:
        if status not in WORK_STATUSES:
            raise ValueError(f"unknown work status: {status}")
        state["work_status"] = status
        checkpoint["status"] = status
    if objective is not None:
        checkpoint["current_objective"] = objective
    if last_action is not None:
        checkpoint["last_completed_action"] = last_action
    if next_action is not None:
        checkpoint["next_action"] = next_action
    if inflight_delegation is not ...:
        checkpoint["inflight_delegation"] = inflight_delegation
    list_updates = {
        "completed_tracks": completed_tracks,
        "remaining_tracks": remaining_tracks,
        "open_findings": open_findings,
        "pending_human_questions": pending_questions,
        "approved_write_targets": approved_write_targets,
        "changed_files": changed_files,
        "verification_pending": verification_pending,
    }
    for key, value in list_updates.items():
        if value is not None:
            checkpoint[key] = list(dict.fromkeys(value))
    if workspace_hygiene is not None:
        checkpoint["workspace_hygiene"] = workspace_hygiene
    timestamp = now_iso()
    state["last_activity_at"] = timestamp
    write_checkpoint(state, checkpoint, validator=validator)
    append_activity(state, event, details=event_details)
    return checkpoint
