---
name: t-checklist-critique
description: Assess checklist critiques, obtain human approval and execution authorization, and freeze the checklist contract.
version: 1.0.0
lifecycle_state: CHECKLIST_CRITIQUE
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: CHECKLIST_CRITIQUE
  cost-profile: economy-compatible
---
# Checklist Critique Skill

## Purpose
Evaluate human critique of an atomic implementation checklist without blindly following the reviewer, silently mutating checklist artifacts, authorizing unbounded work, making new semantic decisions, or executing implementation.

## Required inputs
Use `schemas/input.schema.json`. The source Checklist Builder package must be transition-ready and bound to an approved implementation plan. At least one explicit human critique is required.

## Procedure
1. Bind to the exact builder run, plan contract, repository commit, artifact version, and checklist bundle.
2. Resolve every critique target to an actual checklist item, dependency, coverage row, execution batch, guard, or source binding.
3. Re-read the relevant checklist artifacts, approved plan contract, evidence, model, and source mappings.
4. Classify each critique as `ACCEPTED`, `PARTIALLY_ACCEPTED`, `REJECTED_WITH_EVIDENCE`, or `REQUIRES_INVESTIGATION`.
5. Record rationale, alternatives, limitations, falsification conditions, and evidence.
6. Produce revision directives instead of silently editing checklist artifacts.
7. Route evidence gaps and upstream defects to the earliest correct lifecycle phase.
8. Require explicit human approval and execution authorization.
9. Freeze an immutable approved checklist contract with exact digests, IDs, order, parallel levels, human gates, and operation bindings.
10. Transition only to `BOUNDED_IMPLEMENTATION`; do not implement code in this phase.

## Outputs
- critique assessments JSONL;
- checklist revision directives JSONL;
- evidence requests JSONL;
- human checklist approval YAML;
- approved checklist contract YAML;
- checklist critique report Markdown;
- lifecycle output YAML.

## Non-negotiable rules
- Human critique is a claim to evaluate, not an automatic command.
- Rejection requires evidence and contradicting findings.
- Accepted critique that changes artifacts creates a directive and loopback.
- New semantic decisions route upstream; they are never made here.
- Only a human may approve and authorize execution.
- Approved checklist artifacts are immutable; any change requires versioning and re-approval.
- No code, test, database, configuration, deployment, or runtime mutation is allowed.
- Ambiguity during later execution must become `IMPLEMENTATION_FAILED`, never a guess.

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
