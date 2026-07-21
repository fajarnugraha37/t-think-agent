---
name: t-implementation-review
description: Aggregate mandatory fresh review tracks according to the selected governance lane.
version: 2.5.0
lifecycle_state: IMPLEMENTATION_REVIEW
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: IMPLEMENTATION_REVIEW
  cost-profile: economy-compatible
---
# Implementation Review

## Purpose

Aggregate mandatory fresh review tracks according to the selected governance lane.

## Procedure

1. Determine required component tracks from the selected governance lane.
2. Validate every track artifact, agent/skill binding, status, and fresh invocation identity.
3. Reject missing, duplicated, drifted, or failed required tracks.
4. Create one immutable aggregate artifact without rewriting component results.
5. Only `t-think` may advance lifecycle state after aggregation.

## Non-negotiable rules

- Component tracks remain separately auditable.
- Every required track uses a distinct fresh invocation.
- One material track failure blocks the phase.
- Missing tracks are never inferred or waived silently.

## Small-model execution contract

1. Load only this skill, lane policy, work state, and component results.
2. Use exact track IDs and statuses.
3. Run the validator before transition.
4. Record `BLOCKED` rather than guessing missing results.

<!-- BEGIN T-THINK PORTABLE RESOURCE CONTRACT -->
## Portable resource contract

- Resolve every bundled resource relative to the directory containing this `SKILL.md`.
- Read the generated [resource index](RESOURCE_INDEX.md) before opening templates, schemas, validators, examples, or supporting documentation.
- Treat linked `/`-separated paths as portable relative resource identifiers. Never construct a global path with `~`, `$HOME`, `%USERPROFILE%`, a drive letter, or backslashes.
- Use only the platform-specific resource root declared by the installed adapter: OpenCode may use its own native skill root, while Codex, Claude Code, and Cursor use the exact private path embedded during installation. Never search a shared discovery root or another platform's t-think resources. When an absolute path is unavoidable, join the declared root and relative identifier with the host path API; never concatenate path strings manually.
- If a required resource cannot be opened, return `BLOCKED` with reason `SKILL_RESOURCE_UNAVAILABLE`. Do not recreate a template from memory, infer its shape, or continue with an invented format.

Frequently required resources:

- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`validators/validate.py`](validators/validate.py)
<!-- END T-THINK PORTABLE RESOURCE CONTRACT -->
