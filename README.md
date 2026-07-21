# t-think Governed Multi-Agent SDLC

`t-think` is a globally installable, evidence-gated software-engineering orchestrator for OpenCode, Codex, Claude Code, and Cursor. It coordinates eight role subagents and fifteen progressively loaded `t-*` phase skills without adding an always-on project instruction file.

The package is designed to keep semantic decisions with the human, keep source writes bounded to an approved checklist, separate producers from critics and reviewers, and preserve traceability from the original problem through verification and final closure.

## Architecture

```text
Human
  │ decisions, critique, approvals, execution authorization
  ▼
t-think                         control plane; never implements source
  ├── t-investigator            evidence gathering
  ├── t-modeler                 system model and solution options
  ├── t-planner                 implementation plan and atomic checklist
  ├── t-critic                  independent adversarial critique
  ├── t-builder                 sole authorized source writer
  ├── t-reviewer                independent technical review
  ├── t-verifier                reproducible tests and falsification
  └── t-reconciler              end-to-end traceability audit
```

The topology is a star and delegation depth is one. Workers return structured artifacts to `t-think`; workers never invoke one another. Each worker receives one phase, one skill, a bounded artifact set, explicit completion criteria, and an output schema.

## Lifecycle

```text
t-problem-alignment
→ t-investigation
→ t-system-modeling
→ t-model-critique
→ t-solution-design
→ t-solution-critique
→ t-implementation-planning
→ t-plan-critique
→ t-checklist-builder
→ t-checklist-critique
→ t-bounded-implementation
→ t-self-review
→ t-technical-review
→ t-verification
→ t-reconciliation
→ COMPLETED
```

Every skill contains its own `SKILL.md`, schemas, templates, validators, transition contract, examples, and tests. The phase router in `orchestrator/phase-registry.yaml` maps every lifecycle state to exactly one authorized role and one active skill.

## Role and phase mapping

| Phase | Role | Source-write mode |
|---|---|---|
| Problem alignment | `t-think` | denied |
| Investigation | `t-investigator` | denied |
| System model / solution design | `t-modeler` | denied |
| Model / solution / plan / checklist critique | `t-critic` | denied |
| Implementation plan / checklist | `t-planner` | denied |
| Bounded implementation | `t-builder` | approved targets only |
| Self-review | `t-builder`, fresh invocation | denied |
| Technical review | `t-reviewer` | denied |
| Verification | `t-verifier` | declared generated outputs only |
| Reconciliation | `t-reconciler` | denied |

## Workspace and `.gitignore` policy

`.gitignore` is used only for default discovery. It is not treated as a confidentiality, authorization, or write boundary.

```text
VCS ignore rules          default discovery behavior
approved_write_targets    source-change authorization
protected_paths           sensitive or structurally unsafe paths
outside_workspace         filesystem containment
```

Defaults:

- searches respect VCS ignore rules;
- normal tracked and untracked workspace files may be read when relevant;
- ignored-file reads are denied unless a recorded human approval explicitly authorizes them;
- access outside the active workspace is denied;
- `.git/**`, `.env*`, secret directories, credentials, and private keys remain protected;
- only `t-builder` during `BOUNDED_IMPLEMENTATION` may modify source;
- the builder may modify only targets frozen in the human-approved implementation checklist;
- an empty `approved_write_targets` list means no source writes;
- `t-verifier` may create only declared build, test, and report outputs.

Platform-native permissions provide the first layer. Delegation validation and post-run boundary auditing provide the portable enforcement layer where a platform cannot express path-level rules exactly.

## Requirements

- Python 3.10+
- `jsonschema`
- `PyYAML`
- GNU Make for the complete test suite
- `zip`, `unzip`, and `sha256sum` for packaging verification

```bash
python3 -m pip install jsonschema PyYAML
```

## Global installation

### macOS, Linux, or WSL

```bash
unzip t-think-governed-sdlc-bundle.zip
cd t-think-governed-sdlc
./bin/install.sh --target all --mode copy
./bin/doctor.sh --target all
```

Use `--mode symlink` while developing the bundle. Use `copy` for a stable normal installation.

Install only one platform:

```bash
./bin/install.sh --target opencode
./bin/install.sh --target codex
./bin/install.sh --target claude
./bin/install.sh --target cursor
```

### Windows PowerShell

```powershell
Expand-Archive .\t-think-governed-sdlc-bundle.zip
cd .\t-think-governed-sdlc
.\bin\install.ps1 -Target all -Mode copy
.\bin\doctor.ps1 -Target all
```

### Installed locations

| Platform | Root orchestrator | Role subagents | Skills |
|---|---|---|---|
| OpenCode | `~/.config/opencode/agents/t-think.md` | same directory | `~/.agents/skills/t-*` |
| Codex | `~/.codex/t-think.config.toml` profile | `~/.codex/agents/t-*.toml` | `~/.agents/skills/t-*` |
| Claude Code | `~/.claude/agents/t-think.md` | same directory | `~/.claude/skills/t-*`, linked/copied from the shared store |
| Cursor | `~/.cursor/agents/t-think.md` | same directory | `~/.agents/skills/t-*` |

Global means user-level on the current machine. Install the bundle separately in a remote, containerized, or cloud execution environment that does not share the local home directory.

## Invocation

### OpenCode

Select `t-think` as the primary agent, then state the problem. OpenCode workers are installed as subagents and are allowlisted for delegation by the primary adapter.

### Codex

