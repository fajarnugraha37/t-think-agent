---
name: t-verification
description: Execute independent command-driven verification after every required implementation review passes.
version: 2.4.0
lifecycle_state: VERIFICATION
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: VERIFICATION
  cost-profile: economy-compatible
---
# Verification

## Purpose

Execute independent command-driven verification after every required implementation review passes.

## Procedure

1. Bind to a passing implementation-review aggregate.
2. Execute every approved obligation exactly once.
3. Capture command, exit code, environment, and evidence.
4. Do not mutate source.
5. Route failures to the earliest owner.

## Non-negotiable rules

- Every obligation has one result.
- Ready status requires every result PASS and exit code zero.
- Review never replaces verification.

## Verification script and cleanup policy

- Prefer existing repository test commands and durable test-suite additions.
- When a behavior check would prevent a future regression, do not create a one-off script; route back to `BOUNDED_IMPLEMENTATION` so `t-builder` adds or updates a real test in an approved test target.
- A one-off diagnostic script is allowed only when it is not a reusable product test. It must be a declared generated output under `.t-think/<work-id>/scratch/`.
- Delete every one-off diagnostic before completing verification.
- Run `t-thinkctl.py audit-workdir --file .t-think/<work-id>/state.yaml`; verification may not recommend reconciliation while scratch is non-empty or stray files exist.
- Never place scripts directly in `.t-think/`, `.t-think/<work-id>/`, `artifacts/`, `evidence/`, or `results/`.

## Small-model execution contract

1. Load only this skill, work state, and explicit artifacts.
2. Fill templates using exact IDs and enums.
3. Never guess missing semantics; return `BLOCKED` or route upstream.
4. Run the validator before claiming completion.
5. Save raw logs as evidence and keep the handoff compact.

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
