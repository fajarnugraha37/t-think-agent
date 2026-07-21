---
name: t-implementation-review
description: Aggregate mandatory fresh review tracks according to the selected governance lane.
version: 2.3.0
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
