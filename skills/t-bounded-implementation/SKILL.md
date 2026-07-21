---
name: t-bounded-implementation
description: Execute only human-authorized blueprint tasks within approved write targets.
version: 2.3.0
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
