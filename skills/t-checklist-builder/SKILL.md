---
name: t-checklist-builder
description: Convert every approved plan operation into one atomic, dependency-aware, test- and rollback-bound checklist item.
version: 1.0.0
lifecycle_state: IMPLEMENTATION_BLUEPRINT
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: IMPLEMENTATION_BLUEPRINT
  cost-profile: economy-compatible
---
# Checklist Builder Skill

> **Composite-phase component:** Runs as a fresh track inside `IMPLEMENTATION_BLUEPRINT`. It does not advance lifecycle state directly; `t-think` creates the aggregate artifact.

## Purpose
Transform an approved, immutable implementation plan into an atomic implementation checklist without executing changes, inventing semantic decisions, silently replanning, or expanding the approved change surface.

## Required inputs
Use `schemas/input.schema.json`. The source must include an approved plan contract, a Plan Critique output gated `READY_FOR_IMPLEMENTATION_CHECKLIST`, the exact planning bundle, evidence ledger, and model artifacts.

## Procedure
1. Bind to the approved plan contract, repository commit, plan bundle digest, and exact artifact versions.
2. Recompute the planning bundle digest and reject drift.
3. Enumerate every numbered operation from every approved plan item.
4. Create exactly one atomic `CHK-*` item for each operation.
5. Preserve source scope, targets, evidence, model links, invariants, risks, verification, rollback, and completion evidence.
6. Derive checklist dependencies from within-plan sequence and approved plan dependencies.
7. Compute a deterministic DAG, topological order, and safe parallel execution levels.
8. Build exact operation coverage and execution batches with explicit human gates.
9. Emit findings and route any ambiguity or upstream defect to the earliest responsible phase.
10. Transition only to `CHECKLIST_CRITIQUE`; never implement code in this skill.

## Outputs
- atomic checklist items JSONL;
- checklist dependency edges JSONL;
- plan-operation coverage CSV;
- execution batches JSONL;
- checklist findings JSONL;
- report Markdown;
- lifecycle output YAML.

## Non-negotiable rules
- One checklist item represents exactly one approved plan operation.
- Every approved operation is covered exactly once.
- No new semantic decision, scope expansion, hidden fallback, or silent replanning.
- Ambiguity during construction is `IMPLEMENTATION_FAILED` or a lifecycle loopback, never a guess.
- Verification is mandatory; planned rollback mappings must be retained.
- Source operation text and digest are immutable.
- The builder does not edit code, tests, schemas, configuration, data, or deployment state.

---

## Small-model execution contract

This phase is designed to remain reliable on economical coding models. Follow these mechanical rules:

1. Load only this `SKILL.md`, its declared schemas/templates, the current work-state file, and explicitly referenced upstream artifacts. Do not preload other phase skills.
2. Use IDs, enums, paths, and gate names exactly as defined. Never paraphrase machine-readable values.
3. Produce artifacts from templates first, then fill fields from evidence. Do not invent missing values; record `UNKNOWN`, `ASSUMPTION`, `CONFLICT`, or a blocking finding as allowed by the schema.
4. Run the phase validator before claiming completion. Treat validator failure as authoritative and repair only mechanical defects owned by this phase.
5. Keep the conversational handoff compact: current state, artifacts written, validator command/result, blockers, human decision needed, and proposed next state.
6. Do not make a decision owned by another phase. Route to the earliest responsible phase.
7. If tool output is large, save it as evidence and summarize it with exact references rather than retaining raw logs in conversational context.
8. Repository mutation is forbidden unless this is `t-bounded-implementation`.
