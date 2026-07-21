# Portable and Platform-Isolated Skill-Resource Contract

## Problem addressed

A skill package contains `SKILL.md` plus nested templates, schemas, validators, examples, and documentation. Two independent problems must be prevented:

1. models constructing hybrid paths such as `~\\.agents\\skills\\...` on Windows;
2. one client discovering a t-think copy installed for another client through shared directories such as `~/.agents/skills` or `~/.claude/skills`.

## Canonical resource identifier

Every bundled resource is referenced relative to its own `SKILL.md` and always uses `/` separators:

```text
templates/output.template.yaml
```

Portable metadata never contains a home token, username, drive letter, absolute path, backslash separator, `.` segment, or `..` segment.

## Platform-isolated installation roots

```text
OpenCode    ~/.config/opencode/skills/t-*
Codex       ~/.codex/t-think/skills/t-*
Claude Code ~/.claude/t-think/skills/t-*
Cursor      ~/.cursor/t-think/skills/t-*
```

`t-think` is never installed into:

```text
~/.agents/skills
~/.claude/skills
```

OpenCode uses only its own native skill root. Codex, Claude Code, and Cursor adapters are materialized during installation with the exact absolute path to their own private root. Claude adapters omit the global `Skill` tool.

## Resolution order

1. Read the active platform root from the installed adapter or installation manifest.
2. Select `<platform-root>/<skill-name>/SKILL.md`.
3. Read `RESOURCE_INDEX.md` relative to that file.
4. Join portable resource parts with the host path API.
5. Confirm the resolved file remains within that skill root and exists.
6. On failure return `BLOCKED / SKILL_RESOURCE_UNAVAILABLE`; never recreate a template from memory.

## Deterministic resolver

When multiple targets are installed, `--platform` is mandatory:

```bash
python3 bin/t-thinkctl.py paths \
  --platform opencode \
  --skill t-reconciliation \
  --resource templates/output.template.yaml
```

Print only the native path:

```bash
python3 bin/t-thinkctl.py paths \
  --platform codex \
  --skill t-reconciliation \
  --resource templates/output.template.yaml \
  --native-only
```

The resolver rejects absolute identifiers, drive-qualified identifiers, backslashes, home tokens, non-normalized segments, root escapes, and missing files.

## OpenCode external permission model

OpenCode adapters deny arbitrary external access and allow only:

```text
~/.config/opencode/skills/t-*/**
~/.local/share/t-think/runtime/**
```

Both are edit-denied. No permission rule allows `~/.agents/skills` or `~/.claude/skills`.

## Native path examples

For `t-reconciliation/templates/output.template.yaml`:

```text
Linux OpenCode: /home/user/.config/opencode/skills/t-reconciliation/templates/output.template.yaml
macOS Codex:    /Users/user/.codex/t-think/skills/t-reconciliation/templates/output.template.yaml
Windows Claude: C:\Users\user\.claude\t-think\skills\t-reconciliation\templates\output.template.yaml
Windows Cursor: C:\Users\user\.cursor\t-think\skills\t-reconciliation\templates\output.template.yaml
```

These native display forms are produced by path APIs and must not be copied into portable skill metadata.

## Legacy migration

A v2.5+ install without `--keep-legacy-shared-skills` transactionally removes only canonical t-think live directories and their installer-created `*.bak-*` siblings from the two legacy shared roots. Unrelated user skills are preserved. Temporary rollback data lives only below `~/.local/share/t-think/.transactions/` and is removed on commit.

## Automated verification

```bash
python3 scripts/path_template_contract_test.py
python3 scripts/permission_contract_test.py
python3 scripts/smoke_test.py
```

The audits verify resource containment, structured file validity, all four platform path semantics, absence of cross-platform discovery permissions, exact migration behavior, preservation of unrelated user skills, and path resolution from an isolated installation.
