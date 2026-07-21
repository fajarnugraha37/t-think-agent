# AGENTS.md — t-think Governed Multi-Agent SDLC

## 1. Purpose

This is the repository continuity contract for developing and maintaining **t-think itself**. A new human or coding agent must be able to continue from repository files on another machine or platform without prior chat history.

This file is not a runtime project instruction and must not be copied automatically into repositories governed by t-think.

## 2. Product identity

The bundle contains:

- one root orchestrator: `t-think`;
- eight terminal role workers;
- fifteen canonical phase skills;
- three adaptive governance lanes: `quick`, `standard`, and `full`;
- deterministic routing and promotion;
- schemas, validators, boundary audits, examples, tests, adapters, installers, archives, checksums, and reports.

The full lifecycle remains canonical. Compressed lanes may omit phases only through `orchestrator/lane-registry.yaml` and a validated phase-waiver artifact.

## 3. Start every session here

Before editing:

1. Confirm the root contains `README.md`, `AGENTS.md`, `VERSION`, `Makefile`, `orchestrator/`, `agents/`, `skills/`, `schemas/`, `bin/`, and `scripts/`.
2. Read:
   - `README.md`;
   - `orchestrator/t-think-core.md`;
   - `orchestrator/lane-registry.yaml`;
   - `orchestrator/risk-classification-policy.yaml`;
   - `orchestrator/phase-registry.yaml`;
   - `orchestrator/agent-registry.yaml`;
   - `orchestrator/workspace-policy.yaml`;
   - documents relevant to the requested change.
3. Run:

```bash
make audit
make subagents
make lanes
make economy
```

4. Inspect and preserve unrelated work:

```bash
git status --short
git diff --stat
git diff
```

5. Classify intended files as canonical, generated, packaged, or report output.
6. State affected invariants and required tests before implementation.

Never infer repository state, test status, or previous decisions from chat memory.

## 4. Source-of-truth hierarchy

When sources disagree:

1. schemas and validators;
2. canonical orchestrator policies and registries;
3. canonical role manifests;
4. canonical role instructions;
5. phase skill contracts;
6. generated adapters;
7. examples and reports;
8. prose documentation.

Important canonical files:

```text
orchestrator/t-think-core.md
orchestrator/lane-registry.yaml
orchestrator/risk-classification-policy.yaml
orchestrator/artifact-mode-policy.yaml
orchestrator/context-budget-policy.yaml
orchestrator/lifecycle.yaml
orchestrator/phase-registry.yaml
orchestrator/agent-registry.yaml
orchestrator/delegation-policy.yaml
orchestrator/escalation-policy.yaml
orchestrator/model-profiles.yaml
orchestrator/workspace-policy.yaml
agents/*/agent.yaml
agents/*/AGENT.md
schemas/*.json
skills/t-*/**
```

Fix contradictions at the lowest incorrect layer. Do not weaken a higher contract merely to make a fixture pass.

## 5. Repository map

```text
AGENTS.md                  contributor and continuation contract
README.md                  user-facing operation guide
MANIFEST.md                release inventory and assurance summary
VERSION                    canonical bundle version
Makefile                   development and verification entry points
orchestrator/              canonical lifecycle, lanes, routing, and policies
agents/                    canonical role manifests and instructions
skills/                    fifteen canonical phase packages
schemas/                   portable machine contracts
bin/                       runtime CLI, validators, installers, doctor, uninstallers
scripts/                   generators, audits, tests, packaging, checksums
adapters/                  generated platform adapters
examples/                  validated handoffs and lifecycle examples
templates/                 state templates
tests/                     cross-cutting test data
archives/                  generated standalone skill ZIPs
reports/                   generated verification summaries
docs/                      architecture and policy explanations
CHECKSUMS.sha256           generated root integrity inventory
```

## 6. Locked architecture invariants

### 6.1 Topology

- `t-think` is the sole orchestrator and state-transition owner.
- Workers are terminal: `t-investigator`, `t-modeler`, `t-planner`, `t-critic`, `t-builder`, `t-reviewer`, `t-verifier`, `t-reconciler`.
- Delegation is a star with maximum depth one.
- Workers never invoke workers or advance lifecycle state.

### 6.2 Role separation

- `t-builder` is the only source writer.
- Builder writes are limited to approved targets during `BOUNDED_IMPLEMENTATION`.
- `SELF_REVIEW` is a fresh write-denied builder invocation.
- Critics and reviewers are source-read-only.
- `t-verifier` writes only declared generated outputs.
- Quick-lane reconciliation is the only root-handled phase override; it must remain deterministic and source-read-only.

