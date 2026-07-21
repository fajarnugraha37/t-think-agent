PYTHON ?= python3
VALIDATOR = validators/validate.py
BASE = --builder-output examples/source-valid-checklist-builder-output.yaml --checklists examples/source-valid-checklist-items.jsonl --dependencies examples/source-valid-checklist-dependencies.jsonl --coverage examples/source-valid-checklist-coverage.csv --batches examples/source-valid-execution-batches.jsonl --findings examples/source-empty-checklist-findings.jsonl --plan-contract examples/source-valid-approved-plan-contract.yaml --plan-critique-output examples/source-valid-plan-critique-output.yaml --ledger examples/source-valid-evidence-ledger.jsonl --elements examples/source-valid-model-elements.jsonl --relations examples/source-valid-model-relations.jsonl

.PHONY: schema validate validate-routes test all
schema:
	$(PYTHON) $(VALIDATOR) --kind schema
validate:
	$(PYTHON) $(VALIDATOR) --kind package --input examples/valid-input.yaml --output examples/valid-output-ready.yaml $(BASE) --assessments examples/valid-assessments.jsonl --revisions examples/empty-revision-directives.jsonl --requests examples/empty-evidence-requests.jsonl --approval examples/valid-checklist-approval.yaml --checklist-contract examples/valid-approved-checklist-contract.yaml --require-transition-ready
validate-routes:
	$(PYTHON) $(VALIDATOR) --kind package --input examples/valid-input-checklist-revision-route.yaml --output examples/valid-output-checklist-revision-route.yaml $(BASE) --assessments examples/valid-assessments-checklist-revision-route.jsonl --revisions examples/valid-revision-directives-checklist-route.jsonl --requests examples/empty-evidence-requests.jsonl --approval examples/valid-checklist-approval-pending.yaml --checklist-contract examples/valid-pending-checklist-contract.yaml
	$(PYTHON) $(VALIDATOR) --kind package --input examples/valid-input-investigation-route.yaml --output examples/valid-output-investigation-route.yaml $(BASE) --assessments examples/valid-assessments-investigation-route.jsonl --revisions examples/empty-revision-directives.jsonl --requests examples/valid-evidence-requests-investigation-route.jsonl --approval examples/valid-checklist-approval-pending.yaml --checklist-contract examples/valid-pending-checklist-contract.yaml
test:
	$(PYTHON) tests/test_validator.py
all: schema validate validate-routes test
