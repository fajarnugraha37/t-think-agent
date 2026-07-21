# Per-item State Machine

`PENDING → IN_PROGRESS → COMPLETED` is the normal path. Failure paths are `FAILED`, `BLOCKED`, or `ROLLED_BACK`. Dependents cannot start until all hard dependencies are `COMPLETED`.
