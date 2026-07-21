.PHONY: install validate test package
install:
	python -m pip install -r validators/requirements.txt
validate:
	python validators/validate.py --kind input --file examples/valid-input.yaml
	python validators/validate.py --kind ledger --file examples/valid-evidence-ledger.jsonl
	python validators/validate.py --kind output --file examples/valid-output-ready.yaml --ledger examples/valid-evidence-ledger.jsonl --require-transition-ready
test:
	python -m unittest discover -s tests -v
package:
	cd .. && zip -r investigation-skill.zip investigation-skill
