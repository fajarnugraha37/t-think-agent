---
name: t-solution-critique
description: Assess solution critiques, record human selection and risk acceptance, and freeze the approved solution contract.
version: 2.3.1
lifecycle_state: SOLUTION_CRITIQUE
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: SOLUTION_CRITIQUE
  cost-profile: economy-compatible
---
# Solution Critique Skill

## Purpose
Evaluate human critique of solution options, coverage, assumptions, trade-offs, dominance proof, recommendation, risks, and decision records without blindly following the human or silently mutating approved upstream artifacts.

## Inputs
Use `schemas/input.schema.json`. The skill requires a transition-ready Solution Design package and at least one explicit human critique.

## Procedure
1. Bind to the exact Solution Design version and actual artifacts.
2. Resolve every critique target to an option, coverage row, decision record, dominance proof, or design output.
3. Re-read referenced evidence and affected solution artifacts.
4. Classify each critique as `ACCEPTED`, `PARTIALLY_ACCEPTED`, `REJECTED_WITH_EVIDENCE`, or `REQUIRES_INVESTIGATION`.
5. Provide structured rationale, alternatives, falsification conditions, and impact if wrong.
6. Produce revision directives instead of editing upstream solution artifacts.
7. Route evidence gaps, model defects, problem changes, and solution revisions to the earliest correct phase.
8. When review is resolved, require explicit human selection and risk/assumption acceptance.
9. Produce an immutable approved solution contract.
10. Transition only to `IMPLEMENTATION_PLAN`; do not plan or implement in this skill.

## Outputs
- critique assessments JSONL
- solution revision directives JSONL
- evidence requests JSONL
- human decision approval YAML
- approved solution contract YAML
- critique report Markdown
- lifecycle output YAML

## Non-negotiable rules
- Human critique is a claim to evaluate, not an automatic command.
- Rejection requires evidence.
- Accepted critique that changes solution semantics requires a revision directive and return to Solution Design.
- Only the human may approve the selected option.
- Approval authorizes planning only.
- `IMPLEMENTED` and code changes are outside this phase.

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
