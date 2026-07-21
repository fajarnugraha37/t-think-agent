PYTHON ?= python3
VALIDATOR := validators/validate.py
EX := examples

.PHONY: test validate-schemas validate-example validate-routes

test:
	$(PYTHON) -m unittest discover -s tests -v

validate-schemas:
	$(PYTHON) $(VALIDATOR) --kind schema

validate-example:
	$(PYTHON) $(VALIDATOR) --kind package \
	 --input $(EX)/valid-input.yaml --output $(EX)/valid-output-ready.yaml \
	 --planning-output $(EX)/source-valid-planning-output.yaml \
	 --targets $(EX)/source-valid-planning-targets.jsonl --plans $(EX)/source-valid-plan-items.jsonl \
	 --dependencies $(EX)/source-valid-dependency-edges.jsonl --coverage $(EX)/source-valid-coverage.csv \
	 --verifications $(EX)/source-valid-verification-plan.jsonl --rollbacks $(EX)/source-valid-rollback-plan.jsonl \
	 --findings $(EX)/source-empty-planning-findings.jsonl --solution-contract $(EX)/source-valid-approved-solution-contract.yaml \
	 --ledger $(EX)/source-valid-evidence-ledger.jsonl --elements $(EX)/source-valid-model-elements.jsonl \
	 --relations $(EX)/source-valid-model-relations.jsonl --assessments $(EX)/valid-assessments.jsonl \
	 --revisions $(EX)/empty-revision-directives.jsonl --requests $(EX)/empty-evidence-requests.jsonl \
	 --approval $(EX)/valid-plan-approval.yaml --plan-contract $(EX)/valid-approved-plan-contract.yaml \
	 --require-transition-ready

validate-routes: test
