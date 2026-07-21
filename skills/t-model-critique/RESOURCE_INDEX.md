# Portable Resource Index — t-model-critique

All links are relative to the directory containing `SKILL.md`. They are canonical POSIX-style resource identifiers, not user-home or operating-system paths.

## Templates

- [`templates/assessment.template.jsonl`](templates/assessment.template.jsonl)
- [`templates/evidence-request.template.jsonl`](templates/evidence-request.template.jsonl)
- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/model-critique-report.template.md`](templates/model-critique-report.template.md)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`templates/revision-directive.template.jsonl`](templates/revision-directive.template.jsonl)

## Schemas

- [`schemas/assessment.schema.json`](schemas/assessment.schema.json)
- [`schemas/critique-request.schema.json`](schemas/critique-request.schema.json)
- [`schemas/evidence-request.schema.json`](schemas/evidence-request.schema.json)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`schemas/revision-directive.schema.json`](schemas/revision-directive.schema.json)
- [`schemas/upstream-consistency-decision.schema.json`](schemas/upstream-consistency-decision.schema.json)
- [`schemas/upstream-evidence-record.schema.json`](schemas/upstream-evidence-record.schema.json)
- [`schemas/upstream-model-element.schema.json`](schemas/upstream-model-element.schema.json)
- [`schemas/upstream-model-relation.schema.json`](schemas/upstream-model-relation.schema.json)
- [`schemas/upstream-system-model-output.schema.json`](schemas/upstream-system-model-output.schema.json)
- [`schemas/upstream-traceability-row.schema.json`](schemas/upstream-traceability-row.schema.json)

## Validators

- [`validators/requirements.txt`](validators/requirements.txt)
- [`validators/validate.py`](validators/validate.py)
- [`validators/validate.sh`](validators/validate.sh)

## Orchestrator

- [`orchestrator/transition-contract.yaml`](orchestrator/transition-contract.yaml)

## Docs

- [`docs/critique-policy.md`](docs/critique-policy.md)
- [`docs/routing-rules.md`](docs/routing-rules.md)

## Examples

- [`examples/empty-evidence-requests.jsonl`](examples/empty-evidence-requests.jsonl)
- [`examples/empty-revision-directives.jsonl`](examples/empty-revision-directives.jsonl)
- [`examples/invalid-assessment-dangling-target.jsonl`](examples/invalid-assessment-dangling-target.jsonl)
- [`examples/invalid-assessment-rejection-without-evidence.jsonl`](examples/invalid-assessment-rejection-without-evidence.jsonl)
- [`examples/invalid-input-dangling-target.yaml`](examples/invalid-input-dangling-target.yaml)
- [`examples/invalid-output-ready-without-approval.yaml`](examples/invalid-output-ready-without-approval.yaml)
- [`examples/invalid-output-unassessed.yaml`](examples/invalid-output-unassessed.yaml)
- [`examples/source-valid-evidence-ledger.jsonl`](examples/source-valid-evidence-ledger.jsonl)
- [`examples/source-valid-model-elements.jsonl`](examples/source-valid-model-elements.jsonl)
- [`examples/source-valid-model-relations.jsonl`](examples/source-valid-model-relations.jsonl)
- [`examples/source-valid-output-ready.yaml`](examples/source-valid-output-ready.yaml)
- [`examples/source-valid-traceability-matrix.csv`](examples/source-valid-traceability-matrix.csv)
- [`examples/valid-assessments-investigation-route.jsonl`](examples/valid-assessments-investigation-route.jsonl)
- [`examples/valid-assessments-system-model-route.jsonl`](examples/valid-assessments-system-model-route.jsonl)
- [`examples/valid-assessments.jsonl`](examples/valid-assessments.jsonl)
- [`examples/valid-evidence-requests-investigation-route.jsonl`](examples/valid-evidence-requests-investigation-route.jsonl)
- [`examples/valid-input-investigation-route.yaml`](examples/valid-input-investigation-route.yaml)
- [`examples/valid-input-system-model-route.yaml`](examples/valid-input-system-model-route.yaml)
- [`examples/valid-input.yaml`](examples/valid-input.yaml)
- [`examples/valid-output-investigation-route.yaml`](examples/valid-output-investigation-route.yaml)
- [`examples/valid-output-ready.yaml`](examples/valid-output-ready.yaml)
- [`examples/valid-output-system-model-route.yaml`](examples/valid-output-system-model-route.yaml)
- [`examples/valid-revision-directives-system-model-route.jsonl`](examples/valid-revision-directives-system-model-route.jsonl)
