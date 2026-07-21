# t-think Governed Multi-Agent SDLC

`t-think` is a globally installable, evidence-gated software-engineering orchestrator for OpenCode, Codex, Claude Code, and Cursor. Version 2.3.1 coordinates one root orchestrator, ten terminal workers, twenty progressively loaded `t-*` skills, three adaptive governance lanes, and twelve canonical lifecycle phases.

Repository maintainers and coding agents must read [`AGENTS.md`](AGENTS.md) before changing the bundle.

## Architecture

```text
Human
  │ semantic decisions, approvals, execution authorization
  ▼
t-think                         root control plane and transition owner
  ├── t-investigator            repository/runtime evidence
  ├── t-modeler                 system model and solution design
  ├── t-planner                 blueprint strategy and execution checklist
  ├── t-critic                  model, solution, and blueprint critique
  ├── t-builder                 bounded source implementation and self-review
  ├── t-reviewer                independent technical review
  ├── t-security-reviewer       dedicated security review
  ├── t-breaking-reviewer       semantic and contract-breaking review
  ├── t-verifier                reproducible executable verification
  └── t-reconciler              end-to-end traceability and closure audit
```

The topology is a star with maximum delegation depth one. Workers never invoke workers. Each invocation receives one bounded objective, one active skill, explicit inputs, a permission envelope, completion criteria, output schema, and boundary-report obligation.

## Governance lanes

### Quick — 5 phases

```text
PROBLEM_ALIGNMENT
→ BOUNDED_IMPLEMENTATION
→ IMPLEMENTATION_REVIEW
→ VERIFICATION
→ RECONCILIATION
→ COMPLETED
```

Quick is limited to local, reversible work with established expected behavior and bounded write targets. `IMPLEMENTATION_REVIEW` always runs two fresh tracks:

- `self_review` — fresh, write-denied `t-builder`;
- `technical_review` — independent `t-reviewer`.

### Standard — 9 phases

```text
PROBLEM_ALIGNMENT
→ INVESTIGATION
→ SOLUTION_DESIGN
→ IMPLEMENTATION_BLUEPRINT
→ BLUEPRINT_CRITIQUE
→ BOUNDED_IMPLEMENTATION
→ IMPLEMENTATION_REVIEW
→ VERIFICATION
→ RECONCILIATION
→ COMPLETED
```

Standard is the conservative default for small-to-medium features, local refactors, and non-trivial defects. Its implementation review always runs:

- `self_review`;
- `technical_review`;
- `security_review`;
- `breaking_review`.

### Full — 12 phases

```text
PROBLEM_ALIGNMENT
→ INVESTIGATION
→ SYSTEM_MODEL
→ MODEL_CRITIQUE
→ SOLUTION_DESIGN
→ SOLUTION_CRITIQUE
→ IMPLEMENTATION_BLUEPRINT
→ BLUEPRINT_CRITIQUE
→ BOUNDED_IMPLEMENTATION
→ IMPLEMENTATION_REVIEW
→ VERIFICATION
→ RECONCILIATION
→ COMPLETED
```

Full is mandatory for high-risk, cross-boundary, irreversible, security-sensitive, compatibility-sensitive, concurrency-sensitive, financial, or architecturally complex work.

Lane promotion is monotonic:

```text
quick → standard → full
```

Automatic demotion is forbidden. Promotion returns to the earliest newly required phase.

## Composite phases

A composite phase is one lifecycle state containing several separately delegated, fresh-context tracks. A track cannot advance lifecycle by itself; only the validated aggregate phase artifact can.

```text
IMPLEMENTATION_BLUEPRINT
├── strategy                 t-planner / t-implementation-planning
└── execution_checklist      fresh t-planner / t-checklist-builder

BLUEPRINT_CRITIQUE
├── strategy_critique        t-critic / t-plan-critique
└── execution_critique       fresh t-critic / t-checklist-critique

IMPLEMENTATION_REVIEW
├── self_review              fresh write-denied t-builder / t-self-review
├── technical_review         t-reviewer / t-technical-review
├── security_review          t-security-reviewer / t-security-review
└── breaking_review          t-breaking-reviewer / t-breaking-review
```

Security and breaking reviews run in standard and full. They may return `NOT_APPLICABLE` only after their full checklist is evaluated and a specific applicability reason is recorded. Self-review and independent technical review are mandatory in every lane.

## Workspace and write boundaries

`.gitignore` controls discovery defaults; it is not an authorization or confidentiality boundary.

```text
VCS ignore rules          discovery behavior
approved_write_targets    source-change authorization
protected_paths           sensitive/structural protection
outside_workspace         filesystem containment
```

Defaults:

- only `t-builder` during `BOUNDED_IMPLEMENTATION` may modify product source;
- writes are limited to human-approved targets;
- an empty target list authorizes no product-source writes;
- every composite track is source-write denied, including self-review;
- `t-verifier` may create only declared generated outputs;
- `.git/**`, `.env*`, secrets, credentials, and private keys are protected;
- every worker result requires a passing boundary report.

## Portable skill-resource paths

Every skill contains a generated `RESOURCE_INDEX.md`. Templates, schemas, validators, examples, supporting docs, and transition contracts are referenced relative to the directory containing `SKILL.md`.

Canonical resource identifier:

```text
templates/output.template.yaml
```

Never construct paths such as a user-specific absolute directory, `~` followed by backslashes, `%USERPROFILE%` concatenation, or a drive-letter path inside a skill instruction. Use the platform-native skill/resource loader. If an absolute filesystem path is unavoidable, join the discovered skill root and portable relative identifier with the host path API.

