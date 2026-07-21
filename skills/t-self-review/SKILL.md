---
name: t-self-review
description: Audit the implementation against the checklist and evidence without fixing code during review.
version: 1.0.0
lifecycle_state: SELF_REVIEW
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: SELF_REVIEW
  cost-profile: economy-compatible
---
# Self Review Skill

## Purpose
Perform an evidence-backed second-pass review of a completed bounded implementation before independent technical review. This phase audits the actual change bundle against the immutable approved checklist and never edits code.

## Preconditions
- Bounded Implementation output is `READY_FOR_SELF_REVIEW`.
- Implementation result contract is `COMPLETE`.
- Repository-after state and implementation bundle digest match the bound artifacts.
- Approved checklist contract and checklist items remain unchanged.

## Procedure
1. Bind to the exact implementation result contract, approved checklist, repository-after state, and captured evidence bundle.
2. Verify every source artifact digest and inspect its content rather than trusting summaries.
3. Review every checklist item against its execution, changes, commands, verification, rollback mapping, and actual diff evidence.
4. Execute all mandatory review dimensions: correctness, conformance, scope, semantics, order, human gates, error handling, security, data integrity, concurrency, compatibility, migration, observability, test adequacy, rollback, and maintainability.
5. Label each conclusion with evidence and distinguish FACT from INFERENCE.
6. Create findings for every failure, gap, or inconclusive material issue.
7. Create unapplied remediation directives for findings that require changes. Never modify implementation artifacts in this phase.
8. Route mechanical implementation defects to Bounded Implementation and structural/semantic defects to the earliest responsible lifecycle phase.
9. Produce an immutable self-review result contract.
10. Transition to Technical Review only when coverage is complete, every mandatory check passes or is justified as not applicable, every checklist item conforms, and no blocking finding remains.

## Outputs
- review checks JSONL;
- checklist conformance results JSONL;
- evidence audits JSONL;
- review findings JSONL;
- unapplied remediation directives JSONL;
- self-review result contract YAML;
- self-review report Markdown;
- lifecycle output YAML.

## Non-negotiable rules
- No code, configuration, migration, deployment, or test mutation during self-review.
- No silent remediation and no silent checklist reinterpretation.
- No finding without evidence.
- No `PASS` based only on the implementation summary; inspect underlying records and diff evidence.
- A failed mandatory dimension or checklist conformance blocks Technical Review.
- A new semantic decision routes upstream; it is never resolved inside Self Review.
- `NOT_APPLICABLE` requires evidence-backed reasoning.

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
