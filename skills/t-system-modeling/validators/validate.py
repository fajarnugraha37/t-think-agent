#!/usr/bin/env python3
"""Validate System Modeling skill artifacts and transition readiness."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "input": ROOT / "schemas/input.schema.json",
    "output": ROOT / "schemas/output.schema.json",
    "element": ROOT / "schemas/model-element.schema.json",
    "relation": ROOT / "schemas/model-relation.schema.json",
    "traceability": ROOT / "schemas/traceability-row.schema.json",
    "critique": ROOT / "schemas/critique.schema.json",
    "consistency": ROOT / "schemas/consistency-decision.schema.json",
    "evidence": ROOT / "schemas/upstream-evidence-record.schema.json",
}

CLAIM_PREFIX_TYPE = {
    "F": "FACT",
    "INF": "INFERENCE",
    "ASM": "ASSUMPTION",
    "UNK": "UNKNOWN",
    "CON": "CONFLICT",
    "INV": "INVARIANT_CANDIDATE",
    "RSK": "RISK",
}

@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def normalize(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize(v) for v in value]
    return value


def load_document(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return normalize(yaml.safe_load(text))


def load_schema(kind: str) -> dict[str, Any]:
    schema = json.loads(SCHEMAS[kind].read_text(encoding="utf-8"))
    # Resolve the one local cross-schema reference without network access.
    if kind == "output":
        consistency = json.loads(SCHEMAS["consistency"].read_text(encoding="utf-8"))
        schema["properties"]["consistency_assessment"] = consistency
    return schema


def format_path(path: Iterable[Any]) -> str:
    result = "$"
    for part in path:
        result += f"[{part}]" if isinstance(part, int) else f".{part}"
    return result


def structural_issues(document: Any, schema: dict[str, Any], prefix: str = "$") -> list[ValidationIssue]:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    issues: list[ValidationIssue] = []
    for error in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path)):
        p = format_path(error.absolute_path)
        if prefix != "$":
            p = prefix + (p[1:] if p.startswith("$") else p)
        issues.append(ValidationIssue(p, error.message))
    return issues


def load_jsonl(path: Path, kind: str) -> tuple[list[dict[str, Any]], list[ValidationIssue]]:
    records: list[dict[str, Any]] = []
    issues: list[ValidationIssue] = []
    schema = load_schema(kind)
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = normalize(json.loads(line))
        except json.JSONDecodeError as exc:
            issues.append(ValidationIssue(f"$[line:{line_no}]", f"invalid JSON: {exc.msg}"))
            continue
        records.append(record)
        issues.extend(structural_issues(record, schema, f"$[line:{line_no}]"))
    if not records:
        issues.append(ValidationIssue("$", "JSONL file must contain at least one record"))
    return records, issues


def split_ids(value: str | None) -> list[str]:
    if value is None or not value.strip():
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def load_traceability(path: Path) -> tuple[list[dict[str, Any]], list[ValidationIssue]]:
    issues: list[ValidationIssue] = []
    rows: list[dict[str, Any]] = []
    schema = load_schema("traceability")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_headers = {
            "trace_id", "problem_id", "evidence_ids", "model_element_ids",
            "model_relation_ids", "coverage_status", "summary", "limitations",
        }
        actual_headers = set(reader.fieldnames or [])
        missing = required_headers - actual_headers
        extra = actual_headers - required_headers
        if missing:
            issues.append(ValidationIssue("$.headers", f"missing CSV columns: {sorted(missing)}"))
        if extra:
            issues.append(ValidationIssue("$.headers", f"unexpected CSV columns: {sorted(extra)}"))
        if issues:
            return rows, issues
        for row_no, raw in enumerate(reader, 2):
            row = {
                "trace_id": (raw.get("trace_id") or "").strip(),
                "problem_id": (raw.get("problem_id") or "").strip(),
                "evidence_ids": split_ids(raw.get("evidence_ids")),
                "model_element_ids": split_ids(raw.get("model_element_ids")),
                "model_relation_ids": split_ids(raw.get("model_relation_ids")),
                "coverage_status": (raw.get("coverage_status") or "").strip(),
                "summary": (raw.get("summary") or "").strip(),
            }
            limitations = (raw.get("limitations") or "").strip()
            if limitations:
                row["limitations"] = limitations
            rows.append(row)
            issues.extend(structural_issues(row, schema, f"$[row:{row_no}]"))
    if not rows:
        issues.append(ValidationIssue("$", "traceability CSV must contain at least one row"))
    return rows, issues


def duplicate_id_issues(records: list[dict[str, Any]], label: str) -> list[ValidationIssue]:
    counts = Counter(record.get("id") for record in records if record.get("id"))
    return [ValidationIssue("$", f"duplicate {label} id: {item}") for item, count in counts.items() if count > 1]


def claim_type_from_id(claim_id: str) -> str | None:
    prefix = claim_id.split("-", 1)[0]
    return CLAIM_PREFIX_TYPE.get(prefix)


def input_semantic_issues(doc: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required = doc.get("required_dimensions", [])
    optional = doc.get("optional_dimensions", [])
    overlap = sorted(set(required) & set(optional))
    if overlap:
        issues.append(ValidationIssue("$.optional_dimensions", f"dimensions cannot be both required and optional: {overlap}"))

    problem_ids = {item.get("id") for item in doc.get("approved_problem", {}).get("elements", [])}
    problem_ids |= {item.get("id") for item in doc.get("approved_problem", {}).get("success_criteria", [])}
    problem_ids |= {item.get("id") for item in doc.get("approved_problem", {}).get("constraints", [])}
    for i, objective in enumerate(doc.get("modeling_objectives", [])):
        for problem_id in objective.get("mapped_problem_ids", []):
            if problem_id not in problem_ids:
                issues.append(ValidationIssue(f"$.modeling_objectives[{i}].mapped_problem_ids", f"unknown approved problem id: {problem_id}"))

    source_problem_ids = set(doc.get("source_investigation", {}).get("problem_statement_ids", []))
    if not source_problem_ids.issubset(problem_ids):
        missing = sorted(source_problem_ids - problem_ids)
        issues.append(ValidationIssue("$.source_investigation.problem_statement_ids", f"ids absent from approved_problem: {missing}"))
    return issues


def evidence_semantic_issues(records: list[dict[str, Any]]) -> list[ValidationIssue]:
    issues = duplicate_id_issues(records, "evidence")
    by_id = {record.get("id"): record for record in records}
    for index, record in enumerate(records):
        claim_id = record.get("id", "")
        expected = claim_type_from_id(claim_id)
        if expected and record.get("type") != expected:
            issues.append(ValidationIssue(f"$[{index}].type", f"id {claim_id} requires type {expected}"))
        for field in ("supporting_claim_ids", "contradicting_claim_ids"):
            for ref in record.get(field, []):
                if ref not in by_id:
                    issues.append(ValidationIssue(f"$[{index}].{field}", f"unknown claim id: {ref}"))
    return issues


def element_semantic_issues(elements: list[dict[str, Any]], evidence: dict[str, dict[str, Any]] | None) -> list[ValidationIssue]:
    issues = duplicate_id_issues(elements, "model element")
    by_id = {element["id"]: element for element in elements if "id" in element}
    for index, element in enumerate(elements):
        active = element.get("status") in {"ACTIVE", "WEAKENED"}
        evidence_ids = element.get("evidence_ids", [])
        if active and not evidence_ids:
            issues.append(ValidationIssue(f"$[{index}].evidence_ids", "active model element must reference evidence"))
        if evidence is not None:
            for ref in evidence_ids:
                if ref not in evidence:
                    issues.append(ValidationIssue(f"$[{index}].evidence_ids", f"unknown evidence id: {ref}"))
            typed_fields = {
                "supporting_fact_ids": "FACT",
                "supporting_inference_ids": "INFERENCE",
                "assumption_ids": "ASSUMPTION",
                "unknown_ids": "UNKNOWN",
                "conflict_ids": "CONFLICT",
            }
            for field, expected_type in typed_fields.items():
                for ref in element.get(field, []):
                    if ref not in evidence:
                        issues.append(ValidationIssue(f"$[{index}].{field}", f"unknown evidence id: {ref}"))
                    elif evidence[ref].get("type") != expected_type:
                        issues.append(ValidationIssue(f"$[{index}].{field}", f"{ref} is not {expected_type}"))
        basis = element.get("epistemic_basis")
        if active and basis == "FACT_BACKED" and not element.get("supporting_fact_ids"):
            issues.append(ValidationIssue(f"$[{index}].supporting_fact_ids", "FACT_BACKED element requires at least one fact"))
        if active and basis in {"INFERENCE_BACKED", "MIXED"}:
            if not element.get("supporting_inference_ids") and not element.get("reasoning_summary"):
                issues.append(ValidationIssue(f"$[{index}]", "inference-backed element requires inference reference or reasoning summary"))
            if not element.get("alternative_explanations"):
                issues.append(ValidationIssue(f"$[{index}].alternative_explanations", "inference-backed element must disclose alternatives"))
        if element.get("type") == "BEHAVIOR_GAP" and "behavior_gap" in element:
            detail = element["behavior_gap"]
            for ref in detail.get("actual_element_ids", []):
                if ref not in by_id:
                    issues.append(ValidationIssue(f"$[{index}].behavior_gap.actual_element_ids", f"unknown model element: {ref}"))
                elif by_id[ref].get("type") != "ACTUAL_BEHAVIOR":
                    issues.append(ValidationIssue(f"$[{index}].behavior_gap.actual_element_ids", f"{ref} is not ACTUAL_BEHAVIOR"))
            for ref in detail.get("intended_element_ids", []):
                if ref not in by_id:
                    issues.append(ValidationIssue(f"$[{index}].behavior_gap.intended_element_ids", f"unknown model element: {ref}"))
                elif by_id[ref].get("type") != "INTENDED_BEHAVIOR":
                    issues.append(ValidationIssue(f"$[{index}].behavior_gap.intended_element_ids", f"{ref} is not INTENDED_BEHAVIOR"))
        if element.get("status") == "SUPERSEDED" and not element.get("supersedes"):
            issues.append(ValidationIssue(f"$[{index}].supersedes", "SUPERSEDED element must identify the prior element it supersedes"))
    return issues


def relation_semantic_issues(relations: list[dict[str, Any]], elements: dict[str, dict[str, Any]] | None, evidence: dict[str, dict[str, Any]] | None) -> list[ValidationIssue]:
    issues = duplicate_id_issues(relations, "model relation")
    for index, relation in enumerate(relations):
        if relation.get("from_element_id") == relation.get("to_element_id"):
            issues.append(ValidationIssue(f"$[{index}]", "self-relations are not allowed"))
        if elements is not None:
            for field in ("from_element_id", "to_element_id"):
                ref = relation.get(field)
                if ref not in elements:
                    issues.append(ValidationIssue(f"$[{index}].{field}", f"unknown model element: {ref}"))
        if evidence is not None:
            for ref in relation.get("evidence_ids", []):
                if ref not in evidence:
                    issues.append(ValidationIssue(f"$[{index}].evidence_ids", f"unknown evidence id: {ref}"))
        if relation.get("confidence") in {"MEDIUM", "LOW"} and not relation.get("reasoning_summary"):
            issues.append(ValidationIssue(f"$[{index}].reasoning_summary", "non-HIGH relation requires explicit reasoning summary"))
    return issues


def trace_semantic_issues(rows: list[dict[str, Any]], elements: dict[str, Any] | None, relations: dict[str, Any] | None, evidence: dict[str, Any] | None) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    counts = Counter(row.get("trace_id") for row in rows)
    for trace_id, count in counts.items():
        if count > 1:
            issues.append(ValidationIssue("$", f"duplicate trace id: {trace_id}"))
    for index, row in enumerate(rows):
        if elements is not None:
            for ref in row.get("model_element_ids", []):
                if ref not in elements:
                    issues.append(ValidationIssue(f"$[{index}].model_element_ids", f"unknown model element: {ref}"))
        if relations is not None:
            for ref in row.get("model_relation_ids", []):
                if ref not in relations:
                    issues.append(ValidationIssue(f"$[{index}].model_relation_ids", f"unknown model relation: {ref}"))
        if evidence is not None:
            for ref in row.get("evidence_ids", []):
                if ref not in evidence:
                    issues.append(ValidationIssue(f"$[{index}].evidence_ids", f"unknown evidence id: {ref}"))
        if row.get("coverage_status") == "JUSTIFIED_OUT_OF_SCOPE" and not row.get("limitations"):
            issues.append(ValidationIssue(f"$[{index}].limitations", "JUSTIFIED_OUT_OF_SCOPE requires limitations/justification"))
    return issues


def output_semantic_issues(
    doc: dict[str, Any],
    elements: list[dict[str, Any]] | None,
    relations: list[dict[str, Any]] | None,
    traces: list[dict[str, Any]] | None,
    ledger: list[dict[str, Any]] | None,
    transition: bool,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    element_map = {item["id"]: item for item in elements or [] if "id" in item}
    relation_map = {item["id"]: item for item in relations or [] if "id" in item}
    evidence_map = {item["id"]: item for item in ledger or [] if "id" in item}

    if elements is not None:
        expected = doc.get("model_files", {}).get("elements", {}).get("record_count")
        if expected != len(elements):
            issues.append(ValidationIssue("$.model_files.elements.record_count", f"expected {len(elements)} from elements file"))
    if relations is not None:
        expected = doc.get("model_files", {}).get("relations", {}).get("record_count")
        if expected != len(relations):
            issues.append(ValidationIssue("$.model_files.relations.record_count", f"expected {len(relations)} from relations file"))
    if traces is not None:
        expected = doc.get("model_files", {}).get("traceability_matrix", {}).get("record_count")
        if expected != len(traces):
            issues.append(ValidationIssue("$.model_files.traceability_matrix.record_count", f"expected {len(traces)} from traceability file"))

    # Validate output references.
    for section_name in ("dimension_coverage", "problem_coverage"):
        for index, item in enumerate(doc.get(section_name, [])):
            for ref in item.get("model_element_ids", []):
                if elements is not None and ref not in element_map:
                    issues.append(ValidationIssue(f"$.{section_name}[{index}].model_element_ids", f"unknown model element: {ref}"))
            for ref in item.get("model_relation_ids", []):
                if relations is not None and ref not in relation_map:
                    issues.append(ValidationIssue(f"$.{section_name}[{index}].model_relation_ids", f"unknown model relation: {ref}"))
            for ref in item.get("evidence_ids", []):
                if ledger is not None and ref not in evidence_map:
                    issues.append(ValidationIssue(f"$.{section_name}[{index}].evidence_ids", f"unknown evidence id: {ref}"))
            if item.get("status") == "JUSTIFIED_NOT_APPLICABLE" and not item.get("justification"):
                issues.append(ValidationIssue(f"$.{section_name}[{index}].justification", "required for JUSTIFIED_NOT_APPLICABLE"))

    reasoning = doc.get("reasoning_disclosure", {})
    for collection in ("fact_to_model_mappings", "inference_to_model_mappings"):
        for index, mapping in enumerate(reasoning.get(collection, [])):
            claim_id = mapping.get("claim_id")
            if ledger is not None and claim_id not in evidence_map:
                issues.append(ValidationIssue(f"$.reasoning_disclosure.{collection}[{index}].claim_id", f"unknown evidence id: {claim_id}"))
            for ref in mapping.get("model_element_ids", []):
                if elements is not None and ref not in element_map:
                    issues.append(ValidationIssue(f"$.reasoning_disclosure.{collection}[{index}].model_element_ids", f"unknown model element: {ref}"))
            for ref in mapping.get("model_relation_ids", []):
                if relations is not None and ref not in relation_map:
                    issues.append(ValidationIssue(f"$.reasoning_disclosure.{collection}[{index}].model_relation_ids", f"unknown model relation: {ref}"))
    for index, usage in enumerate(reasoning.get("assumption_usage", [])):
        assumption_id = usage.get("assumption_id")
        if ledger is not None:
            if assumption_id not in evidence_map:
                issues.append(ValidationIssue(f"$.reasoning_disclosure.assumption_usage[{index}].assumption_id", f"unknown evidence id: {assumption_id}"))
            elif evidence_map[assumption_id].get("type") != "ASSUMPTION":
                issues.append(ValidationIssue(f"$.reasoning_disclosure.assumption_usage[{index}].assumption_id", f"{assumption_id} is not ASSUMPTION"))
        for ref in usage.get("used_by_model_ids", []):
            if elements is not None and ref not in element_map:
                issues.append(ValidationIssue(f"$.reasoning_disclosure.assumption_usage[{index}].used_by_model_ids", f"unknown model element: {ref}"))
    for collection in ("conflicts", "unknowns"):
        for index, item in enumerate(reasoning.get(collection, [])):
            claim_id = item.get("claim_id")
            if ledger is not None and claim_id not in evidence_map:
                issues.append(ValidationIssue(f"$.reasoning_disclosure.{collection}[{index}].claim_id", f"unknown evidence id: {claim_id}"))

    gate = doc.get("gate", {})
    consistency = doc.get("consistency_assessment", {})
    if gate.get("status") == "READY_FOR_MODEL_CRITIQUE":
        if doc.get("metadata", {}).get("status") != "COMPLETE":
            issues.append(ValidationIssue("$.metadata.status", "must be COMPLETE when ready for critique"))
        if gate.get("next_state") != "MODEL_CRITIQUE":
            issues.append(ValidationIssue("$.gate.next_state", "must be MODEL_CRITIQUE"))
        if gate.get("blocking_reasons"):
            issues.append(ValidationIssue("$.gate.blocking_reasons", "must be empty when ready for critique"))
        if consistency.get("status") != "CONSISTENT":
            issues.append(ValidationIssue("$.consistency_assessment.status", "must be CONSISTENT"))
        for field in ("problem_coverage_complete", "evidence_mapping_complete", "relation_integrity", "actual_intended_gap_consistent"):
            if not consistency.get(field):
                issues.append(ValidationIssue(f"$.consistency_assessment.{field}", "must be true"))
        if consistency.get("blocking_unknown_ids") or consistency.get("blocking_conflict_ids"):
            issues.append(ValidationIssue("$.consistency_assessment", "blocking unknowns/conflicts must be empty"))
        for index, item in enumerate(doc.get("problem_coverage", [])):
            if item.get("status") not in {"FULL", "JUSTIFIED_OUT_OF_SCOPE"}:
                issues.append(ValidationIssue(f"$.problem_coverage[{index}].status", "must be FULL or JUSTIFIED_OUT_OF_SCOPE"))
            if not item.get("model_element_ids") or not item.get("evidence_ids"):
                issues.append(ValidationIssue(f"$.problem_coverage[{index}]", "transition-ready problem coverage needs model and evidence mappings"))
        for index, item in enumerate(doc.get("dimension_coverage", [])):
            if item.get("required") and item.get("status") not in {"COVERED", "JUSTIFIED_NOT_APPLICABLE"}:
                issues.append(ValidationIssue(f"$.dimension_coverage[{index}].status", "required dimension is incomplete"))
            if item.get("status") == "COVERED" and (not item.get("model_element_ids") or not item.get("evidence_ids")):
                issues.append(ValidationIssue(f"$.dimension_coverage[{index}]", "covered dimension requires model and evidence mappings"))
        if elements is not None:
            active_types = {item.get("type") for item in elements if item.get("status") in {"ACTIVE", "WEAKENED"}}
            for required_type in ("ACTUAL_BEHAVIOR", "INTENDED_BEHAVIOR", "BEHAVIOR_GAP"):
                if required_type not in active_types:
                    issues.append(ValidationIssue("$.model_files.elements", f"transition requires an active {required_type} element"))
            active_assumption_backed = [item.get("id") for item in elements if item.get("status") in {"ACTIVE", "WEAKENED"} and item.get("epistemic_basis") == "ASSUMPTION_BACKED"]
            mapped_nonblocking = {item.get("assumption_id") for item in reasoning.get("assumption_usage", []) if item.get("blocking") is False}
            for element_id in active_assumption_backed:
                element = element_map[element_id]
                assumptions = set(element.get("assumption_ids", []))
                if not assumptions or not assumptions.issubset(mapped_nonblocking):
                    issues.append(ValidationIssue("$.reasoning_disclosure.assumption_usage", f"assumption-backed element {element_id} must map only to explicit non-blocking assumptions"))
        if traces is not None:
            output_problem_ids = {item.get("problem_id") for item in doc.get("problem_coverage", [])}
            trace_problem_ids = {item.get("problem_id") for item in traces}
            missing = sorted(output_problem_ids - trace_problem_ids)
            if missing:
                issues.append(ValidationIssue("$.model_files.traceability_matrix", f"missing traceability rows for problem ids: {missing}"))

    if gate.get("status") == "MODEL_INCOMPLETE":
        if gate.get("next_state") not in {"SYSTEM_MODEL", "INVESTIGATION"}:
            issues.append(ValidationIssue("$.gate.next_state", "incomplete model must return to SYSTEM_MODEL or INVESTIGATION"))
        if not gate.get("blocking_reasons"):
            issues.append(ValidationIssue("$.gate.blocking_reasons", "incomplete model must state blocking reasons"))
    if gate.get("status") == "BLOCKED" and doc.get("metadata", {}).get("status") != "BLOCKED":
        issues.append(ValidationIssue("$.metadata.status", "must be BLOCKED"))

    if transition:
        if gate.get("status") != "READY_FOR_MODEL_CRITIQUE":
            issues.append(ValidationIssue("$.gate.status", "transition-ready validation requires READY_FOR_MODEL_CRITIQUE"))
        for required_name, value in (("--elements", elements), ("--relations", relations), ("--traceability", traces), ("--ledger", ledger)):
            if value is None:
                issues.append(ValidationIssue("$", f"{required_name} is required for transition-ready validation"))
    return issues


def validate_single(kind: str, path: Path) -> list[ValidationIssue]:
    if kind in {"element", "relation", "evidence"}:
        records, issues = load_jsonl(path, kind)
        if issues:
            return issues
        if kind == "evidence":
            issues.extend(evidence_semantic_issues(records))
        elif kind == "element":
            issues.extend(element_semantic_issues(records, None))
        elif kind == "relation":
            issues.extend(relation_semantic_issues(records, None, None))
        return issues
    if kind == "traceability":
        rows, issues = load_traceability(path)
        if not issues:
            issues.extend(trace_semantic_issues(rows, None, None, None))
        return issues
    doc = load_document(path)
    issues = structural_issues(doc, load_schema(kind))
    if not issues and kind == "input":
        issues.extend(input_semantic_issues(doc))
    return issues


def validate_package(args: argparse.Namespace) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    output = load_document(args.file)
    issues.extend(structural_issues(output, load_schema("output"), "output$"))

    elements = relations = ledger = traces = None
    if args.elements:
        elements, found = load_jsonl(args.elements, "element")
        issues.extend(ValidationIssue("elements" + issue.path[1:], issue.message) for issue in found)
    if args.relations:
        relations, found = load_jsonl(args.relations, "relation")
        issues.extend(ValidationIssue("relations" + issue.path[1:], issue.message) for issue in found)
    if args.ledger:
        ledger, found = load_jsonl(args.ledger, "evidence")
        issues.extend(ValidationIssue("ledger" + issue.path[1:], issue.message) for issue in found)
    if args.traceability:
        traces, found = load_traceability(args.traceability)
        issues.extend(ValidationIssue("traceability" + issue.path[1:], issue.message) for issue in found)

    if issues:
        return issues

    evidence_map = {item["id"]: item for item in ledger or []}
    element_map = {item["id"]: item for item in elements or []}
    relation_map = {item["id"]: item for item in relations or []}

    if ledger is not None:
        issues.extend(ValidationIssue("ledger" + issue.path[1:], issue.message) for issue in evidence_semantic_issues(ledger))
    if elements is not None:
        issues.extend(ValidationIssue("elements" + issue.path[1:], issue.message) for issue in element_semantic_issues(elements, evidence_map if ledger is not None else None))
    if relations is not None:
        issues.extend(ValidationIssue("relations" + issue.path[1:], issue.message) for issue in relation_semantic_issues(relations, element_map if elements is not None else None, evidence_map if ledger is not None else None))
    if traces is not None:
        issues.extend(ValidationIssue("traceability" + issue.path[1:], issue.message) for issue in trace_semantic_issues(traces, element_map if elements is not None else None, relation_map if relations is not None else None, evidence_map if ledger is not None else None))

    issues.extend(output_semantic_issues(output, elements, relations, traces, ledger, args.require_transition_ready))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=["input", "output", "element", "relation", "traceability", "critique", "consistency", "evidence", "package"], required=True)
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--elements", type=Path)
    parser.add_argument("--relations", type=Path)
    parser.add_argument("--traceability", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--require-transition-ready", action="store_true")
    args = parser.parse_args()

    try:
        issues = validate_package(args) if args.kind in {"output", "package"} and any([args.elements, args.relations, args.traceability, args.ledger, args.require_transition_ready]) else validate_single(args.kind, args.file)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if issues:
        print(f"INVALID: {args.file}", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    suffix = " and transition-ready" if args.require_transition_ready else ""
    print(f"VALID{suffix}: {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
