#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from tthink_paths import find_skill_root, platform_examples, resolve_skill_resource

from tthink_sessions import (
    WORK_STATUSES,
    acquire_lease,
    append_activity,
    checkpoint_update,
    discover_work_items,
    entry_payload,
    format_entry_menu,
    heartbeat_lease,
    initialize_session_files,
    load_checkpoint,
    migrate_session_metadata,
    release_lease,
    scan_delegations,
    session_paths,
    unfinished_work_items,
    validate_completed_result,
)

from tthink_runtime import (
    ROOT,
    artifact_name_for,
    audit_work_directory,
    canonical_work_directory,
    build_phase_waivers,
    classify_lane,
    dump_data,
    lane_config,
    lane_rank,
    load_data,
    intake_questions,
    promotion_state,
    resolve_route,
    resolve_track,
    validate_delegation,
    validate_schema,
    validate_work_id,
    workspace_hygiene_policy,
)

WORK_STATE_SCHEMA = json.loads((ROOT / "schemas/work-state.schema.json").read_text())
WORKSPACE_POLICY = load_data(ROOT / "orchestrator/workspace-policy.yaml")
VALID_SIGNALS = sorted(
    set(load_data(ROOT / "orchestrator/risk-classification-policy.yaml")["hard_triggers"])
    | set(load_data(ROOT / "orchestrator/risk-classification-policy.yaml")["soft_signals"])
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_state(data: dict) -> None:
    errors = sorted(
        Draft202012Validator(WORK_STATE_SCHEMA).iter_errors(data),
        key=lambda error: list(error.path),
    )
    if errors:
        raise ValueError(
            "; ".join(
                f"{'.'.join(map(str, error.path)) or '$'}: {error.message}"
                for error in errors
            )
        )


def state_path(work_dir: Path) -> Path:
    return work_dir / "state.yaml"


def write_lane_artifacts(work_dir: Path, assessment: dict, suffix: str = "") -> tuple[Path, Path]:
    tag = f"-{suffix}" if suffix else ""
    assessment_path = work_dir / "artifacts" / f"lane-assessment{tag}.yaml"
    waiver_path = work_dir / "artifacts" / f"phase-waivers{tag}.yaml"
    assessment_errors = validate_schema(assessment, "lane-assessment.schema.json")
    if assessment_errors:
        raise ValueError("Lane assessment invalid: " + "; ".join(assessment_errors))
    waivers = build_phase_waivers(assessment["work_id"], assessment["selected_lane"])
    waiver_errors = validate_schema(waivers, "phase-waiver.schema.json")
    if waiver_errors:
        raise ValueError("Phase waiver invalid: " + "; ".join(waiver_errors))
    dump_data(assessment_path, assessment)
    dump_data(waiver_path, waivers)
    return assessment_path, waiver_path


def relative_to_repository(path: Path, repository_root: Path) -> str:
    try:
        return path.resolve().relative_to(repository_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def add_common_risk_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--signal",
        action="append",
        default=[],
        choices=VALID_SIGNALS,
        help="Declared deterministic risk signal; may be repeated.",
    )
    parser.add_argument(
        "--task",
        default="",
        help="Optional task statement used only for conservative keyword hints.",
    )


def init_work_item(args: argparse.Namespace) -> int:
    work_id = validate_work_id(args.work_id)
    if args.lane == "auto":
        raise ValueError("init requires an explicit lane: quick, standard, or full")
    if args.base.as_posix().rstrip("/") != ".t-think":
        raise ValueError("the work root is fixed at .t-think; custom --base paths are not allowed")
    repository_root = args.repository_root.resolve()
    work_dir = repository_root / canonical_work_directory(work_id)
    work_dir.mkdir(parents=True, exist_ok=False)
    for directory in ("artifacts", "delegations", "results", "boundary-reports", "evidence", "scratch", "session"):
        (work_dir / directory).mkdir()

    assessment = classify_lane(
        work_id=work_id,
        requested_lane=args.lane,
        declared_signals=args.signal,
        task=args.task,
        approval_ref=args.approval_ref,
    )
    assessment_path, waiver_path = write_lane_artifacts(work_dir, assessment)
    selected = assessment["selected_lane"]
    lane = lane_config(selected)
    data = {
        "schema_version": "2.4.0",
        "work_id": work_id,
        "current_state": "PROBLEM_ALIGNMENT",
        "current_run_id": "RUN-" + uuid.uuid4().hex[:12].upper(),
        "model_profile": args.profile,
        "repository_root": str(repository_root),
        "work_directory": relative_to_repository(work_dir, repository_root),
        "active_skill": "t-problem-alignment",
        "active_agent": "t-think",
        "last_gate": None,
        "last_validator": None,
        "human_gate_pending": True,
        "work_status": "waiting_human",
        "last_activity_at": now_iso(),
        "current_session_id": None,
        "checkpoint_path": f"{relative_to_repository(work_dir, repository_root)}/session/resume.yaml",
        "activity_path": f"{relative_to_repository(work_dir, repository_root)}/session/activity.jsonl",
        "lease_path": f"{relative_to_repository(work_dir, repository_root)}/session/lease.yaml",
        "session_generation": 0,
        "governance_lane": {
            "requested": assessment["requested_lane"],
            "selected": selected,
            "artifact_mode": lane["artifact_mode"],
            "risk_score": assessment["risk_score"],
            "hard_triggers": assessment["hard_triggers"],
            "assessment_path": relative_to_repository(assessment_path, repository_root),
            "waiver_path": relative_to_repository(waiver_path, repository_root),
            "promotion_count": 0,
        },
        "history": [
            {
                "at": now_iso(),
                "event": "INITIALIZED",
                "lane": selected,
                "requested_lane": assessment["requested_lane"],
            }
        ],
    }
    validate_state(data)
    path = state_path(work_dir)
    dump_data(path, data)
    initialize_session_files(data, objective=args.task or None, validator=validate_schema)
    print(path)
    return 0


def classify_command(args: argparse.Namespace) -> int:
    assessment = classify_lane(
        work_id=args.work_id,
        requested_lane=args.lane,
        declared_signals=args.signal,
        task=args.task,
        approval_ref=args.approval_ref,
    )
    errors = validate_schema(assessment, "lane-assessment.schema.json")
    if errors:
        raise ValueError("Lane assessment invalid: " + "; ".join(errors))
    if args.out:
        dump_data(args.out, assessment)
        print(args.out)
    else:
        print(json.dumps(assessment, indent=2))
    return 0


def promote_command(args: argparse.Namespace) -> int:
    data = load_data(args.file)
    validate_state(data)
    governance = data.get("governance_lane")
    if governance is None:
        current_lane = "full"
        raise ValueError("Legacy work items already use the full lane and cannot be promoted")
    current_lane = governance["selected"]
    target_lane = args.lane
    if lane_rank(target_lane) <= lane_rank(current_lane):
        raise ValueError(f"Promotion must move upward: {current_lane} -> {target_lane}")

    original_state = data["current_state"]
    next_state = promotion_state(current_lane, target_lane, original_state)
    work_dir = args.file.parent
    assessment = classify_lane(
        work_id=data["work_id"],
        requested_lane=target_lane,
        declared_signals=args.signal,
        task=args.task,
        previous_lane=current_lane,
        promotion_reason=args.reason,
        approval_ref=args.approval_ref,
    )
    # Promotion is explicit and monotonic even when the classifier recommends a lower lane.
    assessment["selected_lane"] = target_lane
    assessment["selection_source"] = "promotion"
    assessment["forced_promotion"] = True
    assessment["rationale"].append(
        f"Work item was explicitly promoted from {current_lane} to {target_lane}: {args.reason}"
    )
    promotion_number = int(governance.get("promotion_count", 0)) + 1
    assessment_path, waiver_path = write_lane_artifacts(work_dir, assessment, f"promotion-{promotion_number}")

    route_input = dict(data)
    route_input["current_state"] = next_state
    route_input["governance_lane"] = dict(governance, selected=target_lane)
    route = resolve_route(route_input)

    data["current_state"] = next_state
    data["active_skill"] = route["skill"]
    data["active_agent"] = route["agent"]
    data["human_gate_pending"] = True
    data["governance_lane"] = {
        "requested": target_lane,
        "selected": target_lane,
        "artifact_mode": lane_config(target_lane)["artifact_mode"],
        "risk_score": assessment["risk_score"],
        "hard_triggers": assessment["hard_triggers"],
        "assessment_path": relative_to_repository(
            assessment_path, Path(data["repository_root"])
        ),
        "waiver_path": relative_to_repository(waiver_path, Path(data["repository_root"])),
        "promotion_count": promotion_number,
    }
    data["history"].append(
        {
            "at": now_iso(),
            "event": "LANE_PROMOTED",
            "from": current_lane,
            "to": target_lane,
            "reason": args.reason,
            "state_before": original_state,
            "state_after": next_state,
        }
    )
    data["work_status"] = "waiting_human"
    data["last_activity_at"] = now_iso()
    validate_state(data)
    dump_data(args.file, data)
    checkpoint_update(
        data,
        validator=validate_schema,
        status="waiting_human",
        last_action={"type": "lane_promotion", "from": current_lane, "to": target_lane},
        next_action={"type": "phase_execution", "phase": next_state, "description": f"Continue promoted {target_lane} lane at {next_state}."},
        event="lane_promoted",
        event_details={"from": current_lane, "to": target_lane, "reason": args.reason},
    )
    dump_data(args.file, data)
    print(args.file)
    return 0


def prepare_delegation(args: argparse.Namespace) -> int:
    data = load_data(args.file)
    validate_state(data)
    migrate_session_metadata(data, state_file=args.file, validator=validate_schema)
    validate_state(data)
    route = resolve_route(data)
    if data["current_state"] == "RECONCILIATION":
        hygiene = audit_work_directory(data, require_clean=True)
        if hygiene["status"] != "PASS":
            raise ValueError(
                "workspace hygiene blocks reconciliation: " + "; ".join(hygiene["violations"])
            )

    track = None
    if route.get("composite"):
        if not args.track:
            names = ", ".join(item["id"] for item in route["tracks"])
            raise ValueError(f"Composite phase {route['state']} requires --track; choose one of: {names}")
        track = resolve_track(route["state"], route["lane"], args.track)
        target_agent = track["agent"]
        target_skill = track["skill"]
        source_write_mode = track.get("source_write_mode", "deny")
        expected_next_state = route["state"]
    else:
        if args.track:
            raise ValueError(f"Non-composite phase {route['state']} does not accept --track")
        if route["agent"] in (None, "t-think"):
            raise ValueError("Current phase is handled directly by t-think and cannot be delegated")
        target_agent = route["agent"]
        target_skill = route["skill"]
        source_write_mode = route["source_write_mode"]
        expected_next_state = route["success_state"]

    invocation = "INV-" + uuid.uuid4().hex[:12].upper()
    artifact_inputs = []
    for item in args.artifact_input:
        if "=" not in item:
            raise ValueError("--artifact-input must be PATH=SHA256")
        reference, digest = item.rsplit("=", 1)
        artifact_inputs.append({"ref": reference, "sha256": digest})

    ignored = {
        "mode": "human_approved" if args.ignored_file_approval_ref else "allow",
        "human_approval_ref": args.ignored_file_approval_ref,
    }
    work_prefix = Path(data["work_directory"]).as_posix()
    artifact_name = artifact_name_for(route["lane"], data["current_state"])
    if track:
        artifact_path = (
            f"{work_prefix}/artifacts/components/{route['state'].lower().replace('_', '-')}/"
            f"{track['id'].replace('_', '-')}.yaml"
        )
    else:
        artifact_path = f"{work_prefix}/artifacts/{artifact_name}"

    lifecycle = {
        "current_phase": data["current_state"],
        "skill": target_skill,
        "attempt": args.attempt,
        "lane": route["lane"],
        "artifact_mode": route["artifact_mode"],
        "expected_next_state": expected_next_state,
        "track": track["id"] if track else None,
    }
    packet = {
        "schema_version": "2.0.0",
        "identity": {
            "work_id": data["work_id"],
            "run_id": data["current_run_id"],
            "invocation_id": invocation,
            "parent_agent": "t-think",
            "target_agent": target_agent,
        },
        "lifecycle": lifecycle,
        "objective": {"statement": args.objective, "completion_criteria": args.criterion},
        "workspace": {
            "root": data["repository_root"],
            "active_work_directory": work_prefix,
            "discovery": WORKSPACE_POLICY["discovery_defaults"],
        },
        "permissions": {
            "workspace_read": "allow",
            "outside_workspace": "deny",
            "source_write": source_write_mode,
            "governance_artifact_write": f"{work_prefix}/**",
            "approved_write_targets": args.approved_write_target,
            "generated_output_paths": args.generated_output,
            "protected_paths": WORKSPACE_POLICY["protected_paths"],
            "ignored_file_access": ignored,
            "spawn_subagent": "deny",
        },
        "artifact_inputs": artifact_inputs,
        "output_contract": {
            "schema": f"skills/{target_skill}/schemas/output.schema.json",
            "artifact_path": artifact_path,
            "result_path": f"{work_prefix}/results/{invocation}.yaml",
            "boundary_report_path": f"{work_prefix}/boundary-reports/{invocation}.yaml",
        },
        "stop_conditions": [
            "required evidence is unavailable",
            "scope or permission conflict",
            "artifact digest mismatch",
            "a new semantic decision is required",
            "phase completion criteria cannot be satisfied without guessing",
            "the current lane no longer matches the discovered risk or scope",
        ],
    }
    errors = validate_delegation(packet)
    if errors:
        raise ValueError("Delegation invalid: " + "; ".join(errors))
    default_output = Path(data["repository_root"]) / data["work_directory"] / "delegations" / f"{invocation}.yaml"
    output = args.out or default_output
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_data(output, packet)
    remaining = [item["id"] for item in route.get("tracks", [])]
    checkpoint_update(
        data,
        validator=validate_schema,
        status="active",
        objective=args.objective,
        next_action={
            "type": "await_delegation_result",
            "invocation_id": invocation,
            "phase": data["current_state"],
            "track": track["id"] if track else None,
            "description": f"Run {target_agent} with the generated delegation packet and validate its result.",
        },
        inflight_delegation={
            "invocation_id": invocation,
            "agent": target_agent,
            "skill": target_skill,
            "phase": data["current_state"],
            "track": track["id"] if track else None,
            "packet": relative_to_repository(output, Path(data["repository_root"])),
        },
        remaining_tracks=remaining if route.get("composite") else None,
        approved_write_targets=args.approved_write_target,
        event="delegation_started",
        event_details={"invocation_id": invocation, "agent": target_agent, "track": track["id"] if track else None},
    )
    dump_data(args.file, data)
    print(output)
    return 0



def intake_command(args: argparse.Namespace) -> int:
    payload = intake_questions(args.task)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        first, second = payload["questions"]
        print(f"1. {first['question']} Saran: {first['suggestion']}")
        print(f"2. {second['question']}")
    return 0


def audit_workdir_command(args: argparse.Namespace) -> int:
    data = load_data(args.file)
    validate_state(data)
    report = audit_work_directory(data, require_clean=args.require_clean)
    if args.out:
        dump_data(args.out, report)
    print(json.dumps(report, indent=2))
    return 1 if report["status"] == "FAIL" else 0


def cleanup_workdir_command(args: argparse.Namespace) -> int:
    data = load_data(args.file)
    validate_state(data)
    repository_root = Path(data["repository_root"]).resolve()
    work_dir = repository_root / canonical_work_directory(data["work_id"])
    scratch = work_dir / "scratch"
    removed: list[str] = []
    if scratch.is_dir():
        for child in sorted(scratch.iterdir(), key=lambda item: item.as_posix(), reverse=True):
            for file in ([child] if child.is_file() or child.is_symlink() else [p for p in child.rglob("*") if p.is_file() or p.is_symlink()]):
                removed.append(file.relative_to(repository_root).as_posix())
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink(missing_ok=True)
    if args.prune_forbidden_temporary:
        policy = workspace_hygiene_policy()
        temp_exts = {value.lower() for value in policy["forbidden_temporary_extensions_outside_scratch"]}
        candidates = []
        governance_root = repository_root / ".t-think"
        if governance_root.is_dir():
            candidates.extend(child for child in governance_root.iterdir() if child.is_file())
        if work_dir.is_dir():
            candidates.extend(child for child in work_dir.iterdir() if child.is_file() and child.name != "state.yaml")
        for file in candidates:
            if file.suffix.lower() in temp_exts:
                removed.append(file.relative_to(repository_root).as_posix())
                file.unlink(missing_ok=True)
    report = audit_work_directory(data, require_clean=True, removed_files=removed)
    out = args.out or work_dir / "artifacts" / "workspace-hygiene.yaml"
    dump_data(out, report)
    print(json.dumps({"report": out.relative_to(repository_root).as_posix(), **report}, indent=2))
    return 1 if report["status"] == "FAIL" else 0


def paths_command(args: argparse.Namespace) -> int:
    home = args.home.expanduser().resolve() if args.home else None
    platform, root = find_skill_root(args.skill, home, args.platform)
    result: dict[str, object] = {
        "skill": args.skill,
        "platform": platform,
        "skill_root": str(root),
        "resource_index": str((root / "RESOURCE_INDEX.md").resolve()),
    }
    if args.resource:
        resolved_platform, target = resolve_skill_resource(args.skill, args.resource, home, args.platform)
        if resolved_platform != platform:
            raise ValueError("resolver platform mismatch")
        result["resource"] = args.resource
        result["resolved_path"] = str(target)
        result["platform_examples"] = platform_examples(args.skill, args.resource, platform)
        if args.native_only:
            print(target)
            return 0
    print(json.dumps(result, indent=2))
    return 0


def resolve_state_file(repository_root: Path, work_id: str | None = None, file: Path | None = None) -> Path:
    if file is not None:
        return file.expanduser().resolve()
    if not work_id:
        raise ValueError("work_id or --file is required")
    return repository_root.expanduser().resolve() / canonical_work_directory(work_id) / "state.yaml"


def entry_command(args: argparse.Namespace) -> int:
    payload = entry_payload(args.repository_root, limit=args.limit)
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(format_entry_menu(payload))
    return 0


def work_items_command(args: argparse.Namespace) -> int:
    items = discover_work_items(args.repository_root)
    if not args.all:
        items = [item for item in items if item["status"] in {"active", "waiting_human", "blocked", "interrupted"}]
    if args.limit:
        items = items[: args.limit]
    if args.format == "json":
        print(json.dumps({"work_items": items, "count": len(items)}, indent=2))
        return 0
    if not items:
        print("No matching work items.")
        return 0
    print("WORK ID | LANE | PHASE | STATUS | LAST ACTIVITY | NEXT ACTION")
    for item in items:
        action = item.get("next_action") or {}
        description = action.get("description") if isinstance(action, dict) else str(action)
        print(
            f"{item['work_id']} | {item['lane']} | {item['phase']} | {item['status']} | "
            f"{item['last_activity_at']} | {description or '-'}"
        )
    return 0


def _resume_next_action(data: dict, checkpoint: dict, route: dict, scan: dict) -> tuple[dict | None, list[str], list[str], dict | None]:
    current_phase = data["current_state"]
    completed_tracks = {
        item["track"] for item in scan["completed"]
        if item.get("phase") == current_phase and item.get("track")
    }
    completed_tracks.update(checkpoint.get("completed_tracks", []))
    configured_tracks = [item["id"] for item in route.get("tracks", [])]
    remaining_tracks = [track for track in configured_tracks if track not in completed_tracks]
    inflight = checkpoint.get("inflight_delegation")
    interrupted = None
    if inflight:
        invocation = inflight.get("invocation_id")
        completed = next((item for item in scan["completed"] if item["invocation_id"] == invocation), None)
        if completed:
            if completed.get("track"):
                completed_tracks.add(completed["track"])
                remaining_tracks = [track for track in configured_tracks if track not in completed_tracks]
            inflight = None
        else:
            interrupted = next((item for item in scan["interrupted"] if item["invocation_id"] == invocation), None)
    if data["current_state"] == "COMPLETED":
        return None, sorted(completed_tracks), remaining_tracks, interrupted
    if data.get("human_gate_pending"):
        return {
            "type": "human_decision",
            "phase": current_phase,
            "description": f"Obtain the pending human decision for {current_phase} before continuing.",
        }, sorted(completed_tracks), remaining_tracks, interrupted
    if interrupted:
        return {
            "type": "rerun_interrupted_delegation",
            "phase": current_phase,
            "track": interrupted.get("track"),
            "previous_invocation_id": interrupted.get("invocation_id"),
            "description": "Create a replacement delegation with a new invocation ID; the previous session produced no valid completed result.",
        }, sorted(completed_tracks), remaining_tracks, interrupted
    if route.get("composite") and remaining_tracks:
        track = remaining_tracks[0]
        return {
            "type": "delegation",
            "phase": current_phase,
            "track": track,
            "description": f"Prepare and run the required {track} track.",
        }, sorted(completed_tracks), remaining_tracks, interrupted
    if route.get("composite"):
        return {
            "type": "aggregate_composite_phase",
            "phase": current_phase,
            "description": "Validate and aggregate all required composite track results before transitioning.",
        }, sorted(completed_tracks), remaining_tracks, interrupted
    if route.get("agent") in (None, "t-think"):
        return {
            "type": "root_phase_execution",
            "phase": current_phase,
            "description": f"Continue the root-owned {current_phase} phase from its authoritative artifacts.",
        }, sorted(completed_tracks), remaining_tracks, interrupted
    return {
        "type": "delegation",
        "phase": current_phase,
        "agent": route.get("agent"),
        "description": f"Prepare and run {route.get('agent')} for {current_phase}.",
    }, sorted(completed_tracks), remaining_tracks, interrupted


def resume_command(args: argparse.Namespace) -> int:
    state_file = resolve_state_file(args.repository_root, args.work_id, args.file)
    if not state_file.is_file():
        raise ValueError(f"work item state not found: {state_file}")
    data = load_data(state_file)
    validate_state(data)
    migrated = False
    if not args.read_only:
        migrated = migrate_session_metadata(data, state_file=state_file, validator=validate_schema)
        validate_state(data)
    hygiene = audit_work_directory(data, require_clean=False)
    checkpoint = load_checkpoint(data)
    checkpoint_errors = validate_schema(checkpoint, "session-resume.schema.json")
    if checkpoint_errors:
        raise ValueError("Resume checkpoint invalid: " + "; ".join(checkpoint_errors))
    route = resolve_route(data)
    scan = scan_delegations(data, validator=validate_schema)
    next_action, completed_tracks, remaining_tracks, interrupted = _resume_next_action(data, checkpoint, route, scan)

    lease = None
    if not args.read_only and data["current_state"] != "COMPLETED":
        lease = acquire_lease(
            data,
            session_id=args.session_id,
            platform=args.platform,
            takeover_stale=args.takeover_stale,
            stale_after_seconds=args.stale_after_seconds,
            validator=validate_schema,
        )
    status = "completed" if data["current_state"] == "COMPLETED" else (
        "interrupted" if interrupted else ("waiting_human" if data.get("human_gate_pending") else "active")
    )
    if not args.read_only:
        checkpoint_update(
            data,
            validator=validate_schema,
            status=status,
            next_action=next_action,
            inflight_delegation=None if interrupted else checkpoint.get("inflight_delegation"),
            completed_tracks=completed_tracks,
            remaining_tracks=remaining_tracks,
            workspace_hygiene={
                "status": hygiene["status"],
                "scratch_clean": not bool(hygiene.get("scratch_files")),
                "misplaced_artifacts": sorted(
                    set(hygiene.get("root_stray_files", []))
                    | set(hygiene.get("invalid_work_entries", []))
                    | set(hygiene.get("invalid_session_entries", []))
                ),
            },
            event="work_item_resumed",
            event_details={
                "platform": args.platform,
                "migrated": migrated,
                "interrupted_delegation": interrupted,
            },
        )
        dump_data(state_file, data)
    payload = {
        "work_id": data["work_id"],
        "lane": (data.get("governance_lane") or {}).get("selected", "full"),
        "phase": data["current_state"],
        "status": data.get("work_status") or checkpoint.get("status") or ("completed" if data["current_state"] == "COMPLETED" else "active"),
        "session_id": lease.get("session_id") if lease else None,
        "read_only": args.read_only,
        "workspace_hygiene": hygiene["status"],
        "completed_tracks": completed_tracks,
        "remaining_tracks": remaining_tracks,
        "interrupted_delegation": interrupted,
        "next_action": next_action,
    }
    if args.format == "json":
        print(json.dumps(payload, indent=2))
    else:
        print(f"Resuming {payload['work_id']}" if not args.read_only else f"Inspecting {payload['work_id']}")
        print(f"Lane: {payload['lane']}")
        print(f"Phase: {payload['phase']}")
        print(f"Status: {payload['status']}")
        if completed_tracks:
            print("Completed tracks: " + ", ".join(completed_tracks))
        if remaining_tracks:
            print("Remaining tracks: " + ", ".join(remaining_tracks))
        if interrupted:
            print(f"Recovered interruption: {interrupted['invocation_id']} ({interrupted['reason']})")
        print("Next action: " + ((next_action or {}).get("description") or "None"))
    return 0


def checkpoint_command(args: argparse.Namespace) -> int:
    state_file = args.file.expanduser().resolve()
    data = load_data(state_file)
    validate_state(data)
    migrate_session_metadata(data, state_file=state_file, validator=validate_schema)
    last_action = None
    if args.last_action:
        last_action = {"type": args.last_action_type, "description": args.last_action}
    next_action = None
    if args.next_action:
        next_action = {"type": args.next_action_type, "description": args.next_action, "phase": data["current_state"]}
    checkpoint = checkpoint_update(
        data,
        validator=validate_schema,
        status=args.status,
        objective=args.objective,
        last_action=last_action,
        next_action=next_action,
        inflight_delegation=None if args.clear_inflight else ...,
        completed_tracks=args.completed_track,
        remaining_tracks=args.remaining_track,
        open_findings=args.open_finding,
        pending_questions=args.pending_question,
        approved_write_targets=args.approved_write_target,
        changed_files=args.changed_file,
        verification_pending=args.verification_pending,
        event=args.event,
    )
    dump_data(state_file, data)
    print(json.dumps(checkpoint, indent=2))
    return 0


def record_result_command(args: argparse.Namespace) -> int:
    state_file = args.file.expanduser().resolve()
    data = load_data(state_file)
    validate_state(data)
    migrate_session_metadata(data, state_file=state_file, validator=validate_schema)
    result_path = args.result.expanduser().resolve()
    result = load_data(result_path)
    checkpoint = load_checkpoint(data)
    inflight = checkpoint.get("inflight_delegation") or {}
    if inflight and inflight.get("invocation_id") != result.get("invocation_id"):
        raise ValueError("result invocation does not match the current in-flight delegation")
    packet_path = Path(data["repository_root"]) / data["work_directory"] / "delegations" / f"{result.get('invocation_id')}.yaml"
    if not packet_path.is_file():
        raise ValueError(f"delegation packet not found for result: {packet_path}")
    packet = load_data(packet_path)
    errors = validate_completed_result(
        data,
        packet,
        result,
        result_path=result_path,
        validator=validate_schema,
    )
    if errors:
        raise ValueError("Subagent result invalid: " + "; ".join(errors))
    route = resolve_route(data)
    track = result.get("track")
    completed = list(checkpoint.get("completed_tracks", []))
    if result["status"] == "COMPLETED" and track and track not in completed:
        completed.append(track)
    configured = [item["id"] for item in route.get("tracks", [])]
    remaining = [item for item in configured if item not in completed]
    status = "active" if result["status"] == "COMPLETED" else "blocked"
    next_action = (
        {"type": "delegation", "track": remaining[0], "phase": data["current_state"], "description": f"Run remaining {remaining[0]} track."}
        if remaining
        else {"type": "phase_validation", "phase": data["current_state"], "description": "Validate the completed phase outputs and transition legally."}
    )
    updated = checkpoint_update(
        data,
        validator=validate_schema,
        status=status,
        last_action={
            "type": "delegation_result",
            "invocation_id": result["invocation_id"],
            "track": track,
            "status": result["status"],
            "result": relative_to_repository(result_path, Path(data["repository_root"])),
        },
        next_action=next_action,
        inflight_delegation=None,
        completed_tracks=completed,
        remaining_tracks=remaining,
        open_findings=result.get("unresolved_items", []),
        event="delegation_completed" if result["status"] == "COMPLETED" else "delegation_blocked",
        event_details={"invocation_id": result["invocation_id"], "track": track, "status": result["status"]},
    )
    dump_data(state_file, data)
    print(json.dumps(updated, indent=2))
    return 0


def heartbeat_command(args: argparse.Namespace) -> int:
    state_file = args.file.expanduser().resolve()
    data = load_data(state_file)
    validate_state(data)
    lease = heartbeat_lease(data, session_id=args.session_id, validator=validate_schema)
    dump_data(state_file, data)
    print(json.dumps(lease, indent=2))
    return 0


def release_command(args: argparse.Namespace) -> int:
    state_file = args.file.expanduser().resolve()
    data = load_data(state_file)
    validate_state(data)
    lease = release_lease(data, session_id=args.session_id, reason=args.reason)
    checkpoint_update(
        data,
        validator=validate_schema,
        status="completed" if data["current_state"] == "COMPLETED" else "interrupted",
        event="session_checkpointed_and_released",
        event_details={"reason": args.reason},
    )
    dump_data(state_file, data)
    print(json.dumps(lease, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    command = subparsers.add_parser("init")
    command.add_argument("work_id")
    command.add_argument("--base", type=Path, default=Path(".t-think"))
    command.add_argument("--repository-root", type=Path, default=Path("."))
    command.add_argument(
        "--profile",
        choices=["economy", "balanced", "high-assurance"],
        default="economy",
    )
    command.add_argument(
        "--lane", choices=["quick", "standard", "full"], required=True
    )
    command.add_argument("--approval-ref")
    add_common_risk_arguments(command)

    command = subparsers.add_parser("classify")
    command.add_argument("work_id")
    command.add_argument(
        "--lane", choices=["auto", "quick", "standard", "full"], default="auto"
    )
    command.add_argument("--approval-ref")
    command.add_argument("--out", type=Path)
    add_common_risk_arguments(command)

    command = subparsers.add_parser("route")
    command.add_argument("--file", type=Path, required=True)

    command = subparsers.add_parser("validate-state")
    command.add_argument("--file", type=Path, required=True)

    command = subparsers.add_parser("promote")
    command.add_argument("--file", type=Path, required=True)
    command.add_argument("--lane", choices=["standard", "full"], required=True)
    command.add_argument("--reason", required=True)
    command.add_argument("--approval-ref")
    add_common_risk_arguments(command)

    command = subparsers.add_parser("entry", help="Show the root t-think session-entry menu")
    command.add_argument("--repository-root", type=Path, default=Path("."))
    command.add_argument("--limit", type=int, default=3)
    command.add_argument("--format", choices=["text", "json"], default="text")

    command = subparsers.add_parser("work-items", help="Inspect persisted work items read-only")
    command.add_argument("--repository-root", type=Path, default=Path("."))
    command.add_argument("--all", action="store_true", help="Include completed, abandoned, and archived work items")
    command.add_argument("--limit", type=int)
    command.add_argument("--format", choices=["text", "json"], default="text")

    command = subparsers.add_parser("resume", help="Resume a persisted work item with deterministic recovery")
    command.add_argument("work_id", nargs="?")
    command.add_argument("--file", type=Path)
    command.add_argument("--repository-root", type=Path, default=Path("."))
    command.add_argument("--session-id")
    command.add_argument("--platform", choices=["opencode", "codex", "claude", "cursor", "cli", "unknown"], default="cli")
    command.add_argument("--read-only", action="store_true")
    command.add_argument("--takeover-stale", action="store_true")
    command.add_argument("--stale-after-seconds", type=int, default=900)
    command.add_argument("--format", choices=["text", "json"], default="text")

    command = subparsers.add_parser("checkpoint", help="Persist a bounded cross-session checkpoint")
    command.add_argument("--file", type=Path, required=True)
    command.add_argument("--status", choices=list(WORK_STATUSES))
    command.add_argument("--objective")
    command.add_argument("--last-action")
    command.add_argument("--last-action-type", default="bounded_action")
    command.add_argument("--next-action")
    command.add_argument("--next-action-type", default="bounded_action")
    command.add_argument("--clear-inflight", action="store_true")
    command.add_argument("--completed-track", action="append")
    command.add_argument("--remaining-track", action="append")
    command.add_argument("--open-finding", action="append")
    command.add_argument("--pending-question", action="append")
    command.add_argument("--approved-write-target", action="append")
    command.add_argument("--changed-file", action="append")
    command.add_argument("--verification-pending", action="append")
    command.add_argument("--event", default="checkpoint_updated")

    command = subparsers.add_parser("record-result", help="Record a validated subagent result in the resume checkpoint")
    command.add_argument("--file", type=Path, required=True)
    command.add_argument("--result", type=Path, required=True)

    command = subparsers.add_parser("heartbeat", help="Refresh the active work-item session lease")
    command.add_argument("--file", type=Path, required=True)
    command.add_argument("--session-id", required=True)

    command = subparsers.add_parser("release", help="Checkpoint and release the active session lease")
    command.add_argument("--file", type=Path, required=True)
    command.add_argument("--session-id", required=True)
    command.add_argument("--reason", default="session_released")

    command = subparsers.add_parser("intake", help="Generate the mandatory two-question problem-alignment bootstrap")
    command.add_argument("--task", required=True)
    command.add_argument("--format", choices=["text", "json"], default="text")

    command = subparsers.add_parser("audit-workdir", help="Validate active .t-think/<work-id> isolation and scratch hygiene")
    command.add_argument("--file", type=Path, required=True)
    command.add_argument("--require-clean", action="store_true")
    command.add_argument("--out", type=Path)

    command = subparsers.add_parser("cleanup-workdir", help="Remove active scratch files and audit workspace hygiene")
    command.add_argument("--file", type=Path, required=True)
    command.add_argument("--prune-forbidden-temporary", action="store_true")
    command.add_argument("--out", type=Path)

    command = subparsers.add_parser("paths", help="Resolve an installed skill resource with native path semantics")
    command.add_argument("--skill", required=True)
    command.add_argument("--platform", choices=["opencode", "codex", "claude", "cursor"], help="Installed platform whose isolated skill root should be used")
    command.add_argument("--resource", help="Portable '/'-separated path relative to SKILL.md")
    command.add_argument("--home", type=Path, help="Override user home for installation discovery")
    command.add_argument("--native-only", action="store_true", help="Print only the native resolved resource path")

    command = subparsers.add_parser("prepare-delegation")
    command.add_argument("--file", type=Path, required=True)
    command.add_argument("--objective", required=True)
    command.add_argument("--track", help="Required composite-phase track ID")
    command.add_argument("--criterion", action="append", required=True)
    command.add_argument("--attempt", type=int, default=1)
    command.add_argument(
        "--artifact-input", action="append", default=[], help="PATH=SHA256"
    )
    command.add_argument("--approved-write-target", action="append", default=[])
    command.add_argument("--generated-output", action="append", default=[])
    command.add_argument("--ignored-file-approval-ref")
    command.add_argument("--out", type=Path)

    args = parser.parse_args()
    if args.cmd == "init":
        return init_work_item(args)
    if args.cmd == "classify":
        return classify_command(args)
    if args.cmd == "route":
        data = load_data(args.file)
        validate_state(data)
        print(json.dumps(resolve_route(data), indent=2))
        return 0
    if args.cmd == "validate-state":
        data = load_data(args.file)
        validate_state(data)
        print("STATE VALID")
        return 0
    if args.cmd == "promote":
        return promote_command(args)
    if args.cmd == "entry":
        return entry_command(args)
    if args.cmd == "work-items":
        return work_items_command(args)
    if args.cmd == "resume":
        return resume_command(args)
    if args.cmd == "checkpoint":
        return checkpoint_command(args)
    if args.cmd == "record-result":
        return record_result_command(args)
    if args.cmd == "heartbeat":
        return heartbeat_command(args)
    if args.cmd == "release":
        return release_command(args)
    if args.cmd == "intake":
        return intake_command(args)
    if args.cmd == "audit-workdir":
        return audit_workdir_command(args)
    if args.cmd == "cleanup-workdir":
        return cleanup_workdir_command(args)
    if args.cmd == "paths":
        return paths_command(args)
    if args.cmd == "prepare-delegation":
        return prepare_delegation(args)
    raise ValueError(f"unsupported command: {args.cmd}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
