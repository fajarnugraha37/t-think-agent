# Portable Resource Index — t-checklist-builder

All links are relative to the directory containing `SKILL.md`. They are canonical POSIX-style resource identifiers, not user-home or operating-system paths.

## Templates

- [`templates/checklist-builder-report.template.md`](templates/checklist-builder-report.template.md)
- [`templates/checklist-coverage.template.csv`](templates/checklist-coverage.template.csv)
- [`templates/checklist-dependency.template.jsonl`](templates/checklist-dependency.template.jsonl)
- [`templates/checklist-finding.template.jsonl`](templates/checklist-finding.template.jsonl)
- [`templates/checklist-item.template.jsonl`](templates/checklist-item.template.jsonl)
- [`templates/execution-batch.template.jsonl`](templates/execution-batch.template.jsonl)
- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)

## Schemas

- [`schemas/checklist-dependency.schema.json`](schemas/checklist-dependency.schema.json)
- [`schemas/checklist-finding.schema.json`](schemas/checklist-finding.schema.json)
- [`schemas/checklist-item.schema.json`](schemas/checklist-item.schema.json)
- [`schemas/coverage-row.schema.json`](schemas/coverage-row.schema.json)
- [`schemas/execution-batch.schema.json`](schemas/execution-batch.schema.json)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`schemas/upstream-approved-plan-contract.schema.json`](schemas/upstream-approved-plan-contract.schema.json)
- [`schemas/upstream-approved-solution-contract.schema.json`](schemas/upstream-approved-solution-contract.schema.json)
- [`schemas/upstream-evidence-record.schema.json`](schemas/upstream-evidence-record.schema.json)
- [`schemas/upstream-model-element.schema.json`](schemas/upstream-model-element.schema.json)
- [`schemas/upstream-model-relation.schema.json`](schemas/upstream-model-relation.schema.json)
- [`schemas/upstream-plan-coverage-row.schema.json`](schemas/upstream-plan-coverage-row.schema.json)
- [`schemas/upstream-plan-critique-output.schema.json`](schemas/upstream-plan-critique-output.schema.json)
- [`schemas/upstream-plan-dependency.schema.json`](schemas/upstream-plan-dependency.schema.json)
- [`schemas/upstream-plan-item.schema.json`](schemas/upstream-plan-item.schema.json)
- [`schemas/upstream-planning-finding.schema.json`](schemas/upstream-planning-finding.schema.json)
- [`schemas/upstream-planning-output.schema.json`](schemas/upstream-planning-output.schema.json)
- [`schemas/upstream-planning-target.schema.json`](schemas/upstream-planning-target.schema.json)
- [`schemas/upstream-rollback-item.schema.json`](schemas/upstream-rollback-item.schema.json)
- [`schemas/upstream-verification-item.schema.json`](schemas/upstream-verification-item.schema.json)

## Validators

- [`validators/requirements.txt`](validators/requirements.txt)
- [`validators/validate.py`](validators/validate.py)
- [`validators/validate.sh`](validators/validate.sh)

## Orchestrator

- [`orchestrator/transition-contract.yaml`](orchestrator/transition-contract.yaml)

## Docs

- [`docs/atomicity-policy.md`](docs/atomicity-policy.md)
- [`docs/execution-guard.md`](docs/execution-guard.md)
- [`docs/routing-rules.md`](docs/routing-rules.md)
- [`docs/traceability-and-coverage.md`](docs/traceability-and-coverage.md)

## Examples

- [`examples/empty-checklist-findings.jsonl`](examples/empty-checklist-findings.jsonl)
- [`examples/invalid-checklist-coverage-duplicate.csv`](examples/invalid-checklist-coverage-duplicate.csv)
- [`examples/invalid-checklist-coverage-partial.csv`](examples/invalid-checklist-coverage-partial.csv)
- [`examples/invalid-checklist-dangling-verification.jsonl`](examples/invalid-checklist-dangling-verification.jsonl)
- [`examples/invalid-checklist-dependency-cycle.jsonl`](examples/invalid-checklist-dependency-cycle.jsonl)
- [`examples/invalid-checklist-new-semantic-decision.jsonl`](examples/invalid-checklist-new-semantic-decision.jsonl)
- [`examples/invalid-checklist-source-operation-drift.jsonl`](examples/invalid-checklist-source-operation-drift.jsonl)
- [`examples/invalid-execution-batches-drift.jsonl`](examples/invalid-execution-batches-drift.jsonl)
- [`examples/source-empty-planning-findings.jsonl`](examples/source-empty-planning-findings.jsonl)
- [`examples/source-valid-approved-plan-contract.yaml`](examples/source-valid-approved-plan-contract.yaml)
- [`examples/source-valid-approved-solution-contract.yaml`](examples/source-valid-approved-solution-contract.yaml)
- [`examples/source-valid-evidence-ledger.jsonl`](examples/source-valid-evidence-ledger.jsonl)
- [`examples/source-valid-model-elements.jsonl`](examples/source-valid-model-elements.jsonl)
- [`examples/source-valid-model-relations.jsonl`](examples/source-valid-model-relations.jsonl)
- [`examples/source-valid-plan-coverage.csv`](examples/source-valid-plan-coverage.csv)
- [`examples/source-valid-plan-critique-output.yaml`](examples/source-valid-plan-critique-output.yaml)
- [`examples/source-valid-plan-dependencies.jsonl`](examples/source-valid-plan-dependencies.jsonl)
- [`examples/source-valid-plan-items.jsonl`](examples/source-valid-plan-items.jsonl)
- [`examples/source-valid-planning-output.yaml`](examples/source-valid-planning-output.yaml)
- [`examples/source-valid-planning-targets.jsonl`](examples/source-valid-planning-targets.jsonl)
- [`examples/source-valid-rollback-plan.jsonl`](examples/source-valid-rollback-plan.jsonl)
- [`examples/source-valid-verification-plan.jsonl`](examples/source-valid-verification-plan.jsonl)
- [`examples/valid-checklist-coverage.csv`](examples/valid-checklist-coverage.csv)
- [`examples/valid-checklist-dependencies.jsonl`](examples/valid-checklist-dependencies.jsonl)
- [`examples/valid-checklist-items.jsonl`](examples/valid-checklist-items.jsonl)
- [`examples/valid-execution-batches.jsonl`](examples/valid-execution-batches.jsonl)
- [`examples/valid-findings-implementation-plan-route.jsonl`](examples/valid-findings-implementation-plan-route.jsonl)
- [`examples/valid-findings-investigation-route.jsonl`](examples/valid-findings-investigation-route.jsonl)
- [`examples/valid-input.yaml`](examples/valid-input.yaml)
- [`examples/valid-output-implementation-plan-route.yaml`](examples/valid-output-implementation-plan-route.yaml)
- [`examples/valid-output-investigation-route.yaml`](examples/valid-output-investigation-route.yaml)
- [`examples/valid-output-ready.yaml`](examples/valid-output-ready.yaml)
