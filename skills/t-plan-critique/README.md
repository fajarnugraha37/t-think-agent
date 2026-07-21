# Plan Critique Skill Package

A ready-to-use, schema-validated skill for reviewing implementation plans in an evidence-gated engineering lifecycle.

## Quick start

```bash
python -m pip install -r validators/requirements.txt
make test
make validate-example
```

## Package validation

```bash
./validators/validate.sh --kind package \
  --input examples/valid-input.yaml \
  --output examples/valid-output-ready.yaml \
  --planning-output examples/source-valid-planning-output.yaml \
  --targets examples/source-valid-planning-targets.jsonl \
  --plans examples/source-valid-plan-items.jsonl \
  --dependencies examples/source-valid-dependency-edges.jsonl \
  --coverage examples/source-valid-coverage.csv \
  --verifications examples/source-valid-verification-plan.jsonl \
  --rollbacks examples/source-valid-rollback-plan.jsonl \
  --findings examples/source-empty-planning-findings.jsonl \
  --solution-contract examples/source-valid-approved-solution-contract.yaml \
  --ledger examples/source-valid-evidence-ledger.jsonl \
  --elements examples/source-valid-model-elements.jsonl \
  --relations examples/source-valid-model-relations.jsonl \
  --assessments examples/valid-assessments.jsonl \
  --revisions examples/empty-revision-directives.jsonl \
  --requests examples/empty-evidence-requests.jsonl \
  --approval examples/valid-plan-approval.yaml \
  --plan-contract examples/valid-approved-plan-contract.yaml \
  --require-transition-ready
```
