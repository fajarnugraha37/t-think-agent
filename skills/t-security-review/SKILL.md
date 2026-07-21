---
name: t-security-review
description: Dedicated security review covering trust boundaries, validation, data exposure, dependencies, and fail-open behavior.
version: 2.4.0
lifecycle_state: IMPLEMENTATION_REVIEW
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: IMPLEMENTATION_REVIEW
  cost-profile: economy-compatible
---
# Security Review

## Purpose

Dedicated security review covering trust boundaries, validation, data exposure, dependencies, and fail-open behavior.

## Procedure

1. Bind to exact implementation, diff, boundary report, and approved artifacts.
2. Execute every required category exactly once in a fresh context.
3. Record evidence-backed checks and findings.
4. Never edit source.
5. Return a track result to `t-think`; do not advance lifecycle state.

## Non-negotiable rules

- Every required category is checked exactly once.
- A material failure blocks aggregate review.
- `NOT_APPLICABLE` requires evidence and is allowed only where policy permits.

## Small-model execution contract

1. Load only this skill, work state, and explicitly referenced artifacts.
2. Use templates and exact enums before prose.
3. Record missing semantics as `BLOCKED`; never guess.
4. Run the validator before returning a result.
5. Save large logs as evidence and return compact references.
6. Never make a decision owned by another phase.

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
