#!/usr/bin/env python3
"""Structural and semantic validator for the problem-alignment skill."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "input": ROOT / "schemas" / "input.schema.json",
    "output": ROOT / "schemas" / "output.schema.json",
    "critique": ROOT / "schemas" / "critique.schema.json",
}


class ValidationIssue:
    def __init__(self, path: str, message: str) -> None:
        self.path = path
        self.message = message

    def __str__(self) -> str:
        return f"{self.path}: {self.message}" if self.path else self.message


def _normalize_yaml_scalars(value: Any) -> Any:
    """Convert PyYAML timestamp objects into JSON-compatible ISO strings."""
    if isinstance(value, (dt.datetime, dt.date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _normalize_yaml_scalars(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_yaml_scalars(item) for item in value]
    return value


def load_document(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return _normalize_yaml_scalars(yaml.safe_load(text))


def load_schema(kind: str) -> dict[str, Any]:
    return json.loads(SCHEMAS[kind].read_text(encoding="utf-8"))


def format_path(parts: Iterable[Any]) -> str:
    result = "$"
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}"
    return result


def structural_issues(document: Any, schema: dict[str, Any]) -> list[ValidationIssue]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues: list[ValidationIssue] = []
    for error in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path)):
        issues.append(ValidationIssue(format_path(error.absolute_path), error.message))
    return issues


def duplicate_id_issues(document: dict[str, Any]) -> list[ValidationIssue]:
    collections = {
        "human_statements": document.get("human_statements", []),
        "interpretations": document.get("interpretations", []),
        "terms": document.get("terms", []),
        "constraints": document.get("constraints", []),
        "acceptance_signals": document.get("acceptance_signals", []),
        "open_questions": document.get("open_questions", []),
        "deferred_to_investigation": document.get("deferred_to_investigation", []),
    }
    issues: list[ValidationIssue] = []
    seen: dict[str, str] = {}
    for collection_name, items in collections.items():
        for index, item in enumerate(items):
            item_id = item.get("id")
            if not item_id:
                continue
            if item_id in seen:
                issues.append(
                    ValidationIssue(
                        f"$.{collection_name}[{index}].id",
                        f"duplicate ID {item_id!r}; first seen at {seen[item_id]}",
                    )
                )
            else:
                seen[item_id] = f"$.{collection_name}[{index}].id"
    return issues


def reference_issues(document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    statement_ids = {item["id"] for item in document.get("human_statements", []) if "id" in item}

    def check_ids(path: str, ids: list[str]) -> None:
        for index, item_id in enumerate(ids):
            if item_id not in statement_ids:
                issues.append(
                    ValidationIssue(
                        f"{path}[{index}]",
                        f"references unknown human statement ID {item_id!r}",
                    )
                )

    normalized = document.get("normalized_problem", {})
    for field in ("observed_behavior", "expected_behavior", "impact", "success_definition"):
        for index, item in enumerate(normalized.get(field, [])):
            check_ids(
                f"$.normalized_problem.{field}[{index}].source_statement_ids",
                item.get("source_statement_ids", []),
            )

    for collection in ("constraints", "acceptance_signals"):
        for index, item in enumerate(document.get(collection, [])):
            check_ids(
                f"$.{collection}[{index}].source_statement_ids",
                item.get("source_statement_ids", []),
            )

    for index, item in enumerate(document.get("interpretations", [])):
        original_id = item.get("original_statement_id")
        if original_id and original_id not in statement_ids:
            issues.append(
                ValidationIssue(
                    f"$.interpretations[{index}].original_statement_id",
                    f"references unknown human statement ID {original_id!r}",
                )
            )

    for index, item in enumerate(document.get("open_questions", [])):
        answer_id = item.get("answer_statement_id")
        if answer_id is not None and answer_id not in statement_ids:
            issues.append(
                ValidationIssue(
                    f"$.open_questions[{index}].answer_statement_id",
                    f"references unknown human statement ID {answer_id!r}",
                )
            )
        status = item.get("status")
        if status == "ANSWERED" and not answer_id:
            issues.append(
                ValidationIssue(
                    f"$.open_questions[{index}]",
                    "ANSWERED question must provide answer_statement_id",
                )
            )
        if status == "OPEN" and answer_id is not None:
            issues.append(
                ValidationIssue(
                    f"$.open_questions[{index}]",
                    "OPEN question must not provide answer_statement_id",
                )
            )

    return issues


def output_semantic_issues(document: dict[str, Any], require_transition_ready: bool) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(duplicate_id_issues(document))
    issues.extend(reference_issues(document))

    metadata = document.get("metadata", {})
    approval = document.get("approval", {})
    gate = document.get("gate", {})
    questions = document.get("open_questions", [])
    interpretations = document.get("interpretations", [])

    open_blocking = [
        q for q in questions
        if q.get("classification") == "BLOCKING_ALIGNMENT" and q.get("status") == "OPEN"
    ]
    pending_material_interpretations = [
        item for item in interpretations
        if item.get("material") is True and item.get("human_confirmation") != "CONFIRMED"
    ]

    gate_status = gate.get("status")
    approved = approval.get("approved") is True
    artifact_status = metadata.get("status")

    if gate_status == "APPROVED_FOR_INVESTIGATION":
        if not approved:
            issues.append(ValidationIssue("$.approval.approved", "must be true for APPROVED_FOR_INVESTIGATION"))
        if artifact_status != "APPROVED":
            issues.append(ValidationIssue("$.metadata.status", "must be APPROVED for APPROVED_FOR_INVESTIGATION"))
        if not approval.get("reviewed_by"):
            issues.append(ValidationIssue("$.approval.reviewed_by", "is required for approved transition"))
        if not approval.get("reviewed_at"):
            issues.append(ValidationIssue("$.approval.reviewed_at", "is required for approved transition"))
        if not approval.get("explicit_statement"):
            issues.append(ValidationIssue("$.approval.explicit_statement", "explicit approval statement is required"))
        if open_blocking:
            issues.append(ValidationIssue("$.open_questions", "blocking alignment questions remain open"))
        if pending_material_interpretations:
            issues.append(ValidationIssue("$.interpretations", "material interpretations remain unconfirmed"))
        if gate.get("blocking_reasons"):
            issues.append(ValidationIssue("$.gate.blocking_reasons", "must be empty for approved transition"))
        if "INVESTIGATION" not in gate.get("next_valid_transitions", []):
            issues.append(ValidationIssue("$.gate.next_valid_transitions", "must include INVESTIGATION"))

    if approved and gate_status != "APPROVED_FOR_INVESTIGATION":
        issues.append(
            ValidationIssue(
                "$.gate.status",
                "approved artifact must use APPROVED_FOR_INVESTIGATION",
            )
        )

    if artifact_status == "APPROVED" and not approved:
        issues.append(ValidationIssue("$.approval.approved", "must be true when metadata.status is APPROVED"))

    if gate_status == "NEEDS_HUMAN_CLARIFICATION" and not open_blocking:
        issues.append(
            ValidationIssue(
                "$.gate.status",
                "NEEDS_HUMAN_CLARIFICATION requires at least one open BLOCKING_ALIGNMENT question",
            )
        )

    if gate_status == "READY_FOR_HUMAN_REVIEW":
        if open_blocking:
            issues.append(ValidationIssue("$.open_questions", "blocking questions must be closed before human review"))
        if pending_material_interpretations:
            issues.append(ValidationIssue("$.interpretations", "material interpretations must be confirmed before human review"))
        if approved:
            issues.append(ValidationIssue("$.approval.approved", "must remain false until explicit approval"))

    if gate_status == "REJECTED":
        if artifact_status != "REJECTED":
            issues.append(ValidationIssue("$.metadata.status", "must be REJECTED when gate is REJECTED"))
        if "REJECTED" not in gate.get("next_valid_transitions", []):
            issues.append(ValidationIssue("$.gate.next_valid_transitions", "must include REJECTED"))

    if require_transition_ready and gate_status != "APPROVED_FOR_INVESTIGATION":
        issues.append(
            ValidationIssue(
                "$.gate.status",
                "transition-ready validation requires APPROVED_FOR_INVESTIGATION",
            )
        )

    return issues


def validate(kind: str, path: Path, require_transition_ready: bool = False) -> list[ValidationIssue]:
    document = load_document(path)
    schema = load_schema(kind)
    issues = structural_issues(document, schema)
    if not issues and kind == "output":
        issues.extend(output_semantic_issues(document, require_transition_ready))
    elif require_transition_ready and kind != "output":
        issues.append(ValidationIssue("$", "--require-transition-ready is valid only for output"))
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=sorted(SCHEMAS), required=True)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument(
        "--require-transition-ready",
        action="store_true",
        help="Require an approved output that may transition to INVESTIGATION.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        issues = validate(args.kind, args.file, args.require_transition_ready)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if issues:
        print(f"INVALID: {args.file}", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    transition_suffix = " and transition-ready" if args.require_transition_ready else ""
    print(f"VALID{transition_suffix}: {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
