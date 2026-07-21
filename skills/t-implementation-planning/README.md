# Implementation Planning Skill Package

Ready-to-use, evidence-gated Implementation Planning phase for the governed AI engineering lifecycle.

The package converts a human-approved solution contract into a comprehensive implementation plan while prohibiting code modification and unapproved semantic decisions.

## Included artifacts

- `SKILL.md`
- input/output and record-level JSON Schemas
- YAML, JSONL, CSV, and Markdown templates
- approved-contract normalization into stable planning targets
- atomic implementation plan items
- dependency DAG and topological-order validation
- coverage matrix
- verification and rollback plans
- semantic-decision guard
- actual-code change-surface reconciliation
- lifecycle routing and loopback rules
- CLI validator
- valid and invalid examples
- automated tests

## Install

```bash
python -m pip install -r validators/requirements.txt
```

## Validate the transition-ready example

```bash
make validate-example
```

## Validate loopback routes

```bash
make validate-routes
```

## Validate all schemas

```bash
make schemas
```

## Run tests

```bash
make test
```

## Direct CLI

```bash
python validators/validate.py --help
```

The transition-ready package must pass with:

```text
VALID and transition-ready for PLAN_CRITIQUE
```
