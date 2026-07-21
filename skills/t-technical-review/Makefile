PYTHON ?= python3

.PHONY: validate validate-ready validate-loopback test schema checksums
schema:
	$(PYTHON) validators/validate.py --kind schema
validate: schema validate-ready validate-loopback
validate-ready:
	$(PYTHON) validators/validate.py --kind package \
  --input examples/valid-input.yaml \
  --self-review-output examples/source-valid-self-review-output.yaml \
  --self-review-contract examples/source-valid-self-review-result-contract.yaml \
  --bounded-output examples/source-valid-bounded-output.yaml \
  --implementation-contract examples/source-valid-implementation-result-contract.yaml \
  --checklist-contract examples/source-valid-approved-checklist-contract.yaml \
  --checklists examples/source-valid-checklist-items.jsonl \
  --changes examples/source-valid-change-records.jsonl \
  --verifications examples/source-valid-verification-results.jsonl \
  --repository-after examples/source-valid-repository-after.yaml \
  --ledger examples/source-valid-evidence-ledger.jsonl \
  --self-review-checks examples/source-valid-self-review-checks.jsonl \
  --self-review-conformance examples/source-valid-self-review-conformance.jsonl \
  --self-review-audits examples/source-valid-self-review-audits.jsonl \
  --self-review-findings examples/source-valid-self-review-findings.jsonl \
  --self-review-directives examples/source-valid-self-review-directives.jsonl \
  --assignment examples/valid-review-assignment.yaml \
  --output examples/valid-output-ready.yaml \
  --technical-checks examples/valid-technical-review-checks.jsonl \
  --change-assessments examples/valid-change-assessments.jsonl \
  --evidence-challenges examples/valid-evidence-challenges.jsonl \
  --findings examples/empty-review-findings.jsonl \
  --directives examples/empty-remediation-directives.jsonl \
  --result-contract examples/valid-technical-review-result-contract.yaml \
  --require-transition-ready
validate-loopback:
	$(PYTHON) validators/validate.py --kind package \
  --input examples/valid-input.yaml \
  --self-review-output examples/source-valid-self-review-output.yaml \
  --self-review-contract examples/source-valid-self-review-result-contract.yaml \
  --bounded-output examples/source-valid-bounded-output.yaml \
  --implementation-contract examples/source-valid-implementation-result-contract.yaml \
  --checklist-contract examples/source-valid-approved-checklist-contract.yaml \
  --checklists examples/source-valid-checklist-items.jsonl \
  --changes examples/source-valid-change-records.jsonl \
  --verifications examples/source-valid-verification-results.jsonl \
  --repository-after examples/source-valid-repository-after.yaml \
  --ledger examples/source-valid-evidence-ledger.jsonl \
  --self-review-checks examples/source-valid-self-review-checks.jsonl \
  --self-review-conformance examples/source-valid-self-review-conformance.jsonl \
  --self-review-audits examples/source-valid-self-review-audits.jsonl \
  --self-review-findings examples/source-valid-self-review-findings.jsonl \
  --self-review-directives examples/source-valid-self-review-directives.jsonl \
  --assignment examples/valid-review-assignment.yaml \
  --output examples/valid-output-bounded-loopback.yaml \
  --technical-checks examples/valid-technical-review-checks-bounded-loopback.jsonl \
  --change-assessments examples/valid-change-assessments-bounded-loopback.jsonl \
  --evidence-challenges examples/valid-evidence-challenges-bounded-loopback.jsonl \
  --findings examples/valid-findings-bounded-loopback.jsonl \
  --directives examples/valid-directives-bounded-loopback.jsonl \
  --result-contract examples/valid-technical-review-result-contract-bounded-loopback.yaml
test:
	$(PYTHON) -m unittest -v tests/test_validator.py
checksums:
	sha256sum -c CHECKSUMS.sha256
