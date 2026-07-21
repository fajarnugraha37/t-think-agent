# Portable Resource Index — t-solution-design

All links are relative to the directory containing `SKILL.md`. They are canonical POSIX-style resource identifiers, not user-home or operating-system paths.

## Templates

- [`templates/decision-record.template.yaml`](templates/decision-record.template.yaml)
- [`templates/dominance-proof.template.yaml`](templates/dominance-proof.template.yaml)
- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`templates/solution-coverage-matrix.template.csv`](templates/solution-coverage-matrix.template.csv)
- [`templates/solution-design-report.template.md`](templates/solution-design-report.template.md)
- [`templates/solution-option.template.jsonl`](templates/solution-option.template.jsonl)

## Schemas

- [`schemas/coverage-row.schema.json`](schemas/coverage-row.schema.json)
- [`schemas/decision-record.schema.json`](schemas/decision-record.schema.json)
- [`schemas/dominance-proof.schema.json`](schemas/dominance-proof.schema.json)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`schemas/solution-option.schema.json`](schemas/solution-option.schema.json)
- [`schemas/upstream-evidence-record.schema.json`](schemas/upstream-evidence-record.schema.json)
- [`schemas/upstream-model-critique-output.schema.json`](schemas/upstream-model-critique-output.schema.json)
- [`schemas/upstream-model-element.schema.json`](schemas/upstream-model-element.schema.json)
- [`schemas/upstream-model-relation.schema.json`](schemas/upstream-model-relation.schema.json)

## Validators

- [`validators/requirements.txt`](validators/requirements.txt)
- [`validators/validate.py`](validators/validate.py)
- [`validators/validate.sh`](validators/validate.sh)

## Orchestrator

- [`orchestrator/transition-contract.yaml`](orchestrator/transition-contract.yaml)

## Docs

- [`docs/coverage-and-decision-policy.md`](docs/coverage-and-decision-policy.md)
- [`docs/dominance-proof.md`](docs/dominance-proof.md)
- [`docs/option-distinctness.md`](docs/option-distinctness.md)

## Examples

- [`examples/invalid-coverage-missing-row.csv`](examples/invalid-coverage-missing-row.csv)
- [`examples/invalid-dominance-not-required.yaml`](examples/invalid-dominance-not-required.yaml)
- [`examples/invalid-options-blocking-assumption.jsonl`](examples/invalid-options-blocking-assumption.jsonl)
- [`examples/invalid-options-duplicate.jsonl`](examples/invalid-options-duplicate.jsonl)
- [`examples/invalid-output-premature-ready.yaml`](examples/invalid-output-premature-ready.yaml)
- [`examples/single-valid-coverage.csv`](examples/single-valid-coverage.csv)
- [`examples/single-valid-decision.yaml`](examples/single-valid-decision.yaml)
- [`examples/single-valid-dominance.yaml`](examples/single-valid-dominance.yaml)
- [`examples/single-valid-options.jsonl`](examples/single-valid-options.jsonl)
- [`examples/single-valid-output.yaml`](examples/single-valid-output.yaml)
- [`examples/source-valid-evidence-ledger.jsonl`](examples/source-valid-evidence-ledger.jsonl)
- [`examples/source-valid-model-critique-output.yaml`](examples/source-valid-model-critique-output.yaml)
- [`examples/source-valid-model-elements.jsonl`](examples/source-valid-model-elements.jsonl)
- [`examples/source-valid-model-relations.jsonl`](examples/source-valid-model-relations.jsonl)
- [`examples/valid-coverage.csv`](examples/valid-coverage.csv)
- [`examples/valid-decision.yaml`](examples/valid-decision.yaml)
- [`examples/valid-dominance.yaml`](examples/valid-dominance.yaml)
- [`examples/valid-input.yaml`](examples/valid-input.yaml)
- [`examples/valid-options.jsonl`](examples/valid-options.jsonl)
- [`examples/valid-output.yaml`](examples/valid-output.yaml)
