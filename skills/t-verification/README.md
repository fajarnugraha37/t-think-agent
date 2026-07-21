# Verification Skill Package

A production-oriented, evidence-gated skill package for the Verification phase of an AI software-engineering lifecycle. It consumes the Technical Review contract and bounded implementation artifacts, independently executes exact verification obligations, attempts falsification for high-risk claims, freezes results in an immutable contract, and routes defects without mutating the implementation.

## Validate the ready example

```bash
make validate
```

## Run tests

```bash
make test
```

## Direct CLI

```bash
python3 validators/validate.py --kind package \
  --input examples/valid-input.yaml \
  --output examples/valid-output-ready.yaml \
  --assignment examples/valid-verifier-assignment.yaml \
  --environment examples/valid-environment.yaml \
  --technical-review-output examples/source-valid-technical-review-output.yaml \
  --technical-review-contract examples/source-valid-technical-review-result-contract.yaml \
  --implementation-contract examples/source-valid-implementation-result-contract.yaml \
  --checklist-contract examples/source-valid-approved-checklist-contract.yaml \
  --checklists examples/source-valid-checklist-items.jsonl \
  --source-verifications examples/source-valid-verification-results.jsonl \
  --repository-state examples/source-valid-repository-after.yaml \
  --changes examples/source-valid-change-records.jsonl \
  --source-ledger examples/source-valid-evidence-ledger.jsonl \
  --obligations examples/valid-verification-obligations.jsonl \
  --executions examples/valid-verification-executions.jsonl \
  --falsifications examples/valid-falsification-attempts.jsonl \
  --evidence examples/valid-verification-evidence.jsonl \
  --findings examples/empty-verification-findings.jsonl \
  --directives examples/empty-remediation-directives.jsonl \
  --result-contract examples/valid-verification-result-contract.yaml \
  --require-transition-ready
```