OpenCode adapters deny arbitrary external access but recursively allow read access to trusted t-think skill/runtime roots using `/**`; those roots are explicitly edit-denied. If a required resource cannot be opened, the agent must return:

```text
BLOCKED: SKILL_RESOURCE_UNAVAILABLE
```

It must not reconstruct the template from memory.

Resolve a resource deterministically:

```bash
python3 bin/t-thinkctl.py paths \
  --skill t-reconciliation \
  --resource templates/output.template.yaml
```

Print only the native path:

```bash
python3 bin/t-thinkctl.py paths \
  --skill t-reconciliation \
  --resource templates/output.template.yaml \
  --native-only
```

On an installed bundle, use the runtime CLI at the native location under the current user's t-think runtime. The resolver reads the installation manifest and works with home directories containing spaces or Unicode. See [`docs/portable-path-contract.md`](docs/portable-path-contract.md).

## Requirements

- Python 3.10+
- `jsonschema`
- `PyYAML`
- GNU Make for aggregate verification
- `zip`, `unzip`, and `sha256sum` for packaging checks

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

Install a single platform:

```bash
./bin/install.sh --target opencode
./bin/install.sh --target codex
./bin/install.sh --target claude
./bin/install.sh --target cursor
```

Use `--mode symlink` for bundle development on platforms where symlinks are available. Use `copy` for stable installation.

### Windows PowerShell

```powershell
Expand-Archive .\t-think-governed-sdlc-bundle.zip
Set-Location .\t-think-governed-sdlc
.\bin\install.ps1 -Target all -Mode copy
.\bin\doctor.ps1 -Target all
```

Windows copy mode is the portable default. The installed files may be displayed by Windows tools with backslashes, but all identifiers embedded in skills remain relative and `/`-separated.

### Installed locations

| Platform | Root orchestrator | Terminal workers | Skills |
|---|---|---|---|
| OpenCode | `~/.config/opencode/agents/t-think.md` | same directory | `~/.agents/skills/t-*` |
| Codex | `~/.codex/t-think.config.toml` | `~/.codex/agents/t-*.toml` | `~/.agents/skills/t-*` |
| Claude Code | `~/.claude/agents/t-think.md` | same directory | `~/.claude/skills/t-*` |
| Cursor | `~/.cursor/agents/t-think.md` | same directory | `~/.agents/skills/t-*` |

These are conceptual user-home locations. The installer resolves them through the host path API; agents must not manually derive Windows variants from this table.

## Invocation

### OpenCode

Select `t-think` as the primary agent. The root adapter allowlists the ten terminal workers and recursively read-allows only trusted global skill/runtime paths outside the worktree.

### Codex

```bash
codex --profile t-think
```

The root session owns orchestration. `agents.max_depth = 1` prevents recursive delegation.

### Claude Code

```bash
claude --agent t-think
```

### Cursor

Select the global `t-think` agent in Agent mode.

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

No reliable signals defaults to standard:

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

A hard trigger overrides an unsafe lower-lane request.

## Route and delegate

```bash
python3 bin/t-thinkctl.py route \
  --file .t-think/FEATURE-42/state.yaml
```

Composite phases require one explicit track per delegation:

```bash
python3 bin/t-thinkctl.py prepare-delegation \
  --file .t-think/FEATURE-42/state.yaml \
  --track security_review \
  --objective "Review the actual change for security regressions" \
  --criterion "Evaluate every required security category"
```

The packet remains bound to `IMPLEMENTATION_REVIEW`; completing `security_review` alone cannot advance to verification.

Promote a lane:

```bash
python3 bin/t-thinkctl.py promote \
  --file .t-think/FEATURE-42/state.yaml \
  --lane full \
  --reason "The change now crosses an authorization boundary" \
  --signal security_boundary
```

## Validation

Run the focused cross-platform resource audit:

```bash
make paths
```

Run the full bundle verification:

```bash
make verify
```

Important checks include:

- 12-phase lifecycle and lane routing;
- composite-track activation and aggregation;
- subagent authority and write boundaries;
- all skill schemas, templates, validators, and unit tests;
- 20 generated portable resource indexes;
- structured parsing of every indexed resource;
- recursive OpenCode external-directory rules;
- deterministic Linux, macOS, and Windows path semantics;
- installation and resource resolution under a home path containing spaces and Unicode;
- platform adapter generation;
- standalone skill archives and root checksums.

## Package layout

```text
AGENTS.md
VERSION
orchestrator/              lifecycle, lane, risk, composite, and role policies
agents/                    ten terminal worker definitions
skills/                    twenty canonical/component skill packages
adapters/                  OpenCode, Codex, Claude Code, and Cursor artifacts
bin/                       installer, doctor, runtime, validators, path resolver
schemas/                   cross-package schemas
scripts/                   generators, audits, tests, archive/checksum tooling
templates/                 root work-state templates
docs/                      architecture and operating contracts
reports/                   generated verification summaries
archives/                  standalone skill ZIPs
```

## Assurance boundary

The bundle can deterministically validate topology, permissions, paths, schemas, lifecycle transitions, track requirements, evidence references, and executable checks. It cannot guarantee that a model correctly infers undocumented product semantics. Missing evidence, inaccessible skill resources, ambiguity, contradictory evidence, or repeated validation failure must block or escalate rather than be guessed.
