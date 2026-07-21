# Technical Review Skill Package

Validator-backed independent technical review for a completed, self-reviewed bounded implementation.

## Quick validation

```bash
python3 validators/validate.py --kind schema
make validate
make test
```

## Transition-ready validation

```bash
make validate-ready
```

The package validates source bindings, reviewer independence, mandatory review dimensions, one-to-one change coverage, evidence challenges, finding/directive routing, immutable result contracts, and lifecycle transitions.
