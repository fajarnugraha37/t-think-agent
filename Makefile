PYTHON ?= python3
.PHONY: resources adapters paths permissions schemas graphify intake-workspace sessions audit subagents lanes smoke economy validate test skill-checksums archives checksums verify clean

resources:
	$(PYTHON) scripts/update_skill_resource_indexes.py

adapters:
	$(PYTHON) scripts/generate_adapters.py

paths:
	$(PYTHON) scripts/path_template_contract_test.py

permissions:
	$(PYTHON) scripts/permission_contract_test.py

schemas:
	$(PYTHON) scripts/schema_metaschema_test.py

graphify:
	$(PYTHON) scripts/graphify_contract_test.py

subagents:
	$(PYTHON) scripts/subagent_contract_test.py

intake-workspace:
	$(PYTHON) scripts/intake_workspace_contract_test.py

sessions:
	$(PYTHON) scripts/session_continuity_contract_test.py

lanes:
	$(PYTHON) scripts/lane_contract_test.py

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

skill-checksums:
	$(PYTHON) scripts/generate_skill_checksums.py

archives: skill-checksums
	$(PYTHON) scripts/rebuild_archives.py

checksums: archives
	$(PYTHON) scripts/generate_checksums.py
	sha256sum -c CHECKSUMS.sha256
	@for skill in skills/t-*; do (cd "$$skill" && sha256sum -c CHECKSUMS.sha256 >/dev/null) || exit 1; done

verify: resources adapters paths permissions schemas graphify intake-workspace sessions audit subagents lanes smoke economy validate test checksums
	@echo "t-think multi-agent bundle verification completed"

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
