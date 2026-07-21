# Checklist Critique Skill Package

Production-oriented lifecycle package for reviewing and approving an atomic implementation checklist before bounded execution.

## Quick validation
```bash
python3 validators/validate.py --kind schema
make validate
make test
```

## Transition-ready package validation
```bash
python3 validators/validate.py --kind package \
  --input examples/valid-input.yaml \
  --output examples/valid-output-ready.yaml \
  --builder-output examples/source-valid-checklist-builder-output.yaml \
  --checklists examples/source-valid-checklist-items.jsonl \
  --dependencies examples/source-valid-checklist-dependencies.jsonl \
  --coverage examples/source-valid-checklist-coverage.csv \
  --batches examples/source-valid-execution-batches.jsonl \
  --findings examples/source-empty-checklist-findings.jsonl \
  --plan-contract examples/source-valid-approved-plan-contract.yaml \
  --plan-critique-output examples/source-valid-plan-critique-output.yaml \
  --ledger examples/source-valid-evidence-ledger.jsonl \
  --elements examples/source-valid-model-elements.jsonl \
  --relations examples/source-valid-model-relations.jsonl \
  --assessments examples/valid-assessments.jsonl \
  --revisions examples/empty-revision-directives.jsonl \
  --requests examples/empty-evidence-requests.jsonl \
  --approval examples/valid-checklist-approval.yaml \
  --checklist-contract examples/valid-approved-checklist-contract.yaml \
  --require-transition-ready
```

The validator checks schemas, target closure, critique coverage, evidence discipline, human-only approval, human gates, immutable operation bindings, source and checklist digests, execution order, parallel levels, exact change surface, lifecycle routing, and output summaries.
