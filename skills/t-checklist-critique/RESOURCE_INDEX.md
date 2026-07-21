# Portable Resource Index — t-checklist-critique

All links are relative to the directory containing `SKILL.md`. They are canonical POSIX-style resource identifiers, not user-home or operating-system paths.

## Templates

- [`templates/approved-checklist-contract.template.yaml`](templates/approved-checklist-contract.template.yaml)
- [`templates/assessment.template.jsonl`](templates/assessment.template.jsonl)
- [`templates/checklist-approval.template.yaml`](templates/checklist-approval.template.yaml)
- [`templates/checklist-critique-report.template.md`](templates/checklist-critique-report.template.md)
- [`templates/evidence-request.template.jsonl`](templates/evidence-request.template.jsonl)
- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`templates/revision-directive.template.jsonl`](templates/revision-directive.template.jsonl)

## Schemas

- [`schemas/approved-checklist-contract.schema.json`](schemas/approved-checklist-contract.schema.json)
- [`schemas/assessment.schema.json`](schemas/assessment.schema.json)
- [`schemas/checklist-approval.schema.json`](schemas/checklist-approval.schema.json)
- [`schemas/critique-request.schema.json`](schemas/critique-request.schema.json)
- [`schemas/evidence-request.schema.json`](schemas/evidence-request.schema.json)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`schemas/revision-directive.schema.json`](schemas/revision-directive.schema.json)
- [`schemas/upstream-approved-plan-contract.schema.json`](schemas/upstream-approved-plan-contract.schema.json)
- [`schemas/upstream-checklist-builder-output.schema.json`](schemas/upstream-checklist-builder-output.schema.json)
- [`schemas/upstream-checklist-coverage-row.schema.json`](schemas/upstream-checklist-coverage-row.schema.json)
- [`schemas/upstream-checklist-dependency.schema.json`](schemas/upstream-checklist-dependency.schema.json)
- [`schemas/upstream-checklist-finding.schema.json`](schemas/upstream-checklist-finding.schema.json)
- [`schemas/upstream-checklist-item.schema.json`](schemas/upstream-checklist-item.schema.json)
- [`schemas/upstream-evidence-record.schema.json`](schemas/upstream-evidence-record.schema.json)
- [`schemas/upstream-execution-batch.schema.json`](schemas/upstream-execution-batch.schema.json)
- [`schemas/upstream-model-element.schema.json`](schemas/upstream-model-element.schema.json)
- [`schemas/upstream-model-relation.schema.json`](schemas/upstream-model-relation.schema.json)
- [`schemas/upstream-plan-critique-output.schema.json`](schemas/upstream-plan-critique-output.schema.json)

## Validators

- [`validators/requirements.txt`](validators/requirements.txt)
- [`validators/validate.py`](validators/validate.py)
- [`validators/validate.sh`](validators/validate.sh)

## Orchestrator

- [`orchestrator/transition-contract.yaml`](orchestrator/transition-contract.yaml)

## Docs

- [`docs/approved-checklist-contract.md`](docs/approved-checklist-contract.md)
- [`docs/critique-policy.md`](docs/critique-policy.md)
- [`docs/review-dimensions.md`](docs/review-dimensions.md)
- [`docs/routing-rules.md`](docs/routing-rules.md)

## Examples

- [`examples/empty-evidence-requests.jsonl`](examples/empty-evidence-requests.jsonl)
- [`examples/empty-revision-directives.jsonl`](examples/empty-revision-directives.jsonl)
- [`examples/invalid-agent-self-approval.yaml`](examples/invalid-agent-self-approval.yaml)
- [`examples/invalid-assessment-rejection-without-evidence.jsonl`](examples/invalid-assessment-rejection-without-evidence.jsonl)
- [`examples/invalid-contract-binding-drift.yaml`](examples/invalid-contract-binding-drift.yaml)
- [`examples/invalid-contract-digest.yaml`](examples/invalid-contract-digest.yaml)
- [`examples/invalid-input-dangling-target.yaml`](examples/invalid-input-dangling-target.yaml)
- [`examples/source-empty-checklist-findings.jsonl`](examples/source-empty-checklist-findings.jsonl)
- [`examples/source-valid-approved-plan-contract.yaml`](examples/source-valid-approved-plan-contract.yaml)
- [`examples/source-valid-checklist-builder-output.yaml`](examples/source-valid-checklist-builder-output.yaml)
- [`examples/source-valid-checklist-coverage.csv`](examples/source-valid-checklist-coverage.csv)
- [`examples/source-valid-checklist-dependencies.jsonl`](examples/source-valid-checklist-dependencies.jsonl)
- [`examples/source-valid-checklist-items.jsonl`](examples/source-valid-checklist-items.jsonl)
- [`examples/source-valid-evidence-ledger.jsonl`](examples/source-valid-evidence-ledger.jsonl)
- [`examples/source-valid-execution-batches.jsonl`](examples/source-valid-execution-batches.jsonl)
- [`examples/source-valid-model-elements.jsonl`](examples/source-valid-model-elements.jsonl)
- [`examples/source-valid-model-relations.jsonl`](examples/source-valid-model-relations.jsonl)
- [`examples/source-valid-plan-critique-output.yaml`](examples/source-valid-plan-critique-output.yaml)
- [`examples/valid-approved-checklist-contract.yaml`](examples/valid-approved-checklist-contract.yaml)
- [`examples/valid-assessments-checklist-revision-route.jsonl`](examples/valid-assessments-checklist-revision-route.jsonl)
- [`examples/valid-assessments-investigation-route.jsonl`](examples/valid-assessments-investigation-route.jsonl)
- [`examples/valid-assessments.jsonl`](examples/valid-assessments.jsonl)
- [`examples/valid-checklist-approval-pending.yaml`](examples/valid-checklist-approval-pending.yaml)
- [`examples/valid-checklist-approval.yaml`](examples/valid-checklist-approval.yaml)
- [`examples/valid-checklist-critique-report.md`](examples/valid-checklist-critique-report.md)
- [`examples/valid-evidence-requests-investigation-route.jsonl`](examples/valid-evidence-requests-investigation-route.jsonl)
- [`examples/valid-input-checklist-revision-route.yaml`](examples/valid-input-checklist-revision-route.yaml)
- [`examples/valid-input-investigation-route.yaml`](examples/valid-input-investigation-route.yaml)
- [`examples/valid-input.yaml`](examples/valid-input.yaml)
- [`examples/valid-output-checklist-revision-route.yaml`](examples/valid-output-checklist-revision-route.yaml)
- [`examples/valid-output-investigation-route.yaml`](examples/valid-output-investigation-route.yaml)
- [`examples/valid-output-ready.yaml`](examples/valid-output-ready.yaml)
- [`examples/valid-pending-checklist-contract.yaml`](examples/valid-pending-checklist-contract.yaml)
- [`examples/valid-revision-directives-checklist-route.jsonl`](examples/valid-revision-directives-checklist-route.jsonl)
