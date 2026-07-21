from __future__ import annotations

import fnmatch
import hashlib
import json
from copy import deepcopy
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def load_data(path: Path) -> Any:
    text = path.read_text()
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def dump_data(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps(data, indent=2) + "\n")
    else:
        path.write_text(yaml.safe_dump(data, sort_keys=False, width=110))


def validate_schema(data: Any, schema_name: str) -> list[str]:
    schema = json.loads((ROOT / "schemas" / schema_name).read_text())
    return [
        f"{'.'.join(map(str, error.path)) or '$'}: {error.message}"
        for error in sorted(
            Draft202012Validator(schema).iter_errors(data),
            key=lambda error: list(error.path),
        )
    ]


def registry() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    phases = yaml.safe_load((ROOT / "orchestrator/phase-registry.yaml").read_text())
    agents = yaml.safe_load((ROOT / "orchestrator/agent-registry.yaml").read_text())
    return (
        {phase["state"]: phase for phase in phases["phases"]},
        {agent["name"]: agent for agent in agents["agents"]},
    )


def lane_registry() -> dict[str, Any]:
    return yaml.safe_load((ROOT / "orchestrator/lane-registry.yaml").read_text())


def risk_policy() -> dict[str, Any]:
    return yaml.safe_load((ROOT / "orchestrator/risk-classification-policy.yaml").read_text())


def artifact_policy() -> dict[str, Any]:
    return yaml.safe_load((ROOT / "orchestrator/artifact-mode-policy.yaml").read_text())


def composite_policy() -> dict[str, Any]:
    return yaml.safe_load((ROOT / "orchestrator/composite-phase-policy.yaml").read_text())


def composite_phase_config(phase_name: str) -> dict[str, Any] | None:
    return composite_policy().get("phases", {}).get(phase_name)


def composite_tracks(phase_name: str, lane: str) -> list[dict[str, Any]]:
    config = composite_phase_config(phase_name)
    if not config:
        return []
    return [deepcopy(track) for track in config.get("tracks", []) if lane in track.get("lanes", [])]


def resolve_track(phase_name: str, lane: str, track_id: str) -> dict[str, Any]:
    matches = [track for track in composite_tracks(phase_name, lane) if track.get("id") == track_id]
    if not matches:
        valid = [track.get("id") for track in composite_tracks(phase_name, lane)]
        raise ValueError(
            f"unknown or inactive track {track_id!r} for {phase_name} in lane {lane}; "
            f"expected one of: {', '.join(valid) or 'none'}"
        )
    return matches[0]


def norm(path: str) -> str:
    value = path.replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    return str(PurePosixPath(value))


def is_outside(path: str) -> bool:
    candidate = PurePosixPath(norm(path))
    return candidate.is_absolute() or ".." in candidate.parts


