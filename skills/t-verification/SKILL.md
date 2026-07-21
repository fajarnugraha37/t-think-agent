---
name: t-verification
description: Execute reproducible verification obligations, falsification attempts, and evidence capture independently.
version: 1.0.0
lifecycle_state: VERIFICATION
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: VERIFICATION
  cost-profile: economy-compatible
---
# Verification Skill

## Purpose
Independently verify a technically reviewed bounded implementation against exact approved obligations, invariants, acceptance criteria, and runtime evidence before reconciliation.

## Preconditions
- Technical Review output is `READY_FOR_VERIFICATION`.
- Technical Review result contract is `PASS` and its bundle digest matches.
- Implementation result, approved checklist, repository tree, and source verification records remain unchanged.
- An independent verifier and reproducible environment are available.

## Procedure
1. Bind to exact upstream contracts, digests, and repository tree.
2. Validate verifier independence and competency.
3. Capture a reproducible environment fingerprint.
4. Normalize every upstream `TST-*` item into exactly one `VOB-*` obligation.
5. Execute every mandatory obligation and capture digest-addressed evidence.
6. Attempt falsification for every high-risk or critical obligation.
7. Confirm the repository tree did not change.
8. Record evidence-backed findings for failures, blockers, inconclusive results, source drift, and refuted falsification.
9. Create unapplied remediation directives and route to the earliest responsible phase.
10. Produce an immutable verification result contract.
11. Transition to Reconciliation only when coverage is exact, all mandatory obligations pass, falsification requirements are met, evidence is complete, and no blocking finding remains.

## Outputs
- verifier assignment YAML;
- environment fingerprint YAML;
- verification obligations JSONL;
- verification executions JSONL;
- falsification attempts JSONL;
- verification evidence JSONL;
- findings JSONL;
- unapplied remediation directives JSONL;
- immutable verification result contract YAML;
- verification report Markdown;
- lifecycle output YAML.

## Non-negotiable rules
- No code, configuration, migration, test, or deployment mutation in Verification.
- No weakening or reinterpretation of approved acceptance criteria.
- No result without evidence.
- No high-risk claim without a falsification attempt.
- No source drift.
- Failed, blocked, or inconclusive material results require findings.
- Remediation directives remain unapplied.

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
