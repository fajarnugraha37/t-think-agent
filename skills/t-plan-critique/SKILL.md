---
name: t-plan-critique
description: Assess plan critiques and freeze a human-approved implementation plan without silently mutating it.
version: 2.4.0
lifecycle_state: BLUEPRINT_CRITIQUE
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: BLUEPRINT_CRITIQUE
  cost-profile: economy-compatible
---
# Plan Critique Skill

> **Composite-phase component:** Runs as a fresh track inside `BLUEPRINT_CRITIQUE`. It does not advance lifecycle state directly; `t-think` creates the aggregate artifact.

## Purpose
Evaluate human critique of an evidence-backed implementation plan without blindly following the reviewer, silently mutating planning artifacts, making new semantic decisions, or implementing code.

## Required inputs
Use `schemas/input.schema.json`. The skill requires a transition-ready Implementation Planning package and at least one explicit human critique.

## Procedure
1. Bind to the exact planning run, repository commit, approved solution contract, and artifact versions.
2. Resolve every critique target to an actual planning artifact.
3. Re-read relevant plan items, dependencies, coverage, verification, rollback, model, and evidence.
4. Classify each critique as `ACCEPTED`, `PARTIALLY_ACCEPTED`, `REJECTED_WITH_EVIDENCE`, or `REQUIRES_INVESTIGATION`.
5. Provide structured rationale, contradicting evidence, alternatives, limitations, and falsification conditions.
6. Produce revision directives rather than editing the approved planning package.
7. Route evidence gaps and upstream defects to the earliest correct lifecycle phase.
8. Require explicit human approval before freezing the plan.
9. Generate an immutable approved plan contract whose bundle digest matches all planning artifacts.
10. Transition only to `IMPLEMENTATION_CHECKLIST`; never implement code in this skill.

## Outputs
- critique assessments JSONL;
- plan revision directives JSONL;
- evidence requests JSONL;
- human plan approval YAML;
- approved plan contract YAML;
- plan critique report Markdown;
- lifecycle output YAML.

## Non-negotiable rules
- Human critique is a claim to evaluate, not an automatic command.
- Rejection requires actual evidence.
- Accepted critique that changes the plan creates a directive and returns to Implementation Planning.
- A new semantic decision returns to Solution Design or Solution Critique.
- Only a human may approve the plan.
- Approved plan artifacts are immutable; later changes require versioning and re-approval.
- No code, test, schema, configuration, or deployment mutation is allowed in this phase.

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

<!-- BEGIN T-THINK PORTABLE RESOURCE CONTRACT -->
## Portable resource contract

- Resolve every bundled resource relative to the directory containing this `SKILL.md`.
- Read the generated [resource index](RESOURCE_INDEX.md) before opening templates, schemas, validators, examples, or supporting documentation.
- Treat linked `/`-separated paths as portable relative resource identifiers. Never construct a global path with `~`, `$HOME`, `%USERPROFILE%`, a drive letter, or backslashes.
- Prefer the host's native skill/resource loader. When an absolute filesystem path is unavoidable, join the platform-reported skill root and the relative identifier with the host path API; never concatenate path strings manually.
- If a required resource cannot be opened, return `BLOCKED` with reason `SKILL_RESOURCE_UNAVAILABLE`. Do not recreate a template from memory, infer its shape, or continue with an invented format.

Frequently required resources:

- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`validators/validate.py`](validators/validate.py)
<!-- END T-THINK PORTABLE RESOURCE CONTRACT -->
