.PHONY: validate-example test schemas
PYTHON ?= python3
VALIDATOR = $(PYTHON) validators/validate.py
ARGS = --kind package --input examples/valid-input.yaml --output examples/valid-output-ready.yaml --assessments examples/valid-assessments.jsonl --revisions examples/empty-revision-directives.jsonl --requests examples/empty-evidence-requests.jsonl --approval examples/valid-decision-approval.yaml --contract examples/valid-approved-solution-contract.yaml --design-output examples/source-valid-solution-design-output.yaml --options examples/source-valid-options.jsonl --coverage examples/source-valid-coverage.csv --decision examples/source-valid-decision.yaml --dominance examples/source-valid-dominance.yaml --ledger examples/source-valid-evidence-ledger.jsonl --elements examples/source-valid-model-elements.jsonl --relations examples/source-valid-model-relations.jsonl

validate-example:
	$(VALIDATOR) $(ARGS) --require-transition-ready

test:
	$(PYTHON) -m unittest discover -s tests -v

schemas:
	@for f in schemas/*.json; do $(PYTHON) -m json.tool $$f >/dev/null || exit 1; done
	@echo "All JSON schemas are valid JSON"
