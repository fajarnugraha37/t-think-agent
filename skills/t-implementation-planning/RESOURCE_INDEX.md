# Portable Resource Index — t-implementation-planning

All links are relative to the directory containing `SKILL.md`. They are canonical POSIX-style resource identifiers, not user-home or operating-system paths.

## Templates

- [`templates/coverage.template.csv`](templates/coverage.template.csv)
- [`templates/dependency-edge.template.jsonl`](templates/dependency-edge.template.jsonl)
- [`templates/implementation-plan-report.template.md`](templates/implementation-plan-report.template.md)
- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`templates/plan-item.template.jsonl`](templates/plan-item.template.jsonl)
- [`templates/planning-finding.template.jsonl`](templates/planning-finding.template.jsonl)
- [`templates/planning-target.template.jsonl`](templates/planning-target.template.jsonl)
- [`templates/rollback-item.template.jsonl`](templates/rollback-item.template.jsonl)
- [`templates/verification-item.template.jsonl`](templates/verification-item.template.jsonl)

## Schemas

- [`schemas/coverage-row.schema.json`](schemas/coverage-row.schema.json)
- [`schemas/dependency-edge.schema.json`](schemas/dependency-edge.schema.json)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`schemas/plan-item.schema.json`](schemas/plan-item.schema.json)
- [`schemas/planning-finding.schema.json`](schemas/planning-finding.schema.json)
- [`schemas/planning-target.schema.json`](schemas/planning-target.schema.json)
- [`schemas/rollback-item.schema.json`](schemas/rollback-item.schema.json)
- [`schemas/upstream-approved-solution-contract.schema.json`](schemas/upstream-approved-solution-contract.schema.json)
- [`schemas/upstream-evidence-record.schema.json`](schemas/upstream-evidence-record.schema.json)
- [`schemas/upstream-model-element.schema.json`](schemas/upstream-model-element.schema.json)
- [`schemas/upstream-model-relation.schema.json`](schemas/upstream-model-relation.schema.json)
- [`schemas/upstream-solution-critique-output.schema.json`](schemas/upstream-solution-critique-output.schema.json)
- [`schemas/verification-item.schema.json`](schemas/verification-item.schema.json)

## Validators

- [`validators/requirements.txt`](validators/requirements.txt)
- [`validators/validate.py`](validators/validate.py)
- [`validators/validate.sh`](validators/validate.sh)

## Orchestrator

- [`orchestrator/transition-contract.yaml`](orchestrator/transition-contract.yaml)

## Docs

- [`docs/coverage-and-traceability.md`](docs/coverage-and-traceability.md)
- [`docs/planning-policy.md`](docs/planning-policy.md)
- [`docs/routing-rules.md`](docs/routing-rules.md)
- [`docs/semantic-decision-guard.md`](docs/semantic-decision-guard.md)

## Examples

- [`examples/empty-planning-findings.jsonl`](examples/empty-planning-findings.jsonl)
- [`examples/invalid-coverage-partial.csv`](examples/invalid-coverage-partial.csv)
- [`examples/invalid-dependency-cycle.jsonl`](examples/invalid-dependency-cycle.jsonl)
- [`examples/invalid-output-ready-with-coverage-gap.yaml`](examples/invalid-output-ready-with-coverage-gap.yaml)
- [`examples/invalid-plan-dangling-evidence.jsonl`](examples/invalid-plan-dangling-evidence.jsonl)
- [`examples/invalid-plan-new-semantic-decision.jsonl`](examples/invalid-plan-new-semantic-decision.jsonl)
- [`examples/source-valid-approved-solution-contract.yaml`](examples/source-valid-approved-solution-contract.yaml)
- [`examples/source-valid-evidence-ledger.jsonl`](examples/source-valid-evidence-ledger.jsonl)
- [`examples/source-valid-model-elements.jsonl`](examples/source-valid-model-elements.jsonl)
- [`examples/source-valid-model-relations.jsonl`](examples/source-valid-model-relations.jsonl)
- [`examples/source-valid-solution-critique-output.yaml`](examples/source-valid-solution-critique-output.yaml)
- [`examples/valid-coverage.csv`](examples/valid-coverage.csv)
- [`examples/valid-dependency-edges.jsonl`](examples/valid-dependency-edges.jsonl)
- [`examples/valid-findings-investigation-route.jsonl`](examples/valid-findings-investigation-route.jsonl)
- [`examples/valid-findings-solution-design-route.jsonl`](examples/valid-findings-solution-design-route.jsonl)
- [`examples/valid-input.yaml`](examples/valid-input.yaml)
- [`examples/valid-output-investigation-route.yaml`](examples/valid-output-investigation-route.yaml)
- [`examples/valid-output-ready.yaml`](examples/valid-output-ready.yaml)
- [`examples/valid-output-solution-design-route.yaml`](examples/valid-output-solution-design-route.yaml)
- [`examples/valid-plan-items.jsonl`](examples/valid-plan-items.jsonl)
- [`examples/valid-planning-targets.jsonl`](examples/valid-planning-targets.jsonl)
- [`examples/valid-rollback-plan.jsonl`](examples/valid-rollback-plan.jsonl)
- [`examples/valid-verification-plan.jsonl`](examples/valid-verification-plan.jsonl)
