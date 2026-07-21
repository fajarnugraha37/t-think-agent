# t-think Governed Multi-Agent SDLC

`t-think` is a globally installable, evidence-gated software-engineering orchestrator for OpenCode, Codex, Claude Code, and Cursor. It coordinates one root orchestrator, eight terminal role workers, and fifteen progressively loaded `t-*` phase skills.

Version 2.2 adds adaptive `quick`, `standard`, and `full` governance lanes. Daily patches can use a short path while security-sensitive, irreversible, cross-service, compatibility-sensitive, and architecturally complex work still uses the complete lifecycle.

Repository maintainers and coding agents must read [`AGENTS.md`](AGENTS.md) before changing this bundle. That file is the portable continuity contract for developing t-think itself; it is not installed into governed target repositories.

## Architecture

```text
Human
  │ semantic decisions, critique, approvals, execution authorization
  ▼
t-think                         sole control plane and state transition owner
  ├── t-investigator            evidence gathering
  ├── t-modeler                 system model and solution design
  ├── t-planner                 plan and atomic checklist
  ├── t-critic                  adversarial critique
  ├── t-builder                 sole bounded source writer
  ├── t-reviewer                independent technical review
  ├── t-verifier                reproducible verification and falsification
  └── t-reconciler              standard/full traceability closure
```

Delegation is a star with maximum depth one. Workers never invoke workers. Each invocation receives one phase, one skill, bounded inputs, explicit completion criteria, a schema, and a permission envelope.

## Adaptive governance lanes

### Quick

```text
PROBLEM_ALIGNMENT
→ BOUNDED_IMPLEMENTATION
→ SELF_REVIEW
→ VERIFICATION
→ RECONCILIATION
→ COMPLETED
```

Use for a small, local, reversible patch with established expected behavior and bounded targets. Quick uses only two worker role types:

- `t-builder` for implementation;
- a fresh write-denied `t-builder` invocation for self-review;
- `t-verifier` for independent command-driven verification.

Quick reconciliation is deterministic root work by `t-think`. It may summarize and reconcile validated evidence, but may not repair code or invent missing semantics. One human write-authorization gate is required before implementation.

### Standard

```text
PROBLEM_ALIGNMENT
→ INVESTIGATION
→ SOLUTION_DESIGN
→ IMPLEMENTATION_PLAN
→ BOUNDED_IMPLEMENTATION
→ TECHNICAL_REVIEW
→ VERIFICATION
→ RECONCILIATION
→ COMPLETED
```

Use for small-to-medium features, local refactors, and non-trivial bugs that require evidence, a solution decision, planning, and independent review.

### Full

```text
PROBLEM_ALIGNMENT
→ INVESTIGATION
→ SYSTEM_MODEL
→ MODEL_CRITIQUE
→ SOLUTION_DESIGN
→ SOLUTION_CRITIQUE
→ IMPLEMENTATION_PLAN
→ PLAN_CRITIQUE
→ IMPLEMENTATION_CHECKLIST
→ CHECKLIST_CRITIQUE
→ BOUNDED_IMPLEMENTATION
→ SELF_REVIEW
→ TECHNICAL_REVIEW
→ VERIFICATION
→ RECONCILIATION
→ COMPLETED
```

Full remains the canonical lifecycle. It is forced for hard-risk triggers and is the compatibility default for work states created before v2.2.

Every compressed work item stores a validated lane assessment and explicit phase-waiver artifact. Waived phases do not receive empty placeholder artifacts and cannot be routed until the lane is promoted.

See [`docs/adaptive-governance-lanes.md`](docs/adaptive-governance-lanes.md).

## Lane classification

The deterministic policy lives in `orchestrator/risk-classification-policy.yaml`.

Hard triggers force `full`:

