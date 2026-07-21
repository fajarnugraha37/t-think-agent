#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from tthink_runtime import (
    ROOT,
    artifact_name_for,
    build_phase_waivers,
    classify_lane,
    dump_data,
    lane_config,
    lane_rank,
    load_data,
    promotion_state,
    resolve_route,
    resolve_track,
    validate_delegation,
    validate_schema,
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
    work_dir = args.base / args.work_id
    work_dir.mkdir(parents=True, exist_ok=False)
    for directory in ("artifacts", "delegations", "results", "boundary-reports", "evidence"):
        (work_dir / directory).mkdir()

    assessment = classify_lane(
        work_id=args.work_id,
        requested_lane=args.lane,
        declared_signals=args.signal,
        task=args.task,
        approval_ref=args.approval_ref,
    )
    assessment_path, waiver_path = write_lane_artifacts(work_dir, assessment)
    selected = assessment["selected_lane"]
    lane = lane_config(selected)
    repository_root = args.repository_root.resolve()

    data = {
        "schema_version": "2.3.0",
        "work_id": args.work_id,
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
    validate_state(data)
    dump_data(args.file, data)
    print(args.file)
    return 0


def prepare_delegation(args: argparse.Namespace) -> int:
    data = load_data(args.file)
    validate_state(data)
    route = resolve_route(data)

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
        "mode": "human_approved" if args.ignored_file_approval_ref else "deny",
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
        "workspace": {"root": data["repository_root"], "discovery": WORKSPACE_POLICY["discovery_defaults"]},
        "permissions": {
            "workspace_read": "allow",
            "outside_workspace": "deny",
            "source_write": source_write_mode,
            "governance_artifact_write": ".t-think/**",
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
    output = args.out or Path(data["work_directory"]) / "delegations" / f"{invocation}.yaml"
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_data(output, packet)
    print(output)
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
        "--lane", choices=["auto", "quick", "standard", "full"], default="auto"
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
    if args.cmd == "prepare-delegation":
        return prepare_delegation(args)
    raise ValueError(f"unsupported command: {args.cmd}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
