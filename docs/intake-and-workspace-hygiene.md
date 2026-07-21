# Intake and workspace hygiene contract

## `/t-problem-alignment` bootstrap

For a direct invocation:

```text
/t-problem-alignment [problem statement]
```

the first response asks exactly two questions, in order:

1. `Apa work ID atau nomor tiketnya?` with one suggested ID.
2. `Pilih lane yang akan digunakan: quick, standard, atau full?`

No repository read, `.t-think` directory creation, lane auto-selection, or artifact write is allowed before both answers are explicit.

Generate the deterministic prompt payload without touching the repository:

```bash
python3 bin/t-thinkctl.py intake \
  --task "Fix raw capture mapping bug" \
  --format json
```

After both answers, initialize the selected lane:

```bash
python3 bin/t-thinkctl.py init REQ-001 \
  --lane standard \
  --task "Fix raw capture mapping bug"
```

The only valid work directory is:

```text
.t-think/REQ-001/
```

## Canonical work layout

```text
.t-think/
└── <work-id>/
    ├── state.yaml
    ├── artifacts/
    ├── delegations/
    ├── results/
    ├── boundary-reports/
    ├── evidence/
    └── scratch/
```

Phase artifacts may not be written directly under `.t-think/` or directly under `.t-think/<work-id>/`.

Every delegation packet binds both:

```yaml
workspace:
  active_work_directory: .t-think/REQ-001
permissions:
  governance_artifact_write: .t-think/REQ-001/**
```

The broad permission `.t-think/**` is invalid.

## Temporary diagnostics

A reusable product behavior check, bug reproduction, or regression guard belongs in the repository's real unit, integration, contract, or regression test suite. A one-off script is not a substitute for a permanent test.

A truly ephemeral diagnostic may exist only under:

```text
.t-think/<work-id>/scratch/
```

It must be declared as a generated output and deleted before reconciliation.

Audit the work directory:

```bash
python3 bin/t-thinkctl.py audit-workdir \
  --file .t-think/REQ-001/state.yaml
```

Clean scratch and known forbidden temporary scripts:

```bash
python3 bin/t-thinkctl.py cleanup-workdir \
  --file .t-think/REQ-001/state.yaml \
  --prune-forbidden-temporary
```

Require a clean closure state:

```bash
python3 bin/t-thinkctl.py audit-workdir \
  --file .t-think/REQ-001/state.yaml \
  --require-clean
```

`prepare-delegation` refuses to create a reconciliation delegation while the hygiene audit fails.

## Safety of cleanup

Cleanup automatically removes:

- files inside the active work item's `scratch/` directory;
- forbidden temporary script files directly under `.t-think/` or the active work root when `--prune-forbidden-temporary` is supplied.

It does not silently delete misplaced YAML/JSON/Markdown governance artifacts. Those remain visible as audit failures so an agent must relocate or reconcile them explicitly.