### 6.3 Human authority

Agents must not synthesize human approval, accepted risk, semantic intent, expected behavior, execution authorization, ignored-file approval, or final closure. Missing authority produces `BLOCKED`, `UNKNOWN`, loopback, or lane promotion.

### 6.4 Workspace boundary

`.gitignore` controls discovery only.

- deny outside-workspace access;
- deny ignored-file reads without human approval;
- protect `.git/**`, `.env*`, secrets, credentials, and private keys;
- treat an empty approved-target list as no write authority;
- validate every worker with a post-run boundary report.

### 6.5 Model neutrality

- No flagship model may be a hidden correctness dependency.
- Model settings inherit from the host by default.
- Economy execution remains sequential, bounded, schema-first, and validator-driven.
- Promote governance before model escalation when scope or risk expands.

### 6.6 Evidence and state

- Conversation prose does not advance state.
- Approved artifacts are digest-bound.
- Drift invalidates dependent approvals.
- Large logs remain evidence files.
- Route defects to the earliest owning phase.
- Pre-2.2 work states without lane metadata route as `full`.

## 7. Adaptive lane invariants

### Quick

```text
PROBLEM_ALIGNMENT
→ BOUNDED_IMPLEMENTATION
→ SELF_REVIEW
→ VERIFICATION
→ RECONCILIATION
→ COMPLETED
```

- worker role types: exactly `t-builder` and `t-verifier`;
- artifact mode: `compact`;
- one human write-authorization gate before implementation;
- root deterministic reconciliation;
- requires bounded/reversible classification evidence.

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

- artifact mode: `normal`;
- suited to small-to-medium features, local refactors, and non-trivial bugs;
- retains independent technical review and verification.

### Full

Contains every canonical phase and uses `exhaustive` artifacts.

Required lane rules:

- no reliable signals defaults to standard;
- hard-risk signals force full;
- quick requires a bounded/reversible qualifier;
- promotion is monotonic: quick to standard to full;
- demotion is invalid;
- promotion returns to the earliest newly required phase;
- compressed lanes produce validated lane assessment and phase waiver files;
- waived phases cannot be routed or delegated;
- no empty artifact is created for a waived phase;
- v2.2 delegation packets bind lane, artifact mode, and expected next state;
- shorter paths never weaken permissions, boundary auditing, fresh review contexts, verification, or human authority.

## 8. Canonical phase-to-role mapping

| State | Role | Skill | Source write |
|---|---|---|---|
| `PROBLEM_ALIGNMENT` | `t-think` | `t-problem-alignment` | deny |
| `INVESTIGATION` | `t-investigator` | `t-investigation` | deny |
| `SYSTEM_MODEL` | `t-modeler` | `t-system-modeling` | deny |
| `MODEL_CRITIQUE` | `t-critic` | `t-model-critique` | deny |
| `SOLUTION_DESIGN` | `t-modeler` | `t-solution-design` | deny |
| `SOLUTION_CRITIQUE` | `t-critic` | `t-solution-critique` | deny |
| `IMPLEMENTATION_PLAN` | `t-planner` | `t-implementation-planning` | deny |
| `PLAN_CRITIQUE` | `t-critic` | `t-plan-critique` | deny |
| `IMPLEMENTATION_CHECKLIST` | `t-planner` | `t-checklist-builder` | deny |
| `CHECKLIST_CRITIQUE` | `t-critic` | `t-checklist-critique` | deny |
| `BOUNDED_IMPLEMENTATION` | `t-builder` | `t-bounded-implementation` | approved targets only |
| `SELF_REVIEW` | fresh `t-builder` | `t-self-review` | deny |
| `TECHNICAL_REVIEW` | `t-reviewer` | `t-technical-review` | deny |
| `VERIFICATION` | `t-verifier` | `t-verification` | generated outputs only |
| `RECONCILIATION` | `t-reconciler` | `t-reconciliation` | deny |

Lane overrides are applied after this mapping and must be explicit in `lane-registry.yaml`.

## 9. Editing rules

- Make the smallest coherent change.
- Preserve public identifiers and enums unless a versioned contract change is intentional.
- Do not add aliases or migrations without demonstrated need.
- Never weaken a validator, permission boundary, or role separation for convenience.
- Do not combine unrelated cleanup.
- Keep documentation aligned in the same change.
- Update canonical inputs before generated outputs.
- Never hand-edit generated adapters as the primary fix.
- Preserve deterministic ordering and stable serialization.

Typical change order:

