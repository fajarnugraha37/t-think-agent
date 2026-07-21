# Subagent delegation example

This fixture shows `t-think` delegating `INVESTIGATION` to `t-investigator`. Discovery respects VCS ignore, source writes are denied, outside-workspace access is denied, and the worker cannot spawn another agent.

Validate it:

```bash
python3 bin/validate_delegation.py --file examples/subagent-delegation/investigation-delegation.yaml
python3 bin/audit_boundaries.py \
  --delegation examples/subagent-delegation/investigation-delegation.yaml \
  --activity examples/subagent-delegation/investigation-activity.yaml
python3 bin/validate_result.py \
  --delegation examples/subagent-delegation/investigation-delegation.yaml \
  --result examples/subagent-delegation/investigation-result.yaml \
  --boundary examples/subagent-delegation/investigation-boundary-report.yaml
```
