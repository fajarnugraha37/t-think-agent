# Bounded Implementation Skill Package

A standalone governance skill for executing an approved implementation checklist without semantic drift. It includes strict JSON Schemas, YAML/JSONL templates, cross-artifact validation, lifecycle routing, reproducible examples, and automated tests.

## Quick validation

```bash
python3 validators/validate.py --kind package \
  --input examples/valid-input.yaml \
  --output examples/valid-output-ready.yaml \
  --checklist-contract examples/source-valid-approved-checklist-contract.yaml \
  --critique-output examples/source-valid-checklist-critique-output.yaml \
  --plan-contract examples/source-valid-approved-plan-contract.yaml \
  --checklists examples/source-valid-checklist-items.jsonl \
  --batches examples/source-valid-execution-batches.jsonl \
  --ledger examples/source-valid-evidence-ledger.jsonl \
  --executions examples/valid-execution-records.jsonl \
  --changes examples/valid-change-records.jsonl \
  --commands examples/valid-command-results.jsonl \
  --verifications examples/valid-verification-results.jsonl \
  --rollbacks examples/valid-rollback-results.jsonl \
  --findings examples/empty-implementation-findings.jsonl \
  --repository-before examples/valid-repository-before.yaml \
  --repository-after examples/valid-repository-after.yaml \
  --result-contract examples/valid-implementation-result-contract.yaml \
  --require-transition-ready
```

Run `make validate` and `make test` for the complete package checks.
