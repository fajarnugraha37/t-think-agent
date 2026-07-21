PYTHON ?= python3
.PHONY: test validate
test:
	$(PYTHON) -m unittest discover -s tests -v
validate:
	$(PYTHON) validators/validate.py --kind package --input examples/valid-input.yaml --output examples/valid-output-ready.yaml --assessments examples/valid-assessments.jsonl --revisions examples/empty-revision-directives.jsonl --requests examples/empty-evidence-requests.jsonl --model-output examples/source-valid-output-ready.yaml --elements examples/source-valid-model-elements.jsonl --relations examples/source-valid-model-relations.jsonl --traceability examples/source-valid-traceability-matrix.csv --ledger examples/source-valid-evidence-ledger.jsonl --require-transition-ready
