# Portable Resource Index — t-plan-critique

All links are relative to the directory containing `SKILL.md`. They are canonical POSIX-style resource identifiers, not user-home or operating-system paths.

## Templates

- [`templates/approved-plan-contract.template.yaml`](templates/approved-plan-contract.template.yaml)
- [`templates/assessment.template.jsonl`](templates/assessment.template.jsonl)
- [`templates/evidence-request.template.jsonl`](templates/evidence-request.template.jsonl)
- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`templates/plan-approval.template.yaml`](templates/plan-approval.template.yaml)
- [`templates/plan-critique-report.template.md`](templates/plan-critique-report.template.md)
- [`templates/revision-directive.template.jsonl`](templates/revision-directive.template.jsonl)

## Schemas

- [`schemas/approved-plan-contract.schema.json`](schemas/approved-plan-contract.schema.json)
- [`schemas/assessment.schema.json`](schemas/assessment.schema.json)
- [`schemas/critique-request.schema.json`](schemas/critique-request.schema.json)
- [`schemas/evidence-request.schema.json`](schemas/evidence-request.schema.json)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`schemas/plan-approval.schema.json`](schemas/plan-approval.schema.json)
- [`schemas/revision-directive.schema.json`](schemas/revision-directive.schema.json)
- [`schemas/upstream-approved-solution-contract.schema.json`](schemas/upstream-approved-solution-contract.schema.json)
- [`schemas/upstream-coverage-row.schema.json`](schemas/upstream-coverage-row.schema.json)
- [`schemas/upstream-dependency-edge.schema.json`](schemas/upstream-dependency-edge.schema.json)
- [`schemas/upstream-evidence-record.schema.json`](schemas/upstream-evidence-record.schema.json)
- [`schemas/upstream-model-element.schema.json`](schemas/upstream-model-element.schema.json)
- [`schemas/upstream-model-relation.schema.json`](schemas/upstream-model-relation.schema.json)
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

- [`docs/approved-plan-contract.md`](docs/approved-plan-contract.md)
- [`docs/critique-policy.md`](docs/critique-policy.md)
- [`docs/review-dimensions.md`](docs/review-dimensions.md)
- [`docs/routing-rules.md`](docs/routing-rules.md)

## Examples

- [`examples/empty-evidence-requests.jsonl`](examples/empty-evidence-requests.jsonl)
- [`examples/empty-revision-directives.jsonl`](examples/empty-revision-directives.jsonl)
- [`examples/invalid-agent-self-approval.yaml`](examples/invalid-agent-self-approval.yaml)
- [`examples/invalid-assessment-rejection-without-evidence.jsonl`](examples/invalid-assessment-rejection-without-evidence.jsonl)
- [`examples/invalid-contract-digest.yaml`](examples/invalid-contract-digest.yaml)
- [`examples/invalid-input-dangling-target.yaml`](examples/invalid-input-dangling-target.yaml)
- [`examples/invalid-output-ready-without-approval.yaml`](examples/invalid-output-ready-without-approval.yaml)
- [`examples/source-empty-planning-findings.jsonl`](examples/source-empty-planning-findings.jsonl)
- [`examples/source-valid-approved-solution-contract.yaml`](examples/source-valid-approved-solution-contract.yaml)
- [`examples/source-valid-coverage.csv`](examples/source-valid-coverage.csv)
- [`examples/source-valid-dependency-edges.jsonl`](examples/source-valid-dependency-edges.jsonl)
- [`examples/source-valid-evidence-ledger.jsonl`](examples/source-valid-evidence-ledger.jsonl)
- [`examples/source-valid-model-elements.jsonl`](examples/source-valid-model-elements.jsonl)
- [`examples/source-valid-model-relations.jsonl`](examples/source-valid-model-relations.jsonl)
- [`examples/source-valid-plan-items.jsonl`](examples/source-valid-plan-items.jsonl)
- [`examples/source-valid-planning-output.yaml`](examples/source-valid-planning-output.yaml)
- [`examples/source-valid-planning-targets.jsonl`](examples/source-valid-planning-targets.jsonl)
- [`examples/source-valid-rollback-plan.jsonl`](examples/source-valid-rollback-plan.jsonl)
- [`examples/source-valid-verification-plan.jsonl`](examples/source-valid-verification-plan.jsonl)
- [`examples/valid-approved-plan-contract.yaml`](examples/valid-approved-plan-contract.yaml)
- [`examples/valid-assessments-investigation-route.jsonl`](examples/valid-assessments-investigation-route.jsonl)
- [`examples/valid-assessments-plan-revision-route.jsonl`](examples/valid-assessments-plan-revision-route.jsonl)
- [`examples/valid-assessments-solution-design-route.jsonl`](examples/valid-assessments-solution-design-route.jsonl)
- [`examples/valid-assessments.jsonl`](examples/valid-assessments.jsonl)
- [`examples/valid-evidence-requests-investigation-route.jsonl`](examples/valid-evidence-requests-investigation-route.jsonl)
- [`examples/valid-input-investigation-route.yaml`](examples/valid-input-investigation-route.yaml)
- [`examples/valid-input-plan-revision-route.yaml`](examples/valid-input-plan-revision-route.yaml)
- [`examples/valid-input-solution-design-route.yaml`](examples/valid-input-solution-design-route.yaml)
- [`examples/valid-input.yaml`](examples/valid-input.yaml)
- [`examples/valid-output-investigation-route.yaml`](examples/valid-output-investigation-route.yaml)
- [`examples/valid-output-plan-revision-route.yaml`](examples/valid-output-plan-revision-route.yaml)
- [`examples/valid-output-ready.yaml`](examples/valid-output-ready.yaml)
- [`examples/valid-output-solution-design-route.yaml`](examples/valid-output-solution-design-route.yaml)
- [`examples/valid-pending-plan-contract.yaml`](examples/valid-pending-plan-contract.yaml)
- [`examples/valid-plan-approval-pending.yaml`](examples/valid-plan-approval-pending.yaml)
- [`examples/valid-plan-approval.yaml`](examples/valid-plan-approval.yaml)
- [`examples/valid-plan-critique-report.md`](examples/valid-plan-critique-report.md)
- [`examples/valid-revision-directives-plan-revision-route.jsonl`](examples/valid-revision-directives-plan-revision-route.jsonl)
- [`examples/valid-revision-directives-solution-design-route.jsonl`](examples/valid-revision-directives-solution-design-route.jsonl)