def matches(path: str, patterns: list[str]) -> bool:
    candidate = norm(path)
    return any(
        fnmatch.fnmatchcase(candidate, pattern)
        or fnmatch.fnmatchcase("/" + candidate, pattern)
        for pattern in patterns
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def selected_lane(state: dict[str, Any]) -> str:
    """Return full for pre-lane work states so existing work items remain valid."""
    governance = state.get("governance_lane") or {}
    return governance.get("selected", lane_registry().get("legacy_state_default", "full"))


def lane_config(lane: str) -> dict[str, Any]:
    lanes = lane_registry()["lanes"]
    if lane not in lanes:
        raise ValueError(f"unknown governance lane: {lane}")
    return lanes[lane]


def phase_path(lane: str) -> list[str]:
    return list(lane_config(lane)["phase_path"])


def next_state_for(lane: str, current_state: str) -> str | None:
    path = phase_path(lane)
    if current_state not in path:
        raise ValueError(f"state {current_state} is not part of lane {lane}")
    index = path.index(current_state)
    if index + 1 >= len(path):
        return None
    return path[index + 1]


def resolved_phase(state_name: str, lane: str) -> dict[str, Any]:
    phases, _ = registry()
    if state_name not in phases:
        raise ValueError(f"unknown lifecycle state: {state_name}")
    if state_name not in phase_path(lane):
        raise ValueError(f"state {state_name} is waived by lane {lane}")
    phase = deepcopy(phases[state_name])
    override = lane_config(lane).get("phase_overrides", {}).get(state_name, {})
    phase.update(override)
    phase["success_state"] = next_state_for(lane, state_name)
    return phase


def human_gate_requirements(lane: str, current_state: str) -> dict[str, bool]:
    config = lane_config(lane)
    return {
        "before_phase": current_state in config.get("human_gates_before", []),
        "after_phase": current_state in config.get("human_gates_after", []),
    }


def resolve_route(state: dict[str, Any]) -> dict[str, Any]:
    lane = selected_lane(state)
    current_state = state["current_state"]
    if current_state == "COMPLETED":
        return {
            "state": current_state,
            "skill": None,
            "agent": None,
            "status": "terminal",
            "lane": lane,
            "artifact_mode": lane_config(lane)["artifact_mode"],
            "model_profile": state["model_profile"],
            "composite": False,
            "tracks": [],
        }
    phase = resolved_phase(current_state, lane)
    gates = human_gate_requirements(lane, current_state)
    agent = phase["agent"]
    is_composite = bool(phase.get("composite", False))
    tracks = composite_tracks(current_state, lane) if is_composite else []
    return {
        "state": current_state,
        "skill": phase["skill"],
        "skill_path": str(ROOT / phase["path"]),
        "agent": agent,
        "agent_manifest": None if agent == "t-think" else str(ROOT / "agents" / agent / "agent.yaml"),
        "success_state": phase["success_state"],
        "repository_mutation": phase["repository_mutation"],
        "source_write_mode": phase["source_write_mode"],
        "context": phase["context"],
        "model_profile": state["model_profile"],
        "lane": lane,
        "artifact_mode": lane_config(lane)["artifact_mode"],
        "human_gate_before": gates["before_phase"],
        "human_gate_after": gates["after_phase"],
        "composite": is_composite,
        "tracks": [
            {
                "id": track["id"],
                "agent": track["agent"],
                "skill": track["skill"],
                "required": bool(track.get("required", True)),
                "fresh_context": bool(track.get("fresh_context", True)),
                "source_write_mode": track.get("source_write_mode", "deny"),
            }
            for track in tracks
        ],
    }


def artifact_name_for(lane: str, state_name: str) -> str:
    mode = lane_config(lane)["artifact_mode"]
    overrides = artifact_policy()["modes"][mode].get("path_overrides", {})
    return overrides.get(state_name, state_name.lower().replace("_", "-") + ".yaml")


def _keyword_signals(task: str, policy: dict[str, Any]) -> set[str]:
    lower = task.lower()
    inferred: set[str] = set()
    for signal, keywords in policy.get("keyword_hints", {}).items():
        if any(keyword.lower() in lower for keyword in keywords):
            inferred.add(signal)
    return inferred


def _normalize_signal_names(signals: Iterable[str], policy: dict[str, Any]) -> set[str]:
    valid = set(policy.get("hard_triggers", {})) | set(policy.get("soft_signals", {}))
    normalized = {signal.strip() for signal in signals if signal and signal.strip()}
    unknown = sorted(normalized - valid)
    if unknown:
        raise ValueError(f"unknown risk signal(s): {', '.join(unknown)}")
    return normalized


def classify_lane(
    *,
    work_id: str,
    requested_lane: str = "auto",
    declared_signals: Iterable[str] = (),
    task: str = "",
    previous_lane: str | None = None,
    promotion_reason: str | None = None,
    approval_ref: str | None = None,
) -> dict[str, Any]:
    policy = risk_policy()
    if requested_lane not in {"auto", "quick", "standard", "full"}:
        raise ValueError(f"unknown requested lane: {requested_lane}")

    declared = _normalize_signal_names(declared_signals, policy)
    inferred = _keyword_signals(task, policy) - declared
    all_signals = declared | inferred
    hard = sorted(all_signals & set(policy.get("hard_triggers", {})))
    soft_weights = policy.get("soft_signals", {})
    score = sum(max(0, int(soft_weights.get(signal, 0))) for signal in all_signals)
    quick_qualifiers = set(policy.get("quick_qualifiers", []))
    thresholds = policy["thresholds"]
    rationale: list[str] = []

    if hard:
        recommended = "full"
        rationale.append("One or more hard-risk signals force the full lane.")
    elif not all_signals:
        recommended = policy.get("unknown_default_lane", "standard")
        rationale.append("No reliable risk signal was supplied; the conservative default is standard.")
    elif score >= int(thresholds["full_min"]):
        recommended = "full"
        rationale.append(f"Risk score {score} meets the full-lane threshold.")
    elif score <= int(thresholds["quick_max"]) and all_signals & quick_qualifiers:
        recommended = "quick"
        rationale.append("The task is bounded, reversible, and qualifies for the quick lane.")
    else:
        recommended = "standard"
        rationale.append("The task needs structured investigation or review but has no hard-risk trigger.")

    lane_ranks = {"quick": 0, "standard": 1, "full": 2}
    requested_below_floor = (
        requested_lane != "auto"
        and lane_ranks[requested_lane] < lane_ranks[recommended]
    )
    forced = requested_below_floor
    if requested_lane == "auto":
        selected = recommended
        source = "automatic"
    elif requested_below_floor:
        selected = recommended
        source = "forced_hard_trigger" if hard else "forced_policy_floor"
        rationale.append(
            f"Requested lane {requested_lane} was promoted to {recommended} by the deterministic risk floor."
        )
    else:
        selected = requested_lane
        source = "explicit_human_request" if previous_lane is None else "promotion"
        if requested_lane != recommended:
            rationale.append(
                f"Human-selected lane {requested_lane} is more conservative than the automatic recommendation {recommended}."
            )

    signal_rows = []
    for signal in sorted(all_signals):
        is_hard = signal in policy.get("hard_triggers", {})
        signal_rows.append(
            {
                "name": signal,
                "weight": 0 if is_hard else int(soft_weights.get(signal, 0)),
                "hard_trigger": is_hard,
                "source": "declared" if signal in declared else "keyword_hint",
            }
        )

    return {
        "schema_version": "1.0.0",
        "work_id": work_id,
        "classifier_version": policy["classifier_version"],
        "requested_lane": requested_lane,
        "recommended_lane": recommended,
        "selected_lane": selected,
        "selection_source": source,
        "risk_score": score,
        "signals": signal_rows,
        "hard_triggers": hard,
        "forced_promotion": forced,
        "rationale": rationale,
        "previous_lane": previous_lane,
        "promotion_reason": promotion_reason,
        "approval_ref": approval_ref,
    }


def build_phase_waivers(work_id: str, lane: str) -> dict[str, Any]:
    canonical = [
        phase["state"]
        for phase in yaml.safe_load((ROOT / "orchestrator/phase-registry.yaml").read_text())["phases"]
    ]
    required = phase_path(lane)
    omitted = [
        {
            "phase": phase,
            "reason": f"Waived by the approved {lane} governance lane; promote the lane if this phase becomes necessary.",
        }
        for phase in canonical
        if phase not in required
    ]
    return {
        "schema_version": "1.0.0",
        "work_id": work_id,
        "lane": lane,
        "required_phases": required,
        "omitted_phases": omitted,
    }


def lane_rank(lane: str) -> int:
    return int(lane_config(lane)["rank"])


def promotion_state(current_lane: str, target_lane: str, current_state: str) -> str:
    if lane_rank(target_lane) <= lane_rank(current_lane):
        raise ValueError(f"lane transition must be a promotion: {current_lane} -> {target_lane}")
    target_path = phase_path(target_lane)
    if current_state == "PROBLEM_ALIGNMENT":
        return current_state
    entry = (
        lane_registry()
        .get("promotion_entry_states", {})
        .get(current_lane, {})
        .get(target_lane)
    )
    if not entry or entry not in target_path:
        raise ValueError(f"missing promotion entry state for {current_lane} -> {target_lane}")
    # Preserve work only when it is already at or before the newly required entry state.
    if current_state in target_path and target_path.index(current_state) <= target_path.index(entry):
        return current_state
    return entry


def validate_delegation(data: dict[str, Any]) -> list[str]:
    errors = validate_schema(data, "delegation-packet.schema.json")
    if errors:
        return errors

    phases, agents = registry()
    lifecycle = data["lifecycle"]
    phase_name = lifecycle["current_phase"]
    target = data["identity"]["target_agent"]
    skill = lifecycle["skill"]
    lane = lifecycle.get("lane", "full")
    track_id = lifecycle.get("track")

    if phase_name not in phases:
        errors.append(f"unknown lifecycle phase: {phase_name}")
        return errors
    try:
        row = resolved_phase(phase_name, lane)
    except ValueError as error:
        errors.append(str(error))
        return errors

    is_composite = bool(row.get("composite", False))
    expected_transition = row["success_state"]
    expected_write_mode = row["source_write_mode"]
    if is_composite:
        if not track_id:
            errors.append(f"composite phase {phase_name} requires a lifecycle track")
            return errors
        try:
            track = resolve_track(phase_name, lane, track_id)
        except ValueError as error:
            errors.append(str(error))
            return errors
        expected_agent = track["agent"]
        expected_skill = track["skill"]
        expected_write_mode = track.get("source_write_mode", "deny")
        # A track completes inside the composite phase. Only the aggregate artifact advances lifecycle state.
        expected_transition = phase_name
    else:
        if track_id is not None:
            errors.append(f"non-composite phase {phase_name} must not carry a lifecycle track")
        expected_agent = row["agent"]
        expected_skill = row["skill"]
        if expected_agent == "t-think":
            errors.append(f"phase {phase_name} in lane {lane} is root-handled and must not be delegated")

    if expected_agent != target:
        errors.append(f"phase {phase_name} requires {expected_agent}, got {target}")
    if expected_skill != skill:
        errors.append(f"phase {phase_name} requires {expected_skill}, got {skill}")
    if lifecycle.get("expected_next_state") not in (None, expected_transition):
        errors.append(
            f"phase {phase_name} track {track_id or '-'} in lane {lane} must expect {expected_transition}, "
            f"got {lifecycle.get('expected_next_state')}"
        )
    if lifecycle.get("artifact_mode") not in (None, lane_config(lane)["artifact_mode"]):
        errors.append(f"lane {lane} requires artifact mode {lane_config(lane)['artifact_mode']}")

    if target not in agents:
        errors.append(f"unknown subagent: {target}")
        return errors
    agent = agents[target]
    if is_composite:
        authorized = any(
            item.get("phase") == phase_name
            and item.get("track") == track_id
            and item.get("skill") == skill
            for item in agent.get("phase_tracks", [])
        )
        if not authorized:
            errors.append("agent manifest does not authorize composite phase/track/skill")
    elif phase_name not in agent["phases"] or skill not in agent["skills"]:
        errors.append("agent manifest does not authorize phase/skill")

    permissions = data["permissions"]
    expected = expected_write_mode
    if permissions["source_write"] != expected:
        errors.append(f"phase {phase_name} track {track_id or '-'} source_write must be {expected}")
    if data["workspace"]["discovery"] != {
        "respect_vcs_ignore": True,
        "include_untracked": True,
        "include_ignored": False,
    }:
        errors.append("workspace discovery must respect VCS ignore and exclude ignored files by default")
    if expected == "approved_targets_only" and not permissions["approved_write_targets"]:
        errors.append("bounded implementation requires at least one approved_write_target")
    if expected != "approved_targets_only" and permissions["approved_write_targets"]:
        errors.append(f"{phase_name} must not carry approved_write_targets")
    if expected == "generated_outputs_only" and not permissions["generated_output_paths"]:
        errors.append("verification requires declared generated_output_paths")
    if expected != "generated_outputs_only" and phase_name != "BOUNDED_IMPLEMENTATION" and permissions["generated_output_paths"]:
        errors.append(f"{phase_name} must not carry generated_output_paths")
    if permissions["ignored_file_access"]["mode"] == "human_approved" and not permissions["ignored_file_access"]["human_approval_ref"]:
        errors.append("human-approved ignored file access requires approval reference")
    if permissions["ignored_file_access"]["mode"] == "deny" and permissions["ignored_file_access"]["human_approval_ref"] is not None:
        errors.append("denied ignored file access must not carry approval reference")

    protected = permissions["protected_paths"]
    for path in permissions["approved_write_targets"] + permissions["generated_output_paths"]:
        if is_outside(path):
            errors.append(f"path escapes workspace: {path}")
        if matches(path, protected):
            errors.append(f"authorized target overlaps protected path: {path}")
    for item in data["artifact_inputs"]:
        if is_outside(item["ref"]):
            errors.append(f"artifact input escapes workspace: {item['ref']}")
    for key in ("artifact_path", "result_path", "boundary_report_path"):
        path = data["output_contract"][key]
        if is_outside(path):
            errors.append(f"{key} escapes workspace: {path}")
        if not norm(path).startswith(".t-think/"):
            errors.append(f"{key} must be below .t-think/: {path}")
    return errors


def audit_boundaries(packet: dict[str, Any], activity: dict[str, Any]) -> dict[str, Any]:
    errors = validate_delegation(packet)
    permissions = packet["permissions"]
    target = packet["identity"]["target_agent"]
    invocation = packet["identity"]["invocation_id"]
    source = [norm(item) for item in activity.get("source_changes", [])]
    governance = [norm(item) for item in activity.get("governance_artifact_changes", [])]
    generated = [norm(item) for item in activity.get("generated_output_changes", [])]
    outside = [str(item) for item in activity.get("outside_workspace_access", [])]
    ignored = [norm(item) for item in activity.get("ignored_file_access", [])]
    protected = permissions["protected_paths"]

    for path in source + governance + generated:
        if is_outside(path):
            errors.append(f"path escapes workspace: {path}")
        if matches(path, protected):
            errors.append(f"protected path touched: {path}")
    for path in governance:
        if not path.startswith(".t-think/"):
            errors.append(f"governance artifact outside .t-think/: {path}")

    mode = permissions["source_write"]
    if source:
        if mode != "approved_targets_only":
            errors.append(f"{target} changed source while mode is {mode}")
        for path in source:
            if not matches(path, permissions["approved_write_targets"]):
                errors.append(f"unapproved source change: {path}")
    if generated:
        allowed = permissions["generated_output_paths"]
        if mode not in ("generated_outputs_only", "approved_targets_only"):
            errors.append(f"{target} created generated outputs while mode is {mode}")
        for path in generated:
            if not matches(path, allowed):
                errors.append(f"undeclared generated output: {path}")
    if outside:
        errors.extend(f"outside-workspace access: {path}" for path in outside)
    if ignored and permissions["ignored_file_access"]["mode"] != "human_approved":
        errors.extend(f"ignored file read without approval: {path}" for path in ignored)

    return {
        "schema_version": "1.0.0",
        "invocation_id": invocation,
        "agent": target,
        "status": "FAIL" if errors else "PASS",
        "source_changes": source,
        "governance_artifact_changes": governance,
        "generated_output_changes": generated,
        "outside_workspace_access": outside,
        "ignored_file_access": ignored,
        "violations": errors,
    }


def validate_result(
    result: dict[str, Any], packet: dict[str, Any], boundary: dict[str, Any]
) -> list[str]:
    errors = validate_schema(result, "subagent-result.schema.json")
    errors += validate_schema(boundary, "boundary-report.schema.json")
    if errors:
        return errors

    identity = packet["identity"]
    lifecycle = packet["lifecycle"]
    if result["invocation_id"] != identity["invocation_id"]:
        errors.append("result invocation_id mismatch")
    if result["agent"] != identity["target_agent"]:
        errors.append("result agent mismatch")
    if result["phase"] != lifecycle["current_phase"]:
        errors.append("result phase mismatch")
    if result["skill"] != lifecycle["skill"]:
        errors.append("result skill mismatch")
    if result.get("track") != lifecycle.get("track"):
        errors.append("result track mismatch")
    if (
        boundary["invocation_id"] != identity["invocation_id"]
        or boundary["agent"] != identity["target_agent"]
    ):
        errors.append("boundary identity mismatch")
    if boundary["status"] != "PASS" or result["boundary_report"]["status"] != "PASS":
        errors.append("boundary report did not pass")
    if result["status"] == "COMPLETED" and not all(result["validation"].values()):
        errors.append("completed result has failed validation flags")

    lane = lifecycle.get("lane", "full")
    expected = lifecycle.get("expected_next_state")
    if expected is None:
        phase = resolved_phase(lifecycle["current_phase"], lane)
        expected = lifecycle["current_phase"] if phase.get("composite") else phase["success_state"]
    if result["status"] == "COMPLETED" and result["recommended_transition"]["state"] != expected:
        errors.append(f"completed result must recommend {expected}")
    return errors
