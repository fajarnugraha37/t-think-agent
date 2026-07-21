# Investigation Skill Package

A production-oriented, evidence-gated investigation skill for AI engineering agents.

This package is designed to run after an approved `t-problem-alignment` phase and before `system-modelling`.

## Included

- `SKILL.md` — operational behavior and prohibitions
- JSON Schemas for input, output, evidence records, critique, and sufficiency decisions
- YAML/Markdown/JSONL templates
- Cross-file semantic validator
- Transition-gate validation for `SYSTEM_MODEL`
- Valid and invalid examples
- Automated tests
- Orchestrator transition contract

## Quick start

```bash
cd t-investigation
python -m venv .venv
. .venv/bin/activate
pip install -r validators/requirements.txt

python validators/validate.py --kind input --file examples/valid-input.yaml
python validators/validate.py --kind ledger --file examples/valid-evidence-ledger.jsonl
python validators/validate.py \
  --kind output \
  --file examples/valid-output-ready.yaml \
  --ledger examples/valid-evidence-ledger.jsonl \
  --require-transition-ready

python -m unittest discover -s tests -v
```

## Canonical outputs

```text
artifacts/01-investigation-log.md
artifacts/02-evidence-ledger.jsonl
artifacts/02a-investigation-output.yaml
```

## Design principles

1. Actual repository/runtime evidence outranks memory and conversation context.
2. Conversation context may guide search but cannot become a system fact without verification.
3. Every material claim is typed and traceable.
4. Negative claims must state inspected scope.
5. Evidence sufficiency is a gate, not a feeling.
6. Investigation is read-only unless explicit authorization says otherwise.
7. `READY_FOR_SYSTEM_MODEL` requires cross-file consistency between output and evidence ledger.
