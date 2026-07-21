# Solution Design Skill Package

A ready-to-run package for the `SOLUTION_DESIGN` phase of an evidence-gated AI engineering lifecycle.

## Included

- `SKILL.md` — operational skill definition.
- `schemas/` — JSON Schema contracts for all machine-readable artifacts.
- `templates/` — YAML, JSONL, CSV, and Markdown templates.
- `validators/validate.py` — structural, semantic, cross-file, and transition validator.
- `examples/` — valid multi-option, valid single-option, and invalid packages.
- `tests/` — automated validator tests.
- `orchestrator/transition-contract.yaml` — lifecycle integration contract.
- `docs/` — option distinctness, dominance, coverage, and decision rules.

## Requirements

```bash
python -m pip install -r validators/requirements.txt
```

## Validate an individual artifact

```bash
python validators/validate.py --kind option --file examples/valid-options.jsonl
python validators/validate.py --kind input --file examples/valid-input.yaml
python validators/validate.py --kind output --file examples/valid-output.yaml
```

## Validate the complete example package

```bash
make validate-example
```

## Require transition readiness

```bash
make validate-transition
```

## Run tests

```bash
make test
```

The validator returns exit code `0` for valid artifacts and `1` for invalid artifacts.
