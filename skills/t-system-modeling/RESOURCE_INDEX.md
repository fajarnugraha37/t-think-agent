# Portable Resource Index — t-system-modeling

All links are relative to the directory containing `SKILL.md`. They are canonical POSIX-style resource identifiers, not user-home or operating-system paths.

## Templates

- [`templates/consistency-assessment.template.yaml`](templates/consistency-assessment.template.yaml)
- [`templates/critique.template.yaml`](templates/critique.template.yaml)
- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/model-elements.template.jsonl`](templates/model-elements.template.jsonl)
- [`templates/model-relations.template.jsonl`](templates/model-relations.template.jsonl)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`templates/system-model.mmd`](templates/system-model.mmd)
- [`templates/system-model.template.md`](templates/system-model.template.md)
- [`templates/traceability-matrix.template.csv`](templates/traceability-matrix.template.csv)

## Schemas

- [`schemas/consistency-decision.schema.json`](schemas/consistency-decision.schema.json)
- [`schemas/critique.schema.json`](schemas/critique.schema.json)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/model-element.schema.json`](schemas/model-element.schema.json)
- [`schemas/model-relation.schema.json`](schemas/model-relation.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`schemas/traceability-row.schema.json`](schemas/traceability-row.schema.json)
- [`schemas/upstream-evidence-record.schema.json`](schemas/upstream-evidence-record.schema.json)

## Validators

- [`validators/requirements.txt`](validators/requirements.txt)
- [`validators/validate.py`](validators/validate.py)
- [`validators/validate.sh`](validators/validate.sh)

## Orchestrator

- [`orchestrator/transition-contract.yaml`](orchestrator/transition-contract.yaml)

## Docs

- [`docs/model-taxonomy.md`](docs/model-taxonomy.md)
- [`docs/reasoning-and-evidence-policy.md`](docs/reasoning-and-evidence-policy.md)

## Examples

- [`examples/invalid-model-elements-dangling-evidence.jsonl`](examples/invalid-model-elements-dangling-evidence.jsonl)
- [`examples/invalid-model-relations-dangling-endpoint.jsonl`](examples/invalid-model-relations-dangling-endpoint.jsonl)
- [`examples/invalid-output-partial-coverage.yaml`](examples/invalid-output-partial-coverage.yaml)
- [`examples/valid-evidence-ledger.jsonl`](examples/valid-evidence-ledger.jsonl)
- [`examples/valid-input.yaml`](examples/valid-input.yaml)
- [`examples/valid-model-elements.jsonl`](examples/valid-model-elements.jsonl)
- [`examples/valid-model-relations.jsonl`](examples/valid-model-relations.jsonl)
- [`examples/valid-output-ready.yaml`](examples/valid-output-ready.yaml)
- [`examples/valid-traceability-matrix.csv`](examples/valid-traceability-matrix.csv)
