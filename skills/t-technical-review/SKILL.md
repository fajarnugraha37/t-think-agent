---
name: t-technical-review
description: Perform an independent technical review with per-change assessment and evidence challenges.
version: 1.0.0
lifecycle_state: TECHNICAL_REVIEW
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: TECHNICAL_REVIEW
  cost-profile: economy-compatible
---
# Technical Review Skill

## Purpose
Perform an independent, evidence-backed technical review of a self-reviewed bounded implementation before verification. This phase challenges prior conclusions, reviews the actual change bundle, and never edits implementation artifacts.

## Preconditions
- Self Review output is `READY_FOR_TECHNICAL_REVIEW`.
- Self Review result contract is `PASS` and its bundle digest matches.
- Bounded implementation, approved checklist, repository tree, and source evidence remain unchanged.
- An independent reviewer is assigned and is distinct from both the implementation author and self-reviewer.

## Procedure
1. Bind to exact self-review, implementation, checklist, and repository artifacts.
2. Validate reviewer independence and competency coverage.
3. Inspect actual diff/change evidence rather than relying on summaries.
4. Execute every mandatory technical dimension.
5. Assess every change record exactly once against its checklist item and self-review conformance result.
6. Challenge at least one prior claim through replay, counterexample, boundary analysis, alternative explanation, or provenance inspection.
7. Record evidence-backed findings for every failure, disagreement, or inconclusive material issue.
8. Create unapplied remediation directives and route defects to the earliest responsible lifecycle phase.
9. Produce an immutable technical-review result contract.
10. Transition to Verification only when all mandatory dimensions pass or are justified as not applicable, every change is approved, evidence challenges are complete, and no blocking finding remains.

## Outputs
- reviewer assignment YAML;
- technical review checks JSONL;
- change assessments JSONL;
- evidence challenges JSONL;
- findings JSONL;
- unapplied remediation directives JSONL;
- technical-review result contract YAML;
- review report Markdown;
- lifecycle output YAML.

## Non-negotiable rules
- Reviewer must be independent from implementation and self-review identities.
- No rubber-stamp review and no conclusion copied without independent reasoning.
- No code, configuration, migration, test, or deployment mutation in this phase.
- No finding without evidence.
- Every source change must be assessed exactly once.
- A refuted or inconclusive evidence challenge requires a finding.
- New semantic decisions route upstream and are never resolved in Technical Review.

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
