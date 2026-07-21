---
name: t-system-modeling
description: Build an evidence-backed structural, behavioral, boundary, invariant, actual/intended, and gap model.
version: 1.0.0
lifecycle_state: SYSTEM_MODEL
previous_state: INVESTIGATION
next_state: MODEL_CRITIQUE
input_schema: schemas/input.schema.json
output_schema: schemas/output.schema.json
model_element_schema: schemas/model-element.schema.json
model_relation_schema: schemas/model-relation.schema.json
traceability_schema: schemas/traceability-row.schema.json
critique_schema: schemas/critique.schema.json
consistency_schema: schemas/consistency-decision.schema.json
canonical_artifacts:
  - artifacts/03-system-model.md
  - artifacts/03a-model-elements.jsonl
  - artifacts/03b-model-relations.jsonl
  - artifacts/03c-system-model.mmd
  - artifacts/04-traceability-matrix.csv
  - artifacts/04a-system-model-output.yaml
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: SYSTEM_MODEL
  cost-profile: economy-compatible
---
# System Modeling Skill

## 1. Mission

Construct an explicit, falsifiable, evidence-backed model of the relevant actual system and compare it with the approved intended behavior.

This skill explains the system. It does not select a solution, create an implementation plan, or modify code.

The model must make visible:

- actors and entry points;
- components and ownership;
- execution, state, and data flow;
- transaction, concurrency, retry, security, and failure boundaries where relevant;
- source of truth and external dependencies;
- actual behavior;
- intended behavior;
- invariants;
- the gap between actual and intended behavior;
- model limitations, conflicts, assumptions, unknowns, and falsification conditions.

## 2. Required inputs

The phase may start only when:

1. problem alignment is approved;
2. investigation status is `COMPLETE`;
3. investigation gate is `READY_FOR_SYSTEM_MODEL`;
4. the actual evidence ledger is available;
5. repository and commit scope are recorded.

Input must validate against `schemas/input.schema.json`.

## 3. Hard prohibitions

The modeling agent must not:

1. use conversation context as system evidence;
2. invent code paths, components, runtime behavior, constraints, or contracts;
3. promote an inference to fact;
4. hide assumptions inside model prose;
5. treat generated model artifacts as independent evidence;
6. claim code is active merely because it exists;
7. claim an absence beyond the inspected search scope;
8. propose fixes, designs, implementation steps, or preferred technologies;
9. silently omit contradicting evidence;
10. advance while blocking unknowns or conflicts remain;
11. produce relations with missing endpoints;
12. produce active model elements without evidence;
13. expose private chain-of-thought.

The agent must expose structured rationale: premises, evidence IDs, transformation summary, alternatives, falsification conditions, and limitations.

## 4. Epistemic discipline

Each material model element must declare:

- `FACT_BACKED`;
- `INFERENCE_BACKED`;
- `ASSUMPTION_BACKED`; or
- `MIXED`.

Inference-backed or mixed elements must include:

- supporting evidence;
- explicit reasoning summary;
- alternative explanations;
- falsification conditions;
- confidence;
- limitations.

Assumption-backed elements must cite explicit `ASM-...` records. A transition-ready model may only retain non-blocking assumptions that are declared in `reasoning_disclosure.assumption_usage`.

## 5. Workflow

### Step 1 — Re-read canonical inputs

Read the approved problem artifact, investigation output, and evidence ledger from their canonical files. Do not rely on conversation memory.

### Step 2 — Freeze model scope

Record repositories, branches, commits, modules, environments, included scope, excluded scope, and limitations.

### Step 3 — Decompose model objectives

Map every approved problem element and success criterion to required model dimensions.

### Step 4 — Build atomic model elements

Create records using `schemas/model-element.schema.json`.

Use stable IDs: `MDL-001`, `MDL-002`, and so on.

Prefer atomic elements. Do not combine a component, transaction, actual behavior, and invariant into one element.

### Step 5 — Build evidence-backed relations

Create directed relations using `schemas/model-relation.schema.json`.

Use stable IDs: `REL-001`, `REL-002`, and so on.

Every relation must:

- reference existing endpoints;
- reference actual evidence;
- state confidence;
- expose reasoning when not directly established.

### Step 6 — Model actual behavior

Represent what the inspected system does or can do. Preserve all uncertainty and scope limitations.

### Step 7 — Model intended behavior

Represent only human-approved behavior and evidence-backed contracts or invariant candidates. Do not infer hidden business intent.

### Step 8 — Formalize invariants

For each material invariant, record:

- invariant statement;
- scope;
- candidate enforcement points;
- consequence if violated;
- hardness (`HARD`, `SOFT`, or `UNKNOWN`).

### Step 9 — Model the behavior gap

A `BEHAVIOR_GAP` element must explicitly reference active `ACTUAL_BEHAVIOR` and `INTENDED_BEHAVIOR` elements.

### Step 10 — Create traceability

Populate `artifacts/04-traceability-matrix.csv`.

Every approved problem element must map to:

```text
problem → evidence → model elements → model relations
```

### Step 11 — Perform consistency checks

Check:

- all IDs are unique;
- all evidence IDs exist;
- all relation endpoints exist;
- all active elements have evidence;
- actual, intended, and gap elements are mutually consistent;
- required dimensions are covered;
- all problem elements are fully covered or explicitly out of scope;
- no blocking unknown or conflict remains;
- no solution proposal has leaked into the model.

### Step 12 — Decide the gate

Use one of:

- `READY_FOR_MODEL_CRITIQUE`;
- `MODEL_INCOMPLETE`;
- `BLOCKED`.

Do not mark the model ready merely because documentation exists.

## 6. Canonical outputs

```text
artifacts/03-system-model.md
artifacts/03a-model-elements.jsonl
artifacts/03b-model-relations.jsonl
artifacts/03c-system-model.mmd
artifacts/04-traceability-matrix.csv
artifacts/04a-system-model-output.yaml
```

## 7. Transition gate

Transition to `MODEL_CRITIQUE` is allowed only when:

- output metadata is `COMPLETE`;
- consistency status is `CONSISTENT`;
- required problem coverage is complete;
- required dimensions are covered or justified not applicable;
- relation integrity passes;
- evidence mapping is complete;
- actual, intended, and gap elements are present and consistent;
- blocking unknowns and conflicts are empty;
- all retained assumptions are explicit and non-blocking;
- the complete package passes the validator with `--require-transition-ready`.

## 8. Loopback rules

Return to:

- `INVESTIGATION` when evidence is missing or contradictory;
- `PROBLEM_ALIGNMENT` when intended behavior or business meaning is ambiguous;
- `SYSTEM_MODEL` when the evidence is sufficient but the model is incomplete or inconsistent.

## 9. Critique behavior

For every human critique, classify it as:

- `ACCEPTED`;
- `PARTIALLY_ACCEPTED`;
- `REJECTED_WITH_EVIDENCE`;
- `REQUIRES_INVESTIGATION`.

The agent must not agree automatically. It must compare the critique with evidence, revise when wrong, and retain a conclusion when stronger evidence supports it.

## 10. Completion statement

A successful phase result explains the relevant system within explicit evidence boundaries. It does not claim that the explanation is globally complete beyond the recorded scope.

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
