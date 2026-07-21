PYTHON ?= python3
V := $(PYTHON) validators/validate.py
E := examples
COMMON := --input $(E)/valid-input.yaml --critique-output $(E)/source-valid-model-critique-output.yaml --elements $(E)/source-valid-model-elements.jsonl --relations $(E)/source-valid-model-relations.jsonl --ledger $(E)/source-valid-evidence-ledger.jsonl
PACKAGE := --output $(E)/valid-output.yaml --options $(E)/valid-options.jsonl --coverage $(E)/valid-coverage.csv --decision $(E)/valid-decision.yaml --dominance $(E)/valid-dominance.yaml

.PHONY: install validate-example validate-transition validate-single test checksums
install:
	$(PYTHON) -m pip install -r validators/requirements.txt
validate-example:
	$(V) --kind package $(COMMON) $(PACKAGE)
validate-transition:
	$(V) --kind package $(COMMON) $(PACKAGE) --require-transition-ready
validate-single:
	$(V) --kind package $(COMMON) --output $(E)/single-valid-output.yaml --options $(E)/single-valid-options.jsonl --coverage $(E)/single-valid-coverage.csv --decision $(E)/single-valid-decision.yaml --dominance $(E)/single-valid-dominance.yaml --require-transition-ready
test:
	$(PYTHON) -m unittest discover -s tests -v
checksums:
	find . -type f ! -name CHECKSUMS.sha256 -print0 | sort -z | xargs -0 sha256sum > CHECKSUMS.sha256
