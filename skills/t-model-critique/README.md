# Model Critique Skill Package

A ready-to-use evidence-gated `MODEL_CRITIQUE` phase package.

## Included

- `SKILL.md` — operating policy and lifecycle gate.
- `schemas/` — input/output, critique, assessment, revision, evidence-request, and upstream artifact schemas.
- `templates/` — canonical YAML, JSONL, and Markdown templates.
- `validators/` — structural, semantic, cross-file, and transition-ready validation.
- `examples/` — valid and intentionally invalid packages.
- `tests/` — automated regression tests.
- `orchestrator/transition-contract.yaml` — allowed routing rules.

## Install validator dependencies

```bash
python3 -m pip install -r validators/requirements.txt
```

## Validate a complete package

```bash
python3 validators/validate.py \
  --kind package \
  --input examples/valid-input.yaml \
  --output examples/valid-output-ready.yaml \
  --assessments examples/valid-assessments.jsonl \
  --revisions examples/empty-revision-directives.jsonl \
  --requests examples/empty-evidence-requests.jsonl \
  --model-output examples/source-valid-output-ready.yaml \
  --elements examples/source-valid-model-elements.jsonl \
  --relations examples/source-valid-model-relations.jsonl \
  --traceability examples/source-valid-traceability-matrix.csv \
  --ledger examples/source-valid-evidence-ledger.jsonl \
  --require-transition-ready
```

## Run tests

```bash
make test
```

## Canonical outputs

```text
artifacts/04b-model-critique-input.yaml
artifacts/04c-model-critique-assessments.jsonl
artifacts/04d-model-revision-directives.jsonl
artifacts/04e-model-critique-evidence-requests.jsonl
artifacts/04f-model-critique-report.md
artifacts/04g-model-critique-output.yaml
```
