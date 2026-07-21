---
name: t-reconciliation
description: Reconcile the complete lifecycle trace from problem through change and verification before human closure.
version: 1.0.0
lifecycle_state: RECONCILIATION
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: RECONCILIATION
  cost-profile: economy-compatible
---
# Reconciliation Skill

## Purpose
Reconcile the complete governed software-delivery evidence chain after independent verification. The skill proves that approved intent, investigated evidence, system model, selected solution, approved plan, atomic checklist, bounded implementation, reviews, and verification form one digest-bound and semantically closed chain.

## Preconditions
- Verification output is `READY_FOR_RECONCILIATION`.
- Verification result contract is `PASS` and its bundle digest matches.
- The bound repository tree has not changed.
- Canonical artifacts from every required lifecycle phase are available.
- An independent reconciler is assigned.

## Procedure
1. Bind to the exact Verification contract, repository tree, and upstream contract IDs.
2. Validate reconciler independence and competency.
3. Build a canonical artifact registry for every lifecycle phase.
4. Verify existence, readability, digest, lifecycle status, supersession, and canonical-role uniqueness.
5. Normalize semantic traceability nodes and evidence-backed links.
6. Prove every active problem, acceptance criterion, invariant, and risk reaches its required terminal change, test, review, and verification nodes.
7. Detect contradictions, gaps, source drift, status conflicts, and unauthorized semantic changes.
8. Route blocking defects to the earliest responsible lifecycle phase.
9. Produce an immutable reconciliation result contract.
10. Require explicit human closure approval before transitioning to `COMPLETED`.

## Outputs
- reconciler assignment YAML;
- artifact registry JSONL;
- traceability nodes JSONL;
- traceability links JSONL;
- closure obligations JSONL;
- contradictions JSONL;
- residual gaps JSONL;
- human closure approval YAML;
- immutable reconciliation result contract YAML;
- reconciliation report Markdown;
- lifecycle output YAML.

## Non-negotiable rules
- Digest integrity alone is not semantic closure.
- No source mutation or remediation during Reconciliation.
- No inferred link without rationale and evidence.
- No unresolved blocking contradiction or gap at completion.
- Every terminal-required root must have exact closure coverage.
- Human closure approval is mandatory for `COMPLETED`.
- Any new semantic decision requires lifecycle loopback.

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
