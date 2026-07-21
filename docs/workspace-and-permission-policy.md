# Workspace and permission policy

## Four separate concerns

```text
.gitignore / VCS ignore       default search discovery
approved_write_targets        exact source-change authorization
protected_paths               direct `.git/**` write boundary
outside_workspace             filesystem containment
```

These concerns must not be merged into one generic allow/deny path list.

## Discovery

Search and enumeration may include tracked, untracked, and ignored files anywhere inside the active project worktree. Git ignore status is not an approval boundary and never requires a human prompt.

`.gitignore` controls version-control discovery only. It does not restrict project-local tool access.

## Normal workspace reads

Role workers may read relevant files below the active workspace. Every access outside that workspace is denied and recorded as a boundary violation.

## Governance artifacts

All roles may write only their own governed artifacts below `.t-think/<work-id>/`. Native adapters may require a broader write-capable tool to create these files; portable boundary auditing verifies that no source path was modified.

## Source writes

Only `t-builder` during `BOUNDED_IMPLEMENTATION` may modify source. The authoritative target set comes from the human-approved, digest-frozen checklist and is copied into `approved_write_targets`.

- exact paths and explicitly approved globs are accepted;
- an empty target list authorizes no writes;
- a path omitted from the checklist cannot be added by the builder;
- discovery visibility does not imply write authority;
- self-review runs in a new invocation with source writes denied.

## Generated outputs

`t-verifier` may create only declared build, test, coverage, and report outputs. A generated-output permission never authorizes source changes.

## Native tool path boundary

Inside the active project worktree, native file tools are prompt-free and have no path denylist except `.git/**`. Files such as `.env`, project-local secret fixtures, credentials, keys, generated files, and ignored files are not blocked by the native adapter merely because of their names. Their use remains governed by the active task, delegation packet, repository policy, and review evidence.

Direct writes below `.git/**` remain denied. Version-control inspection must use an explicitly allowed read-only Git command.

## Enforcement layers

1. Native platform permissions restrict the available tools or sandbox.
2. Delegation validation rejects authority inconsistent with role and phase.
3. Activity capture records files, commands, ignored reads, and external access.
4. Boundary auditing compares activity with the exact packet.
5. Result validation refuses lifecycle transition when the boundary report is not `PASS`.

## Prompt-free native tool profile

`t-think` uses the `workspace-autonomous` native-tool profile:

- normal tools inside the project worktree run without approval prompts;
- file read, search, edit, write, shell, build, test, lint, formatting, and diagnostic operations are available;
- access outside the project remains denied except for read-only installed t-think skill/runtime resources;
- native tool availability does not grant lifecycle source-write authority;
- every actual source change still has to match the delegation packet and pass boundary auditing.

The broad native profile avoids approval fatigue. It intentionally relies on the governed delegation and audit layers to keep read-only roles read-only at the lifecycle level.

## Git and GitHub CLI boundary

`gh` is always forbidden. Git is denied by default and reopened only for explicit read-only inspection commands such as `status`, `diff`, `log`, `show`, `rev-parse`, `ls-files`, `grep`, `blame`, read-only ref listing, and read-only configuration queries.

Git mutations are forbidden, including commit, add, fetch, pull, push, merge, rebase, checkout, switch, reset, restore, clean, branch/tag mutation, stash mutation, worktree mutation, remote mutation, config mutation, and direct writes below `.git/`.

Agents must not bypass this boundary through aliases, wrappers, nested shells, renamed executables, or direct filesystem access. A required VCS mutation produces `BLOCKED / VCS_MUTATION_FORBIDDEN` and remains a human action.