```text
canonical policy/schema
→ runtime/router/validator
→ canonical role/skill contract
→ generated adapters
→ examples and tests
→ documentation
→ reports
→ archives
→ checksums
→ manifest/version/final ZIP
```

## 10. Required validation

### Lane, lifecycle, routing, authority, schema, or runtime change

```bash
make adapters
make audit
make subagents
make lanes
make economy
make validate
make test
make smoke
make checksums
```

Add negative tests for every new boundary or authority rule.

### Skill change

```bash
make audit
make validate
make test
make archives
make checksums
```

### Adapter change

```bash
make adapters
make audit
make subagents
make economy
make smoke
make checksums
```

### Installer change

```bash
make smoke
make audit
make checksums
```

### Documentation-only change

```bash
make audit
make checksums
```

Run broader tests when docs contain commands, counts, mappings, or behavioral claims.

### Release

```bash
make verify
make archives
make checksums
```

Then build a clean ZIP, run `unzip -t`, extract to a temporary directory, and rerun applicable acceptance tests from the extracted copy.

## 11. Critical negative cases

Test at minimum:

- hard-risk work classified below full;
- quick selected without a bounded/reversible qualifier;
- routing or delegation into a waived phase;
- lane demotion;
- promotion that discards prior history;
- promotion that incorrectly continues after skipped required phases;
- wrong role or skill for a phase;
- nested worker delegation;
- non-builder source write;
- builder write outside approved targets;
- protected-path write;
- ignored-file read without approval;
- outside-workspace access;
- self-review source write;
- verifier source write;
- forged approval;
- artifact digest mismatch;
- invalid result transition;
- model failure silently advancing state;
- parallel source writers.

## 12. Versioning and release

- `VERSION` is canonical.
- Patch: compatible correction or documentation/test/package fix.
- Minor: backward-compatible capability or optional contract extension.
- Major: incompatible lifecycle, schema, invocation, installation, or artifact contract.
- Update `MANIFEST.md` whenever inventory or assurance claims change.
- Regenerate adapters after canonical prompt changes.
- Rebuild skill archives when skill content changes.
- Regenerate root checksums after every distributed-file change.
- Record final ZIP size and SHA-256 from the produced file.
- Never claim a test count that is not supported by current reports.

## 13. Installation and security

Global installers are consequential. Preserve idempotence, conflict detection, safe backups, owned-path manifests, doctor checks, and uninstall limited to owned files.

Never commit or inspect secrets without explicit authorization. Do not add telemetry, automatic upload, remote execution, background services, shell-profile mutation, or system-directory changes without explicit design and approval.

## 14. Documentation map

- `README.md`: installation, invocation, lanes, commands, assurance boundary;
- `docs/adaptive-governance-lanes.md`: classification, compression, promotion, compatibility;
- `docs/subagent-architecture.md`: topology and roles;
- `docs/workspace-and-permission-policy.md`: discovery and authorization;
- `docs/cheap-model-compatibility.md`: economy behavior and escalation;
- `docs/critique-and-loopback-policy.md`: critique and earliest-owner routing;
- `docs/epistemic-policy.md`: claim labels;
- `docs/platform-compatibility.md`: native platform representation;
- `docs/artifact-conventions.md`: artifact storage and naming;
- `MANIFEST.md`: frozen release facts.

## 15. Continuation protocol

Before ending a session:

1. leave a coherent tree;
2. update canonical docs and tests;
3. record the strongest completed validation;
4. keep generated adapters aligned;
5. do not leave stale checksums while claiming release readiness;
6. preserve unresolved work in a durable file, issue, or commit message;
7. record exact failing commands for blockers;
8. preserve unrelated user work.

At the next session:

```bash
git status --short
git log -n 10 --oneline
cat VERSION
sed -n '1,260p' AGENTS.md
sed -n '1,260p' README.md
make audit
make subagents
make lanes
make economy
```

## 16. Definition of done

A change is complete only when:

- canonical sources represent the requested behavior;
- lane assessment, waiver, paths, roles, skills, schemas, and validators agree;
- permissions remain least-privilege;
- relevant positive and negative tests pass;
- generated adapters match canonical sources;
- documentation and reports are truthful;
- archives and checksums are current when applicable;
- installation smoke tests pass when affected;
- no unrelated work was overwritten;
- live-platform limitations are stated honestly.

## 17. Final guardrail

Optimize for governed correctness, reproducibility, portability, and honest evidence. A shorter lane may reduce ceremony; it must never enable a gate bypass, unauthorized write, recursive delegation, silent completion on invalid evidence, or hidden dependence on an expensive model.
