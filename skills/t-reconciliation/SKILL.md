---
name: t-reconciliation
description: Audit lane-required phase artifacts, review results, verification, and acceptance evidence before closure.
version: 2.3.0
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
