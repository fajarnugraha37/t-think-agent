# t-think Governed Multi-Agent SDLC

`t-think` is a globally installable, evidence-gated software-engineering orchestrator for OpenCode, Codex, Claude Code, and Cursor. Version 2.4.1 coordinates one root orchestrator, ten terminal workers, twenty progressively loaded `t-*` skills, three adaptive governance lanes, and twelve canonical lifecycle phases.

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
protected_paths           direct `.git/**` write protection
outside_workspace         filesystem containment
```

Defaults:

- `/t-problem-alignment` asks for a work ID/ticket and an explicit `quick`, `standard`, or `full` lane before any file is created;
- every work item is isolated under exactly `.t-think/<work-id>/`;
- delegation packets authorize governance writes only to `.t-think/<work-id>/**`, never broad `.t-think/**`;
- phase artifacts and temporary scripts are forbidden directly under `.t-think/` or the active work root;
- one-off diagnostics may exist only in `.t-think/<work-id>/scratch/` and must be removed before reconciliation;
- reusable behavior or regression checks must become real repository tests;
- only `t-builder` during `BOUNDED_IMPLEMENTATION` may modify product source;
- writes are limited to human-approved targets;
- an empty target list authorizes no product-source writes;
- every composite track is source-write denied, including self-review;
- `t-verifier` may create only declared generated outputs;
- direct writes below `.git/**` are always prohibited; other paths inside the project remain natively available and are governed by the active delegation;
- every worker result requires a passing boundary report.


## Prompt-free workspace tools

The generated agents use a `workspace-autonomous` tool profile. All normal operations anywhere inside the active project worktree run without approval prompts: read, search, edit, write, delete, shell commands, builds, tests, package managers, linters, formatters, diagnostics, and project-local scripts. No filename-based native denylist is applied inside the worktree except `.git/**`. External filesystem access remains deny-by-default except for installed t-think skills/runtime, which are read-only.

Tool availability is deliberately broad, while lifecycle authority remains narrow. A worker can have an edit-capable native tool but any source change outside its delegation packet still fails boundary validation.

Version-control operations are a separate hard boundary:

- `gh` is always denied;
- Git is denied by default;
- only an explicit read-only Git allowlist is enabled, including inspection commands such as `status`, `diff`, `log`, `show`, `rev-parse`, `ls-files`, `grep`, `blame`, and read-only ref/config queries;
- commit, add, fetch, pull, push, merge, rebase, checkout, switch, reset, restore, clean, branch/tag/stash/worktree/remote/config mutation, and direct `.git` writes are forbidden;
- aliases, wrappers, nested shells, or renamed executables must not be used to bypass the restriction.

OpenCode enforces this natively through ordered permission rules. Codex uses `approval_policy = "never"` with a workspace-write sandbox. Claude Code agents use `permissionMode: bypassPermissions`. Cursor agents are generated writable; Cursor Auto-run/YOLO must be enabled in the client to suppress client-side approvals. See [`orchestrator/tool-permission-policy.yaml`](orchestrator/tool-permission-policy.yaml) and [`docs/workspace-and-permission-policy.md`](docs/workspace-and-permission-policy.md).

## Portable skill-resource paths

Every skill contains a generated `RESOURCE_INDEX.md`. Templates, schemas, validators, examples, supporting docs, and transition contracts are referenced relative to the directory containing `SKILL.md`.

Canonical resource identifier:

```text
templates/output.template.yaml
```

Never construct paths such as a user-specific absolute directory, `~` followed by backslashes, `%USERPROFILE%` concatenation, or a drive-letter path inside a skill instruction. Use the platform-native skill/resource loader. If an absolute filesystem path is unavoidable, join the discovered skill root and portable relative identifier with the host path API.

OpenCode adapters allow prompt-free worktree tools, deny all `gh` and mutating Git operations, deny arbitrary external access, but recursively allow read access to trusted t-think skill/runtime roots using `/**`; those roots are explicitly edit-denied. If a required resource cannot be opened, the agent must return:

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

Select `t-think` as the primary agent. The root adapter allowlists the ten terminal workers, runs normal worktree tools without prompting, blocks `gh` and mutating Git, and recursively read-allows only trusted global skill/runtime paths outside the worktree.

### Codex

```bash
codex --profile t-think
```

The root session owns orchestration. `approval_policy = "never"` removes approval prompts, the sandbox remains confined to the workspace, and `agents.max_depth = 1` prevents recursive delegation. The t-think command contract still forbids `gh` and mutating Git.

### Claude Code

```bash
claude --agent t-think
```

Generated agents use `permissionMode: bypassPermissions`; the t-think command contract still forbids `gh` and mutating Git.

### Cursor

Select the global `t-think` agent in Agent mode and enable Cursor Auto-run/YOLO when you want client-side tool approvals suppressed. The generated agents are writable, while t-think boundary validation still governs source changes.

## Start with `/t-problem-alignment`

```text
/t-problem-alignment Fix raw capture mapping bug
```

The first response must ask exactly:

1. the work ID or ticket number, with a concrete suggestion;
2. the lane: `quick`, `standard`, or `full`.

No repository read or `.t-think` write is allowed before both answers. Generate the same deterministic prompt payload from the CLI:

```bash
python3 bin/t-thinkctl.py intake \
  --task "Fix raw capture mapping bug" \
  --format json
```

See [`docs/intake-and-workspace-hygiene.md`](docs/intake-and-workspace-hygiene.md).

## Classify and initialize work

Classify without creating state:

```bash
python3 bin/t-thinkctl.py classify BUG-123 \
  --task "Fix the local parser bug covered by an existing failing test" \
  --signal local_reversible \
  --signal existing_reproduction
```

Initialize only after the human selects an explicit lane:

```bash
python3 bin/t-thinkctl.py init BUG-123 \
  --profile economy \
  --lane quick \
  --task "Fix the local parser bug covered by an existing failing test" \
  --signal local_reversible \
  --signal existing_reproduction
```

```bash
python3 bin/t-thinkctl.py init FEATURE-42 \
  --profile economy \
  --lane standard \
  --task "Add a medium-sized feature"
```

```bash
python3 bin/t-thinkctl.py init AUTH-9 \
  --lane full \
  --task "Change an authorization boundary" \
  --signal security_boundary
```

The selected lane is explicit. Existing risk policy may still promote an unsafe lower-lane request; a hard trigger forces `full`.

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

Run the prompt-free permission contract:

```bash
make permissions
```

Run the focused cross-platform resource audit:

```bash
make paths
```

Run the intake/workspace isolation audit:

```bash
make intake-workspace
```

Run the full bundle verification:

```bash
make verify
```

Important checks include:

- 12-phase lifecycle and lane routing;
- composite-track activation and aggregation;
- subagent authority, exact active-work-directory scope, and write boundaries;
- all skill schemas, templates, validators, and unit tests;
- 20 generated portable resource indexes;
- structured parsing of every indexed resource;
- prompt-free workspace-autonomous adapters, read-only Git allowlisting, and full `gh` denial;
- recursive OpenCode external-directory rules;
- deterministic Linux, macOS, and Windows path semantics;
- installation and resource resolution under a home path containing spaces and Unicode;
- mandatory two-question intake, root-pollution detection, scratch cleanup, and reconciliation hygiene gating;
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
