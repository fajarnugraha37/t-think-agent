PYTHON ?= python3
VALIDATOR := validators/validate.py

.PHONY: install validate test clean

install:
	$(PYTHON) -m pip install -r validators/requirements.txt

validate:
	$(PYTHON) $(VALIDATOR) --kind input --file examples/valid-input.yaml
	$(PYTHON) $(VALIDATOR) --kind package --file examples/valid-output-ready.yaml --elements examples/valid-model-elements.jsonl --relations examples/valid-model-relations.jsonl --traceability examples/valid-traceability-matrix.csv --ledger examples/valid-evidence-ledger.jsonl --require-transition-ready

test:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
