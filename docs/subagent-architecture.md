# Subagent architecture

`t-think` is the only control-plane orchestrator. Eight role subagents execute phase work in fresh contexts. The topology is star-shaped and delegation depth is one.

```text
human ↔ t-think → exactly one authorized role worker → structured result → t-think
```

## Why eight roles rather than fifteen phase agents

Roles provide stable identity, permission, context, and independence boundaries. Fifteen `t-*` skills provide the phase-specific procedures, schemas, templates, and transition rules. This avoids duplicating authority definitions and prevents all lifecycle instructions from entering every context.

## Role allocation

- `t-investigator`: direct evidence and actual-system facts;
- `t-modeler`: current/intended models and solution options;
- `t-planner`: ordered plans and atomic checklists;
- `t-critic`: fresh-context critique of producer artifacts;
- `t-builder`: the sole source writer during authorized implementation, then fresh-invocation self-review without writes;
- `t-reviewer`: independent read-only technical review;
- `t-verifier`: reproducible tests and falsification with generated outputs only;
- `t-reconciler`: final traceability and unresolved-finding audit.

## Invocation boundary

Every delegation packet contains:

- work, run, and invocation identity;
- exact phase, role, and skill;
- objective and completion criteria;
- workspace discovery policy;
- write mode and approved targets;
- protected paths and outside-workspace policy;
- digest-bound artifact inputs;
- output paths and schemas;
- explicit stop conditions.

The worker returns a phase artifact, result envelope, activity record, and boundary report. Only `t-think` may transition lifecycle state.

## Independence

Critique, technical review, verification, reconciliation, and builder self-review use fresh invocations. Reviewers receive approved artifacts, actual diffs, tests, and producer reports, but not private producer reasoning. A distinct invocation alone is insufficient: the permission and artifact boundary must also be validated.

## Parallelism

The economy profile is fully sequential. Other profiles may parallelize independent read-only investigation, review, or verification shards. Multiple source writers, shared-environment mutation, lifecycle transitions, human gates, migrations, and reconciliation are never parallelized.