- security, authentication, authorization, cryptography, or sensitive-data boundary;
- destructive or irreversible migration;
- public breaking API, protocol, package export, or serialized contract;
- concurrency, ordering, locking, memory-model, idempotency, or distributed consistency invariant;
- billing, pricing, money movement, ledger, or financial correctness;
- secrets, credentials, IAM, signing keys, or privileged deployment identity;
- irreversible operation without a tested recovery path;
- cross-service protocol or coordinated rollout.

Auto classification without reliable signals selects `standard`, never `quick`. Quick additionally requires a bounded/reversible qualifier such as an existing reproduction, documentation-only scope, test-only scope, or an explicitly local reversible patch.

Lane transitions are monotonic:

```text
quick → standard → full
```

Demotion is forbidden. Promotion after compressed work has progressed returns to the earliest newly required phase instead of silently continuing implementation.

## Workspace and write boundaries

`.gitignore` controls default discovery only. It is not a confidentiality or authorization boundary.

```text
VCS ignore rules          discovery behavior
approved_write_targets    source-change authorization
protected_paths           sensitive/structural protection
outside_workspace         filesystem containment
```

Defaults:

- relevant tracked and untracked workspace files may be read;
- ignored-file reads require recorded human approval;
- outside-workspace access is denied;
- `.git/**`, `.env*`, secrets, credentials, and private keys are protected;
- only `t-builder` during `BOUNDED_IMPLEMENTATION` may modify source;
- source writes are limited to approved targets;
- an empty target list authorizes no source writes;
- `SELF_REVIEW` is write-denied;
- `t-verifier` may write only declared generated outputs;
- every worker result requires a passing boundary report.

## Requirements

- Python 3.10+
- `jsonschema`
- `PyYAML`
- GNU Make for the complete test suite
- `zip`, `unzip`, and `sha256sum` for package verification

```bash
python3 -m pip install jsonschema PyYAML
```

## Installation

### macOS, Linux, or WSL

```bash
unzip t-think-governed-sdlc-bundle.zip
cd t-think-governed-sdlc
./bin/install.sh --target all --mode copy
./bin/doctor.sh --target all
```

Install one platform only:

```bash
./bin/install.sh --target opencode
./bin/install.sh --target codex
./bin/install.sh --target claude
./bin/install.sh --target cursor
```

Use `--mode symlink` while developing the bundle. Use `copy` for normal stable installation.

### Windows PowerShell

```powershell
Expand-Archive .\t-think-governed-sdlc-bundle.zip
cd .\t-think-governed-sdlc
.\bin\install.ps1 -Target all -Mode copy
.\bin\doctor.ps1 -Target all
```

### Installed locations

| Platform | Root orchestrator | Role workers | Skills |
|---|---|---|---|
| OpenCode | `~/.config/opencode/agents/t-think.md` | same directory | `~/.agents/skills/t-*` |
| Codex | `~/.codex/t-think.config.toml` | `~/.codex/agents/t-*.toml` | `~/.agents/skills/t-*` |
| Claude Code | `~/.claude/agents/t-think.md` | same directory | `~/.claude/skills/t-*` |
| Cursor | `~/.cursor/agents/t-think.md` | same directory | `~/.agents/skills/t-*` |

“Global” means user-level within the current machine, container, remote host, or cloud environment. Install separately when home directories are not shared.

## Invocation

### OpenCode

Select `t-think` as the primary agent and describe the problem. The root adapter allowlists the eight terminal workers.

### Codex

```bash
codex --profile t-think
```

`t-think` must be the root session profile. Codex custom agents are terminal child sessions, and `agents.max_depth = 1` prevents recursive delegation.

### Claude Code

```bash
claude --agent t-think
```

### Cursor

Select or invoke the global `t-think` agent in Agent mode.

## Classify and initialize work

Classify without creating state:

```bash
python3 bin/t-thinkctl.py classify BUG-123 \
  --task "Fix the local parser bug covered by an existing failing test" \
  --signal local_reversible \
  --signal existing_reproduction
```

Initialize with automatic classification:

