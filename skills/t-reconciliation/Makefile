.PHONY: validate test schemas

validate:
	python3 validators/validate.py --kind package \
  --input examples/valid-input.yaml \
  --output examples/valid-output-complete.yaml \
  --assignment examples/valid-reconciler-assignment.yaml \
  --verification-output examples/source-valid-verification-output.yaml \
  --verification-contract examples/source-valid-verification-result-contract.yaml \
  --verification-obligations examples/source-valid-verification-obligations.jsonl \
  --verification-executions examples/source-valid-verification-executions.jsonl \
  --verification-evidence examples/source-valid-verification-evidence.jsonl \
  --technical-review-contract examples/source-valid-technical-review-result-contract.yaml \
  --implementation-contract examples/source-valid-implementation-result-contract.yaml \
  --checklist-contract examples/source-valid-approved-checklist-contract.yaml \
  --artifacts examples/valid-artifact-registry.jsonl \
  --nodes examples/valid-traceability-nodes.jsonl \
  --links examples/valid-traceability-links.jsonl \
  --closures examples/valid-closure-obligations.jsonl \
  --contradictions examples/empty-contradictions.jsonl \
  --gaps examples/empty-residual-gaps.jsonl \
  --approval examples/valid-closure-approval.yaml \
  --result-contract examples/valid-reconciliation-result-contract.yaml \
  --report examples/valid-reconciliation-report.md \
  --require-transition-ready

test:
	python3 -m unittest discover -s tests -v

schemas:
	python3 -c "import json,glob; [json.load(open(p)) for p in glob.glob('schemas/*.json')]; print('VALID')"
