PYTHON ?= python3
ARGS = --input examples/valid-input.yaml --output examples/valid-output-ready.yaml --plan-contract examples/source-valid-approved-plan-contract.yaml --plan-critique-output examples/source-valid-plan-critique-output.yaml --planning-output examples/source-valid-planning-output.yaml --targets examples/source-valid-planning-targets.jsonl --plans examples/source-valid-plan-items.jsonl --plan-dependencies examples/source-valid-plan-dependencies.jsonl --plan-coverage examples/source-valid-plan-coverage.csv --verifications examples/source-valid-verification-plan.jsonl --rollbacks examples/source-valid-rollback-plan.jsonl --planning-findings examples/source-empty-planning-findings.jsonl --solution-contract examples/source-valid-approved-solution-contract.yaml --ledger examples/source-valid-evidence-ledger.jsonl --elements examples/source-valid-model-elements.jsonl --relations examples/source-valid-model-relations.jsonl --checklists examples/valid-checklist-items.jsonl --dependencies examples/valid-checklist-dependencies.jsonl --coverage examples/valid-checklist-coverage.csv --batches examples/valid-execution-batches.jsonl --findings examples/empty-checklist-findings.jsonl
.PHONY: validate test schemas clean
validate: schemas
	$(PYTHON) validators/validate.py --kind package $(ARGS) --require-transition-ready
schemas:
	$(PYTHON) validators/validate.py --kind schema
test:
	$(PYTHON) -m unittest discover -s tests -v
clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
