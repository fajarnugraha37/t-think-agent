PYTHON ?= python
VALIDATOR := $(PYTHON) validators/validate.py
BASE := --input examples/valid-input.yaml \
 --contract examples/source-valid-approved-solution-contract.yaml \
 --critique-output examples/source-valid-solution-critique-output.yaml \
 --targets examples/valid-planning-targets.jsonl \
 --plans examples/valid-plan-items.jsonl \
 --dependencies examples/valid-dependency-edges.jsonl \
 --coverage examples/valid-coverage.csv \
 --verifications examples/valid-verification-plan.jsonl \
 --rollbacks examples/valid-rollback-plan.jsonl \
 --findings examples/empty-planning-findings.jsonl \
 --ledger examples/source-valid-evidence-ledger.jsonl \
 --elements examples/source-valid-model-elements.jsonl \
 --relations examples/source-valid-model-relations.jsonl

.PHONY: install validate-example validate-routes test schemas
install:
	$(PYTHON) -m pip install -r validators/requirements.txt

validate-example:
	$(VALIDATOR) --kind package $(BASE) --output examples/valid-output-ready.yaml --require-transition-ready

validate-routes:
	$(VALIDATOR) --kind package $(filter-out --findings examples/empty-planning-findings.jsonl,$(BASE)) --output examples/valid-output-investigation-route.yaml --findings examples/valid-findings-investigation-route.jsonl
	$(VALIDATOR) --kind package $(filter-out --plans examples/valid-plan-items.jsonl --findings examples/empty-planning-findings.jsonl,$(BASE)) --output examples/valid-output-solution-design-route.yaml --plans examples/invalid-plan-new-semantic-decision.jsonl --findings examples/valid-findings-solution-design-route.jsonl

test:
	$(PYTHON) -m unittest discover -s tests -v

schemas:
	$(PYTHON) -c "import json,pathlib; from jsonschema import Draft202012Validator; [Draft202012Validator.check_schema(json.loads(p.read_text())) for p in pathlib.Path('schemas').glob('*.json')]; print('All schemas valid')"