Run `t-think` as the root session profile:

```bash
codex --profile t-think
```

Do not launch `t-think` as a custom child agent. Codex custom agents are spawned sessions; keeping `t-think` at root depth allows it to spawn the eight terminal workers while `agents.max_depth = 1` prevents recursive delegation.

### Claude Code

```bash
claude --agent t-think
```

The root agent allowlists the eight workers. Worker definitions omit the `Agent` tool, so they cannot recursively delegate.

### Cursor

Select or invoke the global `t-think` agent in Agent mode. The adapter keeps role workers foreground and model-neutral.

## Start and route a work item

```bash
python3 bin/t-thinkctl.py init ORDER-2471 --profile economy
python3 bin/t-thinkctl.py route --file .t-think/ORDER-2471/state.yaml
```

The route output identifies the only valid phase, role, skill, context policy, and write mode. `t-think` must not choose a different worker from prose or memory.

Prepare a delegation packet:

```bash
python3 bin/t-thinkctl.py prepare-delegation \
  --file .t-think/ORDER-2471/state.yaml \
  --objective "Trace the actual order creation and retry path" \
  --criterion "Identify every entry point" \
  --criterion "Identify the transaction boundary" \
  --criterion "Identify database uniqueness enforcement"
```

For bounded implementation, pass only checklist-approved write targets:

```bash
python3 bin/t-thinkctl.py prepare-delegation \
  --file .t-think/ORDER-2471/state.yaml \
  --objective "Execute the authorized checklist" \
  --criterion "Complete each item without a new semantic decision" \
  --approved-write-target src/main/java/com/acme/order/OrderService.java \
  --approved-write-target src/test/java/com/acme/order/OrderServiceTest.java \
  --generated-output target/**
```

## Validate every worker handoff

```bash
python3 bin/validate_delegation.py --file delegation.yaml
python3 bin/audit_boundaries.py --delegation delegation.yaml --activity activity.yaml
python3 bin/validate_result.py \
  --result result.yaml \
  --delegation delegation.yaml \
  --boundary-report boundary-report.yaml
```

A worker's prose is never enough to advance lifecycle state. `t-think` accepts a phase only after schema validation, semantic checks, artifact-digest checks, phase validation, and a passing boundary report.

## Model profiles

The default is `economy`:

- models are inherited from the platform or session;
- no flagship model or reasoning tier is pinned;
- exactly one phase skill is active;
- exactly one worker runs at a time;
- each worker starts with a fresh, bounded context;
- templates and enumerated statuses precede prose;
- raw logs remain evidence files rather than conversation history;
- missing semantics produce `UNKNOWN`, `BLOCKED`, or loopback—not guesses;
- validators control transitions externally.

`balanced` permits at most two independent read-only shards. `high-assurance` permits at most four independent read-only review or verification shards. Source edits, migrations, human gates, lifecycle transitions, and reconciliation remain sequential in every profile.

A stronger model is an explicit escalation path, not a lifecycle dependency. Escalation triggers include repeated phase failure, contradictory material evidence, security boundaries, destructive migration, unproven concurrency invariants, unresolved producer/critic disagreement, or nondeterministic verification failure.

## Failure and loopback behavior

- Schema failure: one constrained retry containing validator errors.
- Semantic incompleteness: one constrained retry containing missing completion criteria.
- Second failure: return control to `t-think` without a transition.
- Boundary violation: invalidate immediately; do not auto-retry.
- New semantic decision during implementation: mark `IMPLEMENTATION_FAILED` and loop back to the earliest owning phase.
- Artifact digest drift: invalidate downstream approvals.
- Critique disagreement: preserve both positions and request evidence or human resolution.

## Example delegation artifacts

`examples/subagent-delegation/` contains a complete investigation handoff:

- delegation packet;
- recorded activity;
- boundary report;
- result envelope;
- validation commands.

`examples/e2e-duplicate-order/` contains the complete governed lifecycle simulation for a Java/Jakarta REST, PostgreSQL, and Kafka duplicate-order scenario, including human critique, loopbacks, solution trade-offs, plan correction, checklist decomposition, independent review, verification, and reconciliation.

## Validation and tests

```bash
make adapters     # regenerate all native adapters from canonical role definitions
make audit        # lifecycle, skill, role, and adapter alignment
make subagents    # routing, authority, boundaries, result contracts, negative cases
make smoke        # isolated copy/symlink install, doctor, uninstall, state routing
make economy      # model neutrality and bounded-context contracts
make validate     # transition-ready and loopback examples for all phase skills
make test         # all phase unit tests
make archives     # rebuild standalone skill ZIPs
make checksums    # regenerate and verify checksums
make verify       # complete verification set
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

The uninstaller removes only paths recorded in `~/.local/share/t-think/installation-manifest.json`. Files replaced using `--force` are timestamp-backed-up and can be restored.

## Identifier rule

Installed and invocable skill names always use `t-*`. Some phase artifact schemas retain immutable producer identifiers such as `problem-alignment-skill`; these are schema contract values, not additional skills or migration aliases. The explicit mapping is in `orchestrator/contract-id-map.yaml`.

## Assurance boundary

The package can validate its schemas, routing, permissions contracts, negative boundary cases, lifecycle transitions, installers, archives, checksums, and all included unit tests offline. Native behavior can still be affected by the installed version, account policy, runtime overrides, or managed configuration of a third-party platform. Portable boundary validators remain mandatory even when native permissions are present.