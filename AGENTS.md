# AGENTS.md — t-think Bundle Continuity Contract

This file governs changes to the `t-think-governed-sdlc` repository itself. It is not copied into repositories governed by t-think.

## Product identity

The bundle contains:

- one root orchestrator: `t-think`;
- ten terminal role workers;
- twenty canonical/component skills;
- twelve canonical lifecycle phases;
- three adaptive governance lanes;
- four platform adapter families;
- deterministic schemas, validators, installers, audits, archives, and checksums.

The topology is always a star with maximum delegation depth one. Workers never delegate recursively.

## Canonical lifecycle

### Quick

```text
PROBLEM_ALIGNMENT
→ BOUNDED_IMPLEMENTATION
→ IMPLEMENTATION_REVIEW
→ VERIFICATION
→ RECONCILIATION
→ COMPLETED
```

### Standard

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

### Full

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

Lane promotion is monotonic: `quick → standard → full`. No automatic demotion is allowed.

## Composite phases

Phase compression must never remove independent delegations or fresh contexts.

| Composite phase | Required tracks |
|---|---|
| `IMPLEMENTATION_BLUEPRINT` | `strategy`, `execution_checklist` |
| `BLUEPRINT_CRITIQUE` | `strategy_critique`, `execution_critique` |
| `IMPLEMENTATION_REVIEW` quick | `self_review`, `technical_review` |
| `IMPLEMENTATION_REVIEW` standard/full | `self_review`, `technical_review`, `security_review`, `breaking_review` |

Only the aggregate composite-phase validator may advance lifecycle. A component track may not emit or apply a canonical phase transition.

## Roles and authority

| Worker | Primary responsibility | Product-source write |
|---|---|---:|
| `t-investigator` | collect factual repository/runtime evidence | deny |
| `t-modeler` | system model and solution design | deny |
| `t-planner` | blueprint strategy and executable checklist | deny |
| `t-critic` | independent model, solution, and blueprint critique | deny |
| `t-builder` | approved implementation; fresh self-review | approved targets only during implementation; deny during review |
| `t-reviewer` | independent technical review | deny |
| `t-security-reviewer` | dedicated security review | deny |
| `t-breaking-reviewer` | flow/rule/validation/data/mapping/contract compatibility review | deny |
| `t-verifier` | executable verification | generated outputs only |
| `t-reconciler` | final traceability and residual-gap audit | deny |

`t-think` owns routing, aggregation, human gates, and lifecycle transitions. It never modifies product source.

## Portable path contract

All skill resources must be portable across Windows, macOS, and Linux.

1. Every skill has `SKILL.md` and generated `RESOURCE_INDEX.md`.
2. Resource references are relative to the skill root and use `/` separators.
3. Instructions must never invent user-home paths, use `~` with backslashes, concatenate `%USERPROFILE%`, embed a drive letter, or hard-code a username.
4. Absolute paths, when unavoidable, are produced by `pathlib`/the host path API or `bin/t-thinkctl.py paths`.
5. Missing resources produce `BLOCKED / SKILL_RESOURCE_UNAVAILABLE`; models may not recreate templates from memory.
6. OpenCode `external_directory` rules deny by default, recursively allow trusted t-think skill/runtime roots with `/**`, and edit-deny those roots.
7. Run `scripts/update_skill_resource_indexes.py` after adding, moving, or deleting any skill resource.
8. Run `scripts/path_template_contract_test.py` after every path, template, adapter, installer, or skill change.

Canonical identifier:

```text
templates/output.template.yaml
```

A native Windows tool may display the resolved path with backslashes. That display form must never be copied back into portable skill metadata or Markdown links.

## Repository layout

```text
AGENTS.md                  this continuity contract
README.md                  user-facing installation and operation guide
VERSION                    bundle release version
orchestrator/              phase/lane/risk/composite/role policies
agents/                    source worker instructions
skills/                    twenty skill packages
adapters/                  generated platform-native agents/profiles
bin/                       runtime, installer, doctor, validators, resolver
schemas/                   shared JSON Schemas
scripts/                   generators, audits, tests, archive/checksum tooling
templates/                 root work-state templates
docs/                      detailed operating contracts
reports/                   generated test/audit reports
archives/                  standalone skill archives
```

Generated adapters are outputs. Change their source instructions or generator, then run `python3 scripts/generate_adapters.py`; do not hand-edit generated adapters as the sole change.

