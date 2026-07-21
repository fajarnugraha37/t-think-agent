PYTHON ?= python3
.PHONY: validate test
validate:
	$(PYTHON) validators/validate.py --input examples/valid-input.yaml --output examples/valid-output.yaml
test:
	$(PYTHON) -m unittest discover -s tests -v
