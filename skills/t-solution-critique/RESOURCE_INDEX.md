# Portable Resource Index — t-solution-critique

All links are relative to the directory containing `SKILL.md`. They are canonical POSIX-style resource identifiers, not user-home or operating-system paths.

## Templates

- [`templates/approved-solution-contract.template.yaml`](templates/approved-solution-contract.template.yaml)
- [`templates/assessment.template.jsonl`](templates/assessment.template.jsonl)
- [`templates/decision-approval.template.yaml`](templates/decision-approval.template.yaml)
- [`templates/evidence-request.template.jsonl`](templates/evidence-request.template.jsonl)
- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`templates/revision-directive.template.jsonl`](templates/revision-directive.template.jsonl)
- [`templates/solution-critique-report.template.md`](templates/solution-critique-report.template.md)

## Schemas

- [`schemas/approved-solution-contract.schema.json`](schemas/approved-solution-contract.schema.json)
- [`schemas/assessment.schema.json`](schemas/assessment.schema.json)
- [`schemas/critique-request.schema.json`](schemas/critique-request.schema.json)
- [`schemas/decision-approval.schema.json`](schemas/decision-approval.schema.json)
- [`schemas/evidence-request.schema.json`](schemas/evidence-request.schema.json)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`schemas/revision-directive.schema.json`](schemas/revision-directive.schema.json)
- [`schemas/upstream-coverage-row.schema.json`](schemas/upstream-coverage-row.schema.json)
- [`schemas/upstream-decision-record.schema.json`](schemas/upstream-decision-record.schema.json)
- [`schemas/upstream-dominance-proof.schema.json`](schemas/upstream-dominance-proof.schema.json)
- [`schemas/upstream-evidence-record.schema.json`](schemas/upstream-evidence-record.schema.json)
- [`schemas/upstream-model-element.schema.json`](schemas/upstream-model-element.schema.json)
- [`schemas/upstream-model-relation.schema.json`](schemas/upstream-model-relation.schema.json)
- [`schemas/upstream-solution-design-output.schema.json`](schemas/upstream-solution-design-output.schema.json)
- [`schemas/upstream-solution-option.schema.json`](schemas/upstream-solution-option.schema.json)

## Validators

- [`validators/requirements.txt`](validators/requirements.txt)
- [`validators/validate.py`](validators/validate.py)
- [`validators/validate.sh`](validators/validate.sh)

## Orchestrator

- [`orchestrator/transition-contract.yaml`](orchestrator/transition-contract.yaml)

## Docs

- [`docs/approved-solution-contract.md`](docs/approved-solution-contract.md)
- [`docs/critique-policy.md`](docs/critique-policy.md)
- [`docs/decision-approval-policy.md`](docs/decision-approval-policy.md)
- [`docs/routing-rules.md`](docs/routing-rules.md)

## Examples

- [`examples/empty-evidence-requests.jsonl`](examples/empty-evidence-requests.jsonl)
- [`examples/empty-revision-directives.jsonl`](examples/empty-revision-directives.jsonl)
- [`examples/invalid-approval-missing-risk.yaml`](examples/invalid-approval-missing-risk.yaml)
- [`examples/invalid-assessment-rejection-without-evidence.jsonl`](examples/invalid-assessment-rejection-without-evidence.jsonl)
- [`examples/invalid-contract-semantic-drift.yaml`](examples/invalid-contract-semantic-drift.yaml)
- [`examples/invalid-input-dangling-target.yaml`](examples/invalid-input-dangling-target.yaml)
- [`examples/invalid-output-ready-without-approval.yaml`](examples/invalid-output-ready-without-approval.yaml)
- [`examples/source-valid-coverage.csv`](examples/source-valid-coverage.csv)
- [`examples/source-valid-decision.yaml`](examples/source-valid-decision.yaml)
- [`examples/source-valid-dominance.yaml`](examples/source-valid-dominance.yaml)
- [`examples/source-valid-evidence-ledger.jsonl`](examples/source-valid-evidence-ledger.jsonl)
- [`examples/source-valid-model-elements.jsonl`](examples/source-valid-model-elements.jsonl)
- [`examples/source-valid-model-relations.jsonl`](examples/source-valid-model-relations.jsonl)
- [`examples/source-valid-options.jsonl`](examples/source-valid-options.jsonl)
- [`examples/source-valid-solution-design-output.yaml`](examples/source-valid-solution-design-output.yaml)
- [`examples/valid-approved-solution-contract.yaml`](examples/valid-approved-solution-contract.yaml)
- [`examples/valid-assessments-investigation-route.jsonl`](examples/valid-assessments-investigation-route.jsonl)
- [`examples/valid-assessments-solution-design-route.jsonl`](examples/valid-assessments-solution-design-route.jsonl)
- [`examples/valid-assessments.jsonl`](examples/valid-assessments.jsonl)
- [`examples/valid-decision-approval-pending.yaml`](examples/valid-decision-approval-pending.yaml)
- [`examples/valid-decision-approval.yaml`](examples/valid-decision-approval.yaml)
- [`examples/valid-evidence-requests-investigation-route.jsonl`](examples/valid-evidence-requests-investigation-route.jsonl)
- [`examples/valid-input-investigation-route.yaml`](examples/valid-input-investigation-route.yaml)
- [`examples/valid-input-solution-design-route.yaml`](examples/valid-input-solution-design-route.yaml)
- [`examples/valid-input.yaml`](examples/valid-input.yaml)
- [`examples/valid-output-investigation-route.yaml`](examples/valid-output-investigation-route.yaml)
- [`examples/valid-output-ready.yaml`](examples/valid-output-ready.yaml)
- [`examples/valid-output-solution-design-route.yaml`](examples/valid-output-solution-design-route.yaml)
- [`examples/valid-pending-solution-contract.yaml`](examples/valid-pending-solution-contract.yaml)
- [`examples/valid-revision-directives-solution-design-route.jsonl`](examples/valid-revision-directives-solution-design-route.jsonl)
