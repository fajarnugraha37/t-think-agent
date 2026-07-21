PYTHON ?= python3
.PHONY: adapters audit subagents smoke economy validate test archives checksums verify clean

adapters:
	$(PYTHON) scripts/generate_adapters.py

subagents:
	$(PYTHON) scripts/subagent_contract_test.py

audit:
	$(PYTHON) scripts/audit_alignment.py

smoke:
	$(PYTHON) scripts/smoke_test.py

economy:
	$(PYTHON) scripts/economy_contract_test.py

validate:
	$(PYTHON) scripts/run_all_tests.py --mode validate

test:
	$(PYTHON) scripts/run_all_tests.py --mode test

archives:
	$(PYTHON) scripts/rebuild_archives.py

checksums:
	$(PYTHON) scripts/generate_checksums.py
	sha256sum -c CHECKSUMS.sha256

verify: adapters audit subagents smoke economy validate test checksums
	@echo "t-think multi-agent bundle verification completed"

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