```bash
python3 bin/t-thinkctl.py init BUG-123 \
  --profile economy \
  --lane auto \
  --task "Fix the local parser bug covered by an existing failing test" \
  --signal local_reversible \
  --signal existing_reproduction
```

No signals defaults to standard:

```bash
python3 bin/t-thinkctl.py init FEATURE-42 --profile economy
```

Explicit lane selection:

```bash
python3 bin/t-thinkctl.py init PATCH-9 --lane quick \
  --signal local_reversible \
  --signal existing_reproduction

python3 bin/t-thinkctl.py init AUTH-9 --lane full \
  --signal security_boundary
```

A hard trigger overrides an unsafe lower-lane request and records the forced promotion.

## Route and delegate

```bash
python3 bin/t-thinkctl.py route \
  --file .t-think/BUG-123/state.yaml
```

The route includes lane, artifact mode, active phase, skill, worker, next state, write mode, context policy, and human-gate requirements.

Prepare a bounded implementation delegation:

```bash
python3 bin/t-thinkctl.py prepare-delegation \
  --file .t-think/BUG-123/state.yaml \
  --objective "Apply the approved local parser patch" \
  --criterion "The failing regression test passes" \
  --criterion "Existing tests remain green" \
  --approved-write-target src/parser.ts \
  --approved-write-target tests/parser.test.ts \
  --generated-output dist/**
```

Every v2.2 delegation packet binds:

```yaml
lifecycle:
  lane: quick
  artifact_mode: compact
  expected_next_state: SELF_REVIEW
```

## Promote a lane

```bash
python3 bin/t-thinkctl.py promote \
  --file .t-think/BUG-123/state.yaml \
  --lane standard \
  --reason "The root cause spans a shared utility and two modules" \
  --signal shared_utility \
  --signal multiple_modules
```

Previous lane assessments and waivers are preserved as versioned artifacts. Promotion cannot move downward.

## Validate worker handoffs

```bash
python3 bin/validate_delegation.py --file delegation.yaml
python3 bin/audit_boundaries.py \
  --delegation delegation.yaml \
  --activity activity.yaml
python3 bin/validate_result.py \
  --result result.yaml \
  --delegation delegation.yaml \
  --boundary-report boundary-report.yaml
```

Worker prose is never sufficient to advance state. Schema, semantics, artifact digests, lane transition, and boundary validation must all pass.

## Economy-model behavior

The default `economy` profile:

- inherits the host model and reasoning settings;
- runs one active skill and one sequential worker;
- uses fresh bounded worker contexts;
- applies lane-specific source/evidence budgets;
- saves raw command output as evidence;
- converts missing semantics into `UNKNOWN`, `BLOCKED`, loopback, or promotion;
- uses validators and command exit codes as external memory;
- promotes governance before escalating model cost when scope or risk changes.

A stronger model is an explicit exception path, not a correctness dependency.

## Validation and tests

```bash
make adapters     # regenerate all native adapters
make audit        # canonical alignment
make subagents    # authority, permissions, result contracts, negative cases
make lanes        # classifier, paths, waivers, promotion, legacy compatibility
make economy      # model neutrality and context-budget contracts
make smoke        # isolated install/doctor/uninstall and runtime smoke
make validate     # all phase validators
make test         # all phase unit tests
make archives     # standalone skill ZIP files
make checksums    # regenerate and verify root integrity inventory
make verify       # complete repository acceptance set
```

## Uninstall

```bash
./bin/uninstall.sh
./bin/uninstall.sh --restore-backups
```

PowerShell:

```powershell
.\bin\uninstall.ps1
.\bin\uninstall.ps1 -RestoreBackups
```

The uninstaller removes only paths recorded in the t-think installation manifest.

## Assurance boundary

The bundle can verify its schemas, classifier, lane routing, phase waivers, monotonic promotion, permissions, negative boundary cases, lifecycle contracts, installers, archives, checksums, and included tests offline. Native platform behavior may still depend on the installed CLI version, account policy, managed configuration, or runtime overrides. Portable validators remain authoritative for lifecycle transitions.
