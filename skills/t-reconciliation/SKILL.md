---
name: t-reconciliation
description: Audit lane-required phase artifacts, review results, verification, and acceptance evidence before closure.
version: 2.3.1
lifecycle_state: RECONCILIATION
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: RECONCILIATION
  cost-profile: economy-compatible
---
# Reconciliation

## Purpose

Audit lane-required phase artifacts, review results, verification, and acceptance evidence before closure.

## Procedure

1. Load the selected lane path and phase waivers.
2. Bind every required phase artifact by digest.
3. Confirm implementation-review and verification readiness.
4. Map every acceptance criterion to evidence.
5. Reject unresolved blocking findings or missing phases.

## Non-negotiable rules

- No missing lane-required phase artifact.
- No unsatisfied acceptance criterion.
- No open blocking finding.
- Human final closure remains external.

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
- Use only the platform-specific resource root declared by the installed adapter: OpenCode may use its own native skill root, while Codex, Claude Code, and Cursor use the exact private path embedded during installation. Never search a shared discovery root or another platform's t-think resources. When an absolute path is unavoidable, join the declared root and relative identifier with the host path API; never concatenate path strings manually.
- If a required resource cannot be opened, return `BLOCKED` with reason `SKILL_RESOURCE_UNAVAILABLE`. Do not recreate a template from memory, infer its shape, or continue with an invented format.

Frequently required resources:

- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`validators/validate.py`](validators/validate.py)
<!-- END T-THINK PORTABLE RESOURCE CONTRACT -->
