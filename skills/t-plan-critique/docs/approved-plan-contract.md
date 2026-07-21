# Approved plan contract

The approved plan contract freezes the exact planning targets, plan items, dependency graph, verification plan, rollback plan, execution order, change surface, discretion envelope, and remediation failure budget.

`plan_bundle_digest` is computed over canonical JSON representations of all source planning artifacts. A mismatch invalidates approval and prevents checklist construction.
