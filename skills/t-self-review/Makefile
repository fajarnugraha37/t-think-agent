PYTHON ?= python3
V = $(PYTHON) validators/validate.py
ARGS = --input examples/valid-input.yaml --output examples/valid-output-ready.yaml --bounded-output examples/source-valid-bounded-output.yaml --implementation-contract examples/source-valid-implementation-result-contract.yaml --checklist-contract examples/source-valid-approved-checklist-contract.yaml --checklists examples/source-valid-checklist-items.jsonl --executions examples/source-valid-execution-records.jsonl --changes examples/source-valid-change-records.jsonl --commands examples/source-valid-command-results.jsonl --verifications examples/source-valid-verification-results.jsonl --rollbacks examples/source-valid-rollback-results.jsonl --implementation-findings examples/source-valid-implementation-findings.jsonl --repository-before examples/source-valid-repository-before.yaml --repository-after examples/source-valid-repository-after.yaml --ledger examples/source-valid-evidence-ledger.jsonl --review-checks examples/valid-review-checks.jsonl --conformance-results examples/valid-conformance-results.jsonl --evidence-audits examples/valid-evidence-audits.jsonl --findings examples/empty-review-findings.jsonl --directives examples/empty-remediation-directives.jsonl --result-contract examples/valid-self-review-result-contract.yaml
.PHONY: schema validate loopback test
schema:
	$(V) --kind schema
validate: schema
	$(V) --kind package $(ARGS) --require-transition-ready
loopback:
	$(V) --kind package $(filter-out --output examples/valid-output-ready.yaml --review-checks examples/valid-review-checks.jsonl --conformance-results examples/valid-conformance-results.jsonl --findings examples/empty-review-findings.jsonl --directives examples/empty-remediation-directives.jsonl --result-contract examples/valid-self-review-result-contract.yaml,$(ARGS)) --output examples/valid-output-bounded-loopback.yaml --review-checks examples/valid-review-checks-bounded-loopback.jsonl --conformance-results examples/valid-conformance-results-bounded-loopback.jsonl --findings examples/valid-findings-bounded-loopback.jsonl --directives examples/valid-directives-bounded-loopback.jsonl --result-contract examples/valid-self-review-result-contract-bounded-loopback.yaml
test:
	$(PYTHON) tests/test_validator.py