`RESOURCE_INDEX.md` files are generated outputs. Update resource files or the index generator, then regenerate all indexes.

## Source-of-truth hierarchy

When artifacts disagree, use this order:

1. JSON Schemas and deterministic validators;
2. orchestrator registries and policies;
3. skill transition contracts;
4. worker/source agent instructions;
5. generated adapters;
6. README, MANIFEST, and examples.

Fix all lower layers when a higher source changes.

## Workspace boundaries

`.gitignore` controls discovery only. It does not grant or deny authority.

- Product writes require exact human-approved targets.
- Protected files remain denied.
- Outside-workspace product access remains denied.
- Trusted global skill/runtime paths are a separate read-only resource exception for platform operation.
- Self-review and all independent review tracks are read-only.
- Verifier output is limited to declared generated paths.
- Every worker result requires a boundary report.

Do not weaken these rules to simplify adapters or tests.

## Skill package requirements

Every `skills/t-*` package must contain at least:

```text
SKILL.md
RESOURCE_INDEX.md
README.md
MANIFEST.md
schemas/
templates/
validators/
examples/
tests/
orchestrator/transition-contract.yaml
```

Each `SKILL.md` must:

- have name matching its directory;
- declare the correct canonical lifecycle state;
- remain scoped to one phase or component track;
- use bounded, cheap-model-friendly instructions;
- contain the portable resource contract;
- link to its resource index and frequent input/output resources;
- direct missing evidence or resources to `BLOCKED`, never invention.

## Cheap-model reliability

Preserve:

- one objective per invocation;
- one active skill per invocation;
- fresh contexts between producer and critic/reviewer;
- enumerated statuses before prose;
- template-first output;
- exact file/evidence inputs rather than repository dumps;
- checklist-based review;
- command-driven verification with exit code and evidence path;
- one constrained retry, then escalation.

Do not merge independent reviewer contexts merely because phases share one lifecycle state.

## Versioning

Use semantic versioning for the bundle.

- Patch: compatibility fix, validator/audit hardening, documentation correction, portable-path fix without lifecycle/schema break.
- Minor: backward-compatible lifecycle/role/skill capability.
- Major: incompatible state, manifest, installer, or lifecycle contract.

A bundle version bump does not automatically require a work-state schema version bump. State schema versions change only when serialized state changes.

When bumping the bundle:

- update `VERSION`;
- update skill frontmatter versions where the package changed;
- update `README.md` and `MANIFEST.md`;
- regenerate adapters, indexes, archives, reports, and checksums;
- verify an extracted ZIP, not only the source tree.

## Required change workflow

For any architecture, path, template, or installer change:

1. inspect registries, schemas, generators, and affected skills;
2. edit source-of-truth files;
3. regenerate portable resource indexes;
4. regenerate platform adapters;
5. run path/template contract audit;
6. run alignment, lane, subagent, economy, and installation smoke tests;
7. run every skill validator and unit test;
8. rebuild standalone skill archives;
9. update manifest/report totals;
10. regenerate root and per-skill checksums;
11. build the ZIP;
12. extract to a clean directory and repeat critical checks plus install/doctor/path resolution.

## Verification commands

Focused:

```bash
python3 scripts/update_skill_resource_indexes.py
python3 scripts/generate_adapters.py
python3 scripts/path_template_contract_test.py
python3 scripts/audit_alignment.py
python3 scripts/subagent_contract_test.py
python3 scripts/lane_contract_test.py
python3 scripts/economy_contract_test.py
python3 scripts/smoke_test.py
```

Full:

```bash
make verify
```

Packaging:

```bash
python3 scripts/generate_skill_checksums.py
python3 scripts/rebuild_archives.py
python3 scripts/generate_checksums.py
sha256sum -c CHECKSUMS.sha256
```

Aggregate test processes may exceed a host command window. It is acceptable to execute deterministic validator/unit-test batches and combine their reports, but every command/test must run and every failure must remain visible.

## Completion criteria for bundle changes

A change is complete only when:

- path, lane, phase, role, skill, adapter, schema, and validator contracts agree;
- generated files are current;
- all required resources are indexed and exist;
- templates and structured resources parse;
- portable path semantics pass for Linux, macOS, and Windows;
- copy install, doctor, resolver, and uninstall pass in an isolated home path with spaces and Unicode;
- symlink install passes where supported;
- all skill validators and unit tests pass;
- standalone archives and root checksums pass;
- extracted-package checks pass;
- README and MANIFEST describe the actual bundle.
