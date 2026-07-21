PYTHON ?= python3
VALIDATOR = $(PYTHON) validators/validate.py
BASE = --input examples/valid-input.yaml --assignment examples/valid-verifier-assignment.yaml --environment examples/valid-environment.yaml --technical-review-output examples/source-valid-technical-review-output.yaml --technical-review-contract examples/source-valid-technical-review-result-contract.yaml --implementation-contract examples/source-valid-implementation-result-contract.yaml --checklist-contract examples/source-valid-approved-checklist-contract.yaml --checklists examples/source-valid-checklist-items.jsonl --source-verifications examples/source-valid-verification-results.jsonl --repository-state examples/source-valid-repository-after.yaml --changes examples/source-valid-change-records.jsonl --source-ledger examples/source-valid-evidence-ledger.jsonl --obligations examples/valid-verification-obligations.jsonl --evidence examples/valid-verification-evidence.jsonl

.PHONY: validate validate-loopback test schemas checksums
validate:
	$(VALIDATOR) --kind package $(BASE) --output examples/valid-output-ready.yaml --executions examples/valid-verification-executions.jsonl --falsifications examples/valid-falsification-attempts.jsonl --findings examples/empty-verification-findings.jsonl --directives examples/empty-remediation-directives.jsonl --result-contract examples/valid-verification-result-contract.yaml --require-transition-ready
validate-loopback:
	$(VALIDATOR) --kind package $(BASE) --output examples/valid-output-bounded-loopback.yaml --executions examples/valid-verification-executions-bounded-loopback.jsonl --falsifications examples/valid-falsification-attempts-bounded-loopback.jsonl --findings examples/valid-findings-bounded-loopback.jsonl --directives examples/valid-directives-bounded-loopback.jsonl --result-contract examples/valid-verification-result-contract-bounded-loopback.yaml
test:
	$(PYTHON) -m unittest -v tests/test_validator.py
schemas:
	$(PYTHON) -c "import json,glob; [json.load(open(p)) for p in glob.glob('schemas/*.json')]; print('schemas valid')"
checksums:
	sha256sum -c CHECKSUMS.sha256
