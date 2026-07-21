---
name: t-bounded-implementation
description: Execute only human-authorized blueprint tasks within approved write targets.
version: 2.4.0
lifecycle_state: BOUNDED_IMPLEMENTATION
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: BOUNDED_IMPLEMENTATION
  cost-profile: economy-compatible
---
# Bounded Implementation

## Purpose

Execute only human-authorized blueprint tasks within approved write targets.

## Procedure

1. Validate authorization and source contract.
2. Execute tasks in dependency order.
3. Modify only approved targets.
4. Capture actual diff, commands, and evidence.
5. Stop and route upstream when a new semantic decision is required.

## Non-negotiable rules

- No unapproved source path.
- No silent task reinterpretation.
- No new semantic decision.
- Ready status requires every task completed.

## Small-model execution contract

1. Load only this skill, work state, and explicit artifacts.
2. Fill templates using exact IDs and enums.
3. Never guess missing semantics; return `BLOCKED` or route upstream.
4. Run the validator before claiming completion.
5. Save raw logs as evidence and keep the handoff compact.

## Test and temporary-file rule

Implement approved reusable behavior checks as real repository tests. Do not leave diagnostic scripts in `.t-think/`. If an authorized one-off diagnostic is unavoidable, place it only in the active work item's `scratch/` directory, record it as generated output, and remove it before completion.

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
