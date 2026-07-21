# Reconciliation Skill Package

A ready-to-use governance skill for the final reconciliation phase of an evidence-gated AI software-engineering lifecycle.

## Validate the transition-ready example

```bash
make validate
```

## Run tests

```bash
make test
```

## Important artifacts
- `SKILL.md`: normative process.
- `schemas/`: machine-readable contracts.
- `templates/`: reusable authoring templates.
- `examples/`: success, loopback, and invalid fixtures.
- `validators/validate.py`: structural and cross-artifact validator.
- `orchestrator/transition-contract.yaml`: lifecycle integration.
