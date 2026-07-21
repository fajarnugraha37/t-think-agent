---
name: t-bounded-implementation
description: Execute only the approved checklist, capture changes and commands, and stop on ambiguity or semantic drift.
version: 1.0.0
lifecycle_state: BOUNDED_IMPLEMENTATION
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: BOUNDED_IMPLEMENTATION
  cost-profile: economy-compatible
---
# Bounded Implementation Skill

## Purpose
Execute only an immutable, human-approved checklist contract while preserving scope, order, dependencies, human gates, semantic boundaries, failure behavior, and evidence traceability.

## Preconditions
- Source Checklist Critique output is `READY_FOR_BOUNDED_IMPLEMENTATION`.
- Approved checklist contract status is `APPROVED` and execution is human-authorized.
- Repository baseline matches the bound commit.
- Checklist bundle digest, operation bindings, decision envelope, failure budget, and human gates are unchanged.

## Procedure
1. Bind to the exact approved checklist contract and baseline repository state.
2. Revalidate checklist item digests, source operation digests, order, dependencies, batches, and human gates.
3. Execute checklist items only in validated topological order or approved parallel levels.
4. Before each item, record precondition checks and any required human authorization.
5. Capture every actual change, command, output digest, verification result, and repository state.
6. Exercise only mechanical discretion explicitly allowed by the decision envelope.
7. Stop immediately on ambiguity, source drift, scope expansion, missing human gate, or a new semantic decision.
8. Use remediation attempts only for mechanical failures and never beyond the approved failure budget.
9. Invoke rollback only when mapped and record its exact outcome.
10. Produce an immutable implementation result contract for Self Review.

## Outputs
- execution records JSONL;
- change records JSONL;
- command results JSONL;
- verification results JSONL;
- rollback results JSONL;
- implementation findings JSONL;
- repository-before and repository-after YAML;
- implementation result contract YAML;
- implementation report Markdown;
- lifecycle output YAML.

## Non-negotiable rules
- No silent replanning.
- No new semantic decision.
- No unapproved file, component, migration, deployment, or runtime mutation.
- No execution of a human-gated batch without explicit human authorization.
- No fabricated command output, diff, test result, or repository hash.
- Ambiguity is `IMPLEMENTATION_FAILED`, never a guess.
- A failed item blocks dependent items.
- A transition to Self Review requires every checklist item completed and every required verification passed.

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
