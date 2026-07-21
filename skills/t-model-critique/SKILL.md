---
name: t-model-critique
description: Assess human critique of the system model, defend or route revisions with evidence, and obtain model acceptance.
version: 2.4.0
lifecycle_state: MODEL_CRITIQUE
previous_state: SYSTEM_MODEL
next_state: SOLUTION_DESIGN
input_schema: schemas/input.schema.json
output_schema: schemas/output.schema.json
critique_request_schema: schemas/critique-request.schema.json
assessment_schema: schemas/assessment.schema.json
revision_directive_schema: schemas/revision-directive.schema.json
evidence_request_schema: schemas/evidence-request.schema.json
canonical_artifacts:
  - artifacts/04b-model-critique-input.yaml
  - artifacts/04c-model-critique-assessments.jsonl
  - artifacts/04d-model-revision-directives.jsonl
  - artifacts/04e-model-critique-evidence-requests.jsonl
  - artifacts/04f-model-critique-report.md
  - artifacts/04g-model-critique-output.yaml
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: MODEL_CRITIQUE
  cost-profile: economy-compatible
---
# Model Critique Skill

## Mission

Evaluate human critiques of an evidence-backed system model without obedience bias. Preserve conclusions supported by stronger evidence, revise or retract weak conclusions, and request further investigation when the current evidence cannot resolve the critique.

This skill does not modify code, design a solution, or silently rewrite approved model artifacts.

## Required inputs

The phase may start only when the System Modeling output is `COMPLETE` with gate `READY_FOR_MODEL_CRITIQUE`, and the canonical model elements, relations, traceability matrix, and evidence ledger are available.

## Hard prohibitions

The critique agent must not:

1. accept a critique merely because it came from the human;
2. reject a critique without citing inspected model items and evidence;
3. promote a new human assertion to `FACT`;
4. use conversation memory as evidence;
5. silently mutate model artifacts;
6. propose implementation or solution choices;
7. hide contradictory evidence or alternative interpretations;
8. declare a critique resolved when required evidence is unavailable;
9. expose private chain-of-thought.

Expose structured rationale: reviewed evidence, model items, findings, alternatives, falsification conditions, limitations, and required action.

## Classification contract

Every critique must be classified exactly once as:

- `ACCEPTED` — the critique is supported and materially invalidates or corrects the model;
- `PARTIALLY_ACCEPTED` — part of the critique is supported, while another part is not;
- `REJECTED_WITH_EVIDENCE` — the current model is retained because stronger evidence contradicts the critique;
- `REQUIRES_INVESTIGATION` — current evidence cannot responsibly resolve the critique.

## Workflow

1. Re-read canonical source artifacts; never rely on compressed conversation context.
2. Validate every critique target against the actual model package.
3. Separate the human's observation, interpretation, requested outcome, and any unverified assertion.
4. Re-evaluate relevant evidence and model items.
5. Search for contradicting evidence and plausible alternative interpretations.
6. Classify the critique.
7. Create a revision directive when model changes are required. Directives are instructions for the System Modeling skill and must not be applied silently.
8. Create an evidence request when evidence is insufficient.
9. Calculate critique coverage and route the lifecycle.
10. Require explicit human approval before transition to `SOLUTION_DESIGN`.

## Gate routing

- `RETURN_TO_PROBLEM_ALIGNMENT`: business meaning or intended behavior is ambiguous.
- `RETURN_TO_INVESTIGATION`: blocking evidence request exists.
- `RETURN_TO_SYSTEM_MODEL`: critique assessment requires model revision but no new evidence is needed.
- `AWAITING_HUMAN_APPROVAL`: all critiques resolved and the current model needs no revision, but human approval is pending.
- `READY_FOR_CHANGE_OPTIONS`: all critiques resolved, no revision or evidence gap remains, and the human explicitly approved the model version.
- `BLOCKED`: references are invalid or critique processing cannot proceed safely.

## Invariants

- Every input critique has exactly one assessment.
- Every assessment references existing critique, evidence, and model IDs.
- `REJECTED_WITH_EVIDENCE` always includes supporting reviewed evidence and contradicting findings.
- `REQUIRES_INVESTIGATION` always maps to an open evidence request.
- Any `WEAKENED`, `REVISED`, or `RETRACTED` result maps to a revision directive.
- Revision directives are non-executable in this phase.
- Human approval authorizes progression; it does not change epistemic claim types.

## Completion

A successful critique phase does not mean every human critique was accepted. It means every critique was explicitly evaluated, evidence-backed, falsifiable, traceable, and routed to the correct next phase.

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
