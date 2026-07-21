# Traceability and Coverage

Required chain:

`approved plan contract → PLN operation → CHK item → evidence/model/invariant → TST verification → RBK rollback → completion evidence`

Every numbered plan operation must have exactly one `FULL` coverage row and exactly one active checklist item. Checklist unions must preserve the approved plan item set, verification set, rollback set, and change surface.
