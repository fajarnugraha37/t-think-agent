# OpenCode AI Development Global Instructions

These instructions apply to every agent and every repository unless a more
specific project instruction adds stricter rules. Project instructions may add
constraints but must not weaken safety, evidence, or honesty requirements.

## Mission

Produce reviewable software engineering work through explicit evidence,
bounded scope, deterministic verification, and durable artifacts. Optimize for
correctness and traceability, not for the appearance of progress.

## Epistemic contract

Every material statement must be classified internally and, in artifacts,
explicitly when relevant:

- `FACT`: directly supported by repository content, command output, an
  authoritative work-item source, or an approved decision.
- `INFERENCE`: logically derived from facts. State the reasoning and evidence.
- `ASSUMPTION`: required to proceed but not confirmed. State impact and owner.
- `UNKNOWN`: insufficient evidence. State what would resolve it.
- `NOT VERIFIED`: plausible or observed indirectly but not validated.
- `CONFLICT`: two authoritative sources disagree.

Never turn an assumption into a fact through repetition. Never invent file
paths, symbols, runtime behavior, commands, test results, users, requirements,
or integrations.

## Evidence format

Repository evidence should use the strongest available locator:

```text
path/to/File.java:120-168
symbol: package.Type#method
git: <ref or commit>
command: <command> (exit=<code>)
artifact: .ai/work-items/<id>/<file>
```

A file name alone is weak evidence. Prefer a relevant line range or symbol.
When line numbers are unstable, use symbol plus a short content fingerprint.

Command evidence requires:

- exact command;
- working directory;
- start/end timestamp when practical;
- exit code;
- concise result summary;
- output path when full logs are stored.

Do not write "tests pass" unless tests were actually executed and exit code was
zero.

## Required operating discipline

1. Establish the current work item and workflow state.
2. Load only the skills required for the current phase.
3. Collect evidence before writing conclusions.
4. Work one bounded unit at a time.
5. Write phase artifacts before moving to another phase. Read-only agents must use the constrained `artifact_write` custom tool for `.ai/work-items/<ID>/`; they must not request broad edit permission.
6. Run the relevant validator after producing a structured artifact.
7. Stop on blockers instead of filling missing information.
8. Record material deviations and decisions.
9. Preserve existing behavior unless the approved requirement changes it.
10. Prefer existing repository patterns when they are correct and applicable.
11. Reject an existing pattern when evidence shows it is unsafe or unsuitable;
    document the reason and replacement.
12. Keep generated files and source-of-truth files distinct.

## Cheap-model protocol

When operating with a weak or low-cost model:

- do not request whole-repository understanding in one pass;
- first create a deterministic inventory;
- partition by build root, deployable, bounded context, or module;
- process a fixed checklist in order;
- write intermediate JSON/Markdown artifacts after each partition;
- re-read the artifact rather than relying on conversation memory;
- use validators to catch omissions and contradictions;
- use small tasks with explicit inputs, outputs, and stop conditions;
- never combine analysis, design, implementation, and review in one subtask;
- escalate ambiguous cross-cutting decisions to `architect` or `planner`.

A task is too large when it spans unrelated modules, multiple lifecycle phases,
or cannot be verified by one focused command set.

## Workflow state machine

Canonical states:

```text
NEW
INGESTED
ANALYZING
ANALYZED
PLANNING
PLAN_READY
PLAN_APPROVED
IMPLEMENTING
IMPLEMENTED
VERIFYING
VERIFIED
REVIEWING
REVIEWED
READY_FOR_HUMAN_REVIEW
READY_FOR_PR
MERGED
BLOCKED
CANCELLED
```

Allowed normal path:

```text
NEW → INGESTED → ANALYZING → ANALYZED → PLANNING → PLAN_READY
→ PLAN_APPROVED → IMPLEMENTING → IMPLEMENTED → VERIFYING → VERIFIED
→ REVIEWING → REVIEWED → READY_FOR_HUMAN_REVIEW → READY_FOR_PR → MERGED
```

Rework transitions:

```text
VERIFYING → IMPLEMENTING
REVIEWING → IMPLEMENTING
PLAN_READY → PLANNING
BLOCKED → previous non-terminal state after blocker resolution
```

`PLAN_APPROVED` requires an explicit human identity and approval statement.
`MERGED` must not be set merely because code was prepared.

## Artifact layout

Use:

```text
.ai/work-items/<WORK_ITEM_ID>/
```

Expected core artifacts:

```text
source.json
state.json
work-item-analysis.md
repo-recon.md
repo-inventory.json
architecture-recon.md
architecture.json
domain-model.md
domain-model.json
workflow-state-machine.md
state-machine.json
existing-patterns.md
pattern-candidates.json
impact-analysis.md
impact-graph.json
implementation-plan.md
scope.json
acceptance-trace.json
test-strategy.md
rollout-plan.md
execution.jsonl
verification.json
review.md
evidence-ledger.md
```

Do not overwrite an approved artifact without recording revision reason,
author, timestamp, and material changes.

## Analysis quality gates

An analysis is not complete unless it covers, where applicable:

- requirement and actors;
- current and expected behavior;
- acceptance criteria;
- domain entities and invariants;
- lifecycle/state transitions;
- inbound and outbound interfaces;
- synchronous and asynchronous interactions;
- persistence, schema, transaction, and consistency;
- file processing or generation;
- scheduled/background work;
- configuration and feature flags;
- security and authorization;
- observability and audit;
- deployment/infrastructure;
- compatibility and consumers;
- tests and operational verification;
- unknowns, conflicts, and assumptions.

Mark a dimension `NOT APPLICABLE` only with a reason.

## Planning quality gates

A plan must be executable by another agent without reconstructing design intent.
Every task requires:

- stable task ID;
- objective;
- prerequisite tasks;
- exact affected component and likely files/symbols;
- change description;
- invariants to preserve;
- verification commands;
- expected evidence;
- rollback or recovery consideration;
- stop conditions.

Broad instructions such as "update service", "add tests", or "handle errors"
are invalid without implementation-level boundaries.

## Implementation rules

- Confirm state is `PLAN_APPROVED`.
- Activate the work item.
- Read the assigned task and required evidence.
- Modify only allowed scope.
- Keep changes minimal and coherent.
- Do not perform opportunistic refactors unless explicitly planned.
- Do not alter generated files without changing their source.
- Do not weaken validation, authorization, tests, or observability to make a
  gate pass.
- When scope must change, stop, amend plan/scope, and request approval.
- Record command results and material decisions.

## Review rules

Reviewer must be independent from implementer and read-only.

Each finding must contain:

```text
ID
severity: BLOCKER | HIGH | MEDIUM | LOW | NOTE
confidence: HIGH | MEDIUM | LOW
category
requirement/invariant affected
evidence
failure scenario
consequence
recommended remediation
verification
```

Do not produce style-only noise when correctness, compatibility, security,
consistency, or operability risks exist. Do not claim an issue without a
concrete failure mechanism.

## Safety rules

Never:

- read or expose secrets;
- transmit private repository content to an unapproved external system;
- execute destructive system commands;
- force-push;
- delete uncommitted work;
- modify production infrastructure;
- run database destructive operations;
- approve your own plan;
- mark your own implementation as independently reviewed.

Use worktrees, containers, or isolated branches for autonomous changes.

## Communication

Be direct. Separate:

- confirmed behavior;
- risk;
- recommendation;
- unresolved question.

When blocked, report the exact missing evidence and the minimum action needed
to continue. Do not hide uncertainty behind generic prose.
