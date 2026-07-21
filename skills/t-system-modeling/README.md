# System Modeling Skill Package

A ready-to-use evidence-gated `SYSTEM_MODEL` phase package for an AI software-engineering lifecycle.

## Included

- `SKILL.md` — operating rules and lifecycle gate.
- `schemas/` — JSON Schema for input, output, model elements, relations, traceability rows, critiques, and consistency decisions.
- `templates/` — YAML, JSONL, CSV, Markdown, and Mermaid templates.
- `validators/` — structural, semantic, cross-file, and transition-ready validation.
- `examples/` — valid and intentionally invalid packages.
- `tests/` — automated regression tests.
- `orchestrator/transition-contract.yaml` — state transition contract.

## Requirements

```bash
python3 -m pip install -r validators/requirements.txt
```

## Validate individual files

```bash
python3 validators/validate.py --kind input \
  --file examples/valid-input.yaml

python3 validators/validate.py --kind element \
  --file examples/valid-model-elements.jsonl

python3 validators/validate.py --kind relation \
  --file examples/valid-model-relations.jsonl

python3 validators/validate.py --kind traceability \
  --file examples/valid-traceability-matrix.csv
```

## Validate the complete package

```bash
python3 validators/validate.py \
  --kind package \
  --file examples/valid-output-ready.yaml \
  --elements examples/valid-model-elements.jsonl \
  --relations examples/valid-model-relations.jsonl \
  --traceability examples/valid-traceability-matrix.csv \
  --ledger examples/valid-evidence-ledger.jsonl \
  --require-transition-ready
```

## Run tests

```bash
make test
```

## Canonical artifact names

```text
artifacts/03-system-model.md
artifacts/03a-model-elements.jsonl
artifacts/03b-model-relations.jsonl
artifacts/03c-system-model.mmd
artifacts/04-traceability-matrix.csv
artifacts/04a-system-model-output.yaml
```

## Important behavior

The validator rejects, among other things:

- dangling evidence references;
- relations with missing endpoints;
- partial problem coverage marked transition-ready;
- missing actual/intended/gap model elements;
- blocking unknowns or conflicts;
- hidden or unmapped assumptions;
- record-count mismatches;
- incomplete required dimensions;
- inconsistent lifecycle gates.
