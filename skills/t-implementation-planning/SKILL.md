---
name: t-implementation-planning
description: Convert an approved solution into an ordered implementation, verification, rollout, migration, and rollback plan.
version: 2.3.1
lifecycle_state: IMPLEMENTATION_BLUEPRINT
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: IMPLEMENTATION_BLUEPRINT
  cost-profile: economy-compatible
---
# Implementation Planning Skill

> **Composite-phase component:** Runs as a fresh track inside `IMPLEMENTATION_BLUEPRINT`. It does not advance lifecycle state directly; `t-think` creates the aggregate artifact.

## Purpose
Translate one immutable, human-approved solution contract into a complete, evidence-backed, reviewable implementation plan without editing code or making new semantic decisions.

## Inputs
Use `schemas/input.schema.json`. The skill requires:
- a Solution Critique output whose gate is `READY_FOR_IMPLEMENTATION_PLAN`;
- an `APPROVED` solution contract signed by a human;
- the bound evidence ledger and system model;
- an exact repository snapshot that must be re-inspected from actual code.

## Procedure
1. Bind to the exact approved contract, model version, repository commit, and source artifacts.
2. Re-inspect actual code/configuration/schema/tests relevant to the approved change surface. Conversation memory is only a search hint.
3. Normalize every approved obligation into stable `PTGT-*` planning targets.
4. Decompose the solution into atomic `PLN-*` items with explicit operations, preconditions, failure conditions, completion evidence, verification, rollback, and dependencies.
5. Map every plan item to problem, model, evidence, invariant, and approved solution commitments.
6. Build an acyclic dependency graph and deterministic topological order.
7. Build test/t-verification work as part of the plan, including pre-patch reproduction, negative paths, invariants, compatibility, concurrency, migration, and rollback where applicable.
8. Reconcile exact files discovered from actual code with the approved change surface. Supporting files are allowed only when evidence-backed and semantically non-expanding.
9. Detect semantic decisions, solution conflicts, model conflicts, evidence gaps, repository drift, and scope expansion. Do not resolve them silently.
10. Route the package to the earliest correct upstream phase or, when complete, to `PLAN_CRITIQUE`.

## Outputs
- planning targets JSONL;
- implementation plan items JSONL;
- dependency edges JSONL;
- plan coverage matrix CSV;
- verification plan JSONL;
- rollback plan JSONL;
- planning findings JSONL;
- implementation planning report Markdown;
- lifecycle output YAML.

## Non-negotiable rules
- No code, schema, configuration, test, or deployment artifact may be modified in this phase.
- Planning may decompose an approved decision but may not change its semantics.
- Every material plan operation must be evidence-backed and mapped.
- Every mandatory planning target must be fully covered before critique.
- New semantic decisions require return to Solution Design.
- Evidence gaps require Investigation; model contradictions require System Modeling.
- A plan is not implementation authorization. It must pass Plan Critique first.

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
