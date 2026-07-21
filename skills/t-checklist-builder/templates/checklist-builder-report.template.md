# Checklist Builder Report

## Source binding
- Approved plan contract: `PLANCON-...`
- Planning run: `IPLAN-...`
- Repository commit: `...`
- Plan bundle digest: `sha256:...`

## Atomic checklist summary
Document item counts, exact operation coverage, action types, human gates, and any blocked items.

## Traceability
For every checklist item, show: approved plan operation → checklist item → evidence/model → verification → rollback.

## Dependency and execution analysis
Record roots, leaves, deterministic topological order, safe parallel levels, and explicit human gates.

## Semantic guard
State whether any new semantic decision, scope expansion, or silent replanning was detected.

## Findings and routing
List findings with evidence and route each blocking issue to the earliest responsible phase.

## Gate decision
State whether the exact checklist bundle is ready for `CHECKLIST_CRITIQUE`.
