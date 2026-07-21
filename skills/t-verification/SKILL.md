---
name: t-verification
description: Execute independent command-driven verification after every required implementation review passes.
version: 2.3.0
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

## Small-model execution contract

1. Load only this skill, work state, and explicit artifacts.
2. Fill templates using exact IDs and enums.
3. Never guess missing semantics; return `BLOCKED` or route upstream.
4. Run the validator before claiming completion.
5. Save raw logs as evidence and keep the handoff compact.
