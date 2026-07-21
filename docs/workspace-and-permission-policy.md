# Workspace and permission policy

## Four separate concerns

```text
.gitignore / VCS ignore       default search discovery
approved_write_targets        exact source-change authorization
protected_paths               sensitive and structural safety boundary
outside_workspace             filesystem containment
```

These concerns must not be merged into one generic allow/deny path list.

## Discovery

Search and enumeration respect VCS ignore rules by default, include relevant untracked files, and exclude ignored files. An ignored file may be read only when the delegation packet contains a recorded human approval reference.

`.gitignore` is not a security boundary: a tool may still open an ignored path explicitly if permissions permit it.

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

## Protected paths

Default protected patterns include:

- `.git/**`;
- `.env` and `.env.*`;
- secret directories;
- credential-bearing files;
- private keys.

Protected paths remain denied even if tracked, visible, or accidentally included in a proposed checklist target.

## Enforcement layers

1. Native platform permissions restrict the available tools or sandbox.
2. Delegation validation rejects authority inconsistent with role and phase.
3. Activity capture records files, commands, ignored reads, and external access.
4. Boundary auditing compares activity with the exact packet.
5. Result validation refuses lifecycle transition when the boundary report is not `PASS`.
