# Problem Alignment Agent Skill

A production-ready skill package for the `PROBLEM_ALIGNMENT` phase of an evidence-gated AI engineering lifecycle.

## Goals

This skill ensures that the human and AI explicitly agree on the problem before investigation, modelling, solution design, planning, or implementation begins.

The skill is intentionally strict:

- no hidden assumptions;
- no reading human intent;
- no root-cause speculation;
- no solution proposal;
- no code investigation as a substitute for requirement clarification;
- no lifecycle transition without explicit human approval.

## Package contents

```text
t-problem-alignment/
├── SKILL.md
├── README.md
├── schemas/
│   ├── input.schema.json
│   ├── output.schema.json
│   └── critique.schema.json
├── templates/
│   ├── input.template.yaml
│   ├── output.template.yaml
│   ├── problem-alignment.template.md
│   └── critique.template.yaml
├── validators/
│   ├── validate.py
│   ├── validate.sh
│   └── requirements.txt
├── examples/
│   ├── valid-input.yaml
│   ├── valid-output-draft.yaml
│   ├── valid-output-approved.yaml
│   └── invalid-output-hidden-assumption.yaml
├── tests/
│   └── test_validator.py
└── orchestrator/
    └── transition-contract.yaml
```

## Quick start

Requires Python 3.11+.

```bash
cd t-problem-alignment
python -m venv .venv
source .venv/bin/activate
pip install -r validators/requirements.txt
```

Validate input:

```bash
python validators/validate.py \
  --kind input \
  --file examples/valid-input.yaml
```

Validate a draft output:

```bash
python validators/validate.py \
  --kind output \
  --file examples/valid-output-draft.yaml
```

Validate an approved output and enforce transition rules:

```bash
python validators/validate.py \
  --kind output \
  --file examples/valid-output-approved.yaml \
  --require-transition-ready
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Canonical lifecycle behavior

The skill may emit one of these gate outcomes:

- `NEEDS_HUMAN_CLARIFICATION`
- `READY_FOR_HUMAN_REVIEW`
- `APPROVED_FOR_INVESTIGATION`
- `REJECTED`

Only `APPROVED_FOR_INVESTIGATION` permits transition to the investigation skill.

## Integration

The root `AGENT.md` should route the lifecycle to this skill when the current state is `PROBLEM_ALIGNMENT`.

The orchestrator must:

1. validate input using `schemas/input.schema.json`;
2. execute `SKILL.md`;
3. validate output using `schemas/output.schema.json`;
4. run semantic validation with `validators/validate.py`;
5. require explicit human approval before transition;
6. persist the approved Markdown artifact as `artifacts/00-problem-alignment.md`;
7. pass the approved YAML/JSON output as structured input to investigation.
