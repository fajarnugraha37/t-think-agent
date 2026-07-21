---
name: t-solution-design
description: Create materially distinct evidence-backed solution options or a justified single-option dominance proof.
version: 1.0.0
lifecycle_state: SOLUTION_DESIGN
previous_state: MODEL_CRITIQUE
next_state: SOLUTION_CRITIQUE
input_schema: schemas/input.schema.json
output_schema: schemas/output.schema.json
solution_option_schema: schemas/solution-option.schema.json
coverage_row_schema: schemas/coverage-row.schema.json
decision_record_schema: schemas/decision-record.schema.json
dominance_proof_schema: schemas/dominance-proof.schema.json
canonical_artifacts:
  - artifacts/05a-solution-design-input.yaml
  - artifacts/05b-solution-options.jsonl
  - artifacts/05c-solution-coverage-matrix.csv
  - artifacts/05d-decision-record.yaml
  - artifacts/05e-dominance-proof.yaml
  - artifacts/05f-solution-design-report.md
  - artifacts/05g-solution-design-output.yaml
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: SOLUTION_DESIGN
  cost-profile: economy-compatible
---
# Solution Design Skill

## Mission

Generate materially distinct, evidence-backed solution options for the approved system model. Make every engineering decision, trade-off, assumption, risk, compatibility effect, and verification strategy explicit. Map each option back to the approved problem, evidence, model gaps, and invariants before human critique begins.

This skill proposes and compares. It does not select a binding solution, modify code, produce an implementation plan, or silently alter the approved model.

## Preconditions

The phase may start only when:

1. Model Critique completed with `READY_FOR_CHANGE_OPTIONS`.
2. The exact approved system-model version is identified.
3. Canonical model elements, relations, traceability matrix, and evidence ledger are available.
4. Blocking evidence requests and model revisions are closed.
5. Human-approved residual uncertainties are carried forward.

## Hard prohibitions

The solution-design agent must not:

1. invent requirements, system behavior, or repository capabilities;
2. use conversation context as evidence;
3. hide assumptions inside option descriptions;
4. produce cosmetic alternatives that differ only by naming or packaging;
5. recommend an option without explicit comparison criteria;
6. mark a decision `APPROVED` or impersonate human authority;
7. silently narrow problem coverage;
8. claim compatibility, security, performance, or correctness without evidence and a verification strategy;
9. introduce implementation details unrelated to the approved model;
10. proceed when a material option decision requires missing evidence;
11. expose private chain-of-thought.

Expose structured rationale instead: premises, evidence references, option mechanism, decision dimensions, trade-offs, alternatives, falsification conditions, and residual uncertainty.

## Required workflow

1. Re-read canonical upstream artifacts.
2. Extract design targets from approved problem IDs, behavior-gap model elements, invariants, risks, and accepted residual uncertainties.
3. Identify explicit constraints and prohibited changes.
4. Generate materially distinct mechanisms, not cosmetic variants.
5. For each option, define:
   - enforcement point;
   - state and contract changes;
   - transaction and concurrency semantics;
   - failure behavior;
   - compatibility and migration impact;
   - security and operational impact;
   - assumptions and unknowns;
   - rollback and verification strategy;
   - residual risks.
6. Create a coverage row for every option × required target.
7. Compare options using explicit criteria.
8. Produce a non-binding recommendation when evidence supports one.
9. If only one viable option remains, produce a dominance proof showing every considered alternative and why it is not viable.
10. Validate references, coverage, distinctness, and lifecycle gate.
11. Route to Solution Critique only when the package is complete.

## Meaningfully distinct option rule

Two options are materially distinct only when at least one of these differs in a behaviorally relevant way:

- enforcement boundary;
- source of truth;
- consistency guarantee;
- transaction boundary;
- concurrency control;
- compatibility strategy;
- migration strategy;
- failure semantics;
- operational ownership;
- residual risk profile.

Different class names, helper functions, libraries with equivalent behavior, or differently worded versions of the same mechanism are not distinct options.

## Single viable option rule

When fewer than two viable options exist, a dominance proof is mandatory. It must include:

- alternatives considered;
- evidence and constraints used to evaluate them;
- exact elimination reason for each alternative;
- why relaxing the constraint would change viability;
- residual risks of the surviving option;
- falsification conditions for the dominance conclusion.

“Best practice” is not a dominance proof.

## Gate routing

- `READY_FOR_SOLUTION_CRITIQUE`: options are traceable, materially distinct or supported by a valid dominance proof, coverage is complete, and no blocking evidence/model gap remains.
- `RETURN_TO_INVESTIGATION`: a material design decision cannot be evaluated without new evidence.
- `RETURN_TO_SYSTEM_MODEL`: the approved model lacks or contradicts a required design target.
- `BLOCKED`: package integrity or references are invalid.

## Completion invariants

- Every active option references existing problem, model, evidence, and invariant IDs.
- Every required design target has one coverage row per active option.
- At least one viable option fully addresses every required target.
- Every option exposes assumptions, risks, failure semantics, compatibility, migration, rollback, and verification.
- No decision record is `APPROVED` in this phase.
- Recommendation is explicitly non-binding.
- One viable option requires a valid dominance proof.
- The output gate and next state agree.

## Completion

A completed package means the human can critique concrete alternatives and understand exactly what each option addresses, leaves unresolved, assumes, changes, risks, and requires. It does not mean a solution has been selected.

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
