#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

policy = (ROOT / "orchestrator/repository-intelligence-policy.md").read_text(encoding="utf-8")
for required in (
    "Graphify is fail-open",
    "Never invent Graphify commands",
    "t-think` owns the first availability decision",
    "not_needed",
    "possibly_stale",
    "artifact_inputs",
):
    if required not in policy:
        raise AssertionError(f"missing policy contract: {required}")

schema = json.loads((ROOT / "schemas/repository-intelligence.schema.json").read_text(encoding="utf-8"))
statuses = set(schema["properties"]["graphify_status"]["enum"])
expected = {"available", "unavailable", "not_needed", "failed", "possibly_stale"}
if not expected.issubset(statuses):
    raise AssertionError(f"missing Graphify statuses: {sorted(expected - statuses)}")

required_fields = set(schema["required"])
expected_fields = {
    "graphify_status",
    "repository_root",
    "queries_performed",
    "findings",
    "affected_areas",
    "uncertainties",
    "verification_required",
}
if required_fields != expected_fields:
    raise AssertionError(f"repository-intelligence fields drifted: {sorted(required_fields)}")

generator = (ROOT / "scripts/generate_adapters.py").read_text(encoding="utf-8")
if "repository-intelligence-policy.md" not in generator:
    raise AssertionError("adapter generator does not load the shared policy")
if "name == 't-think'" not in generator:
    raise AssertionError("shared policy must be rooted at t-think rather than duplicated blindly")

for installer in (ROOT / "bin/install.sh", ROOT / "bin/install.ps1"):
    text = installer.read_text(encoding="utf-8")
    if "scripts/generate_adapters.py" not in text:
        raise AssertionError(f"installer does not regenerate platform adapters: {installer}")

for path in (
    ROOT / "docs/graphify-first-repository-intelligence.md",
    ROOT / "orchestrator/repository-intelligence-policy.md",
):
    text = path.read_text(encoding="utf-8")
    for forbidden in ("graphify init", "graphify install", "graphify update", "graphify build"):
        if forbidden in text.lower():
            raise AssertionError(f"automatic Graphify mutation wording found in {path}: {forbidden}")

print("graphify repository-intelligence contracts PASS")
