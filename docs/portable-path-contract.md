# Portable Skill-Resource Path Contract

## Problem addressed

A platform may load `SKILL.md` through its native skill mechanism while treating sibling templates and schemas as external filesystem paths. On Windows, a model may also incorrectly combine a POSIX home shorthand with Windows separators, producing a path such as a tilde followed by backslashes. A non-recursive permission pattern can then allow the skill directory but reject nested `templates/`, `schemas/`, or `validators/` files.

## Canonical rule

All bundled skill resources use an identifier relative to the directory containing `SKILL.md`:

```text
templates/output.template.yaml
```

This identifier is not an absolute operating-system path. It always uses `/` separators because it is stored in Markdown, YAML, JSON, delegation metadata, and generated indexes.

## Resolution order

1. Load the skill through the platform-native skill tool.
2. Read `RESOURCE_INDEX.md` relative to the loaded `SKILL.md`.
3. Open a linked resource using the platform's native resource loader.
4. Only when an absolute path is required, obtain the skill root from the platform or t-think installation manifest and join path components with the host path API.
5. If resolution fails, return `BLOCKED / SKILL_RESOURCE_UNAVAILABLE`.

Never guess a template's content from prior experience.

## Deterministic resolver

```bash
python3 bin/t-thinkctl.py paths \
  --skill t-reconciliation \
  --resource templates/output.template.yaml
```

The JSON result contains the discovered skill root, resource index, native resolved path, and illustrative path semantics for Linux, macOS, and Windows.

To print only the native path:

```bash
python3 bin/t-thinkctl.py paths \
  --skill t-reconciliation \
  --resource templates/output.template.yaml \
  --native-only
```

The resolver rejects:

- absolute resource identifiers;
- drive-qualified identifiers;
- backslashes in portable identifiers;
- `.` or `..` path segments;
- home-directory tokens;
- targets that escape the discovered skill root;
- missing files.

## OpenCode permission model

Generated OpenCode adapters use a deny-first `external_directory` rule map and recursive trusted allows for:

```text
~/.agents/skills/t-*/**
~/.claude/skills/t-*/**
~/.config/opencode/skills/t-*/**
~/.local/share/t-think/runtime/**
```

The same trusted roots are edit-denied. This permits nested template/schema reads without granting general external filesystem access.

## Platform behavior

### Linux

A native resolved path may look like:

```text
/home/user/.agents/skills/t-reconciliation/templates/output.template.yaml
```

### macOS

```text
/Users/user/.agents/skills/t-reconciliation/templates/output.template.yaml
```

### Windows

```text
C:\Users\user\.agents\skills\t-reconciliation\templates\output.template.yaml
```

The Windows representation is produced by the native path API. Do not write that representation into `SKILL.md`, `RESOURCE_INDEX.md`, or portable metadata.

## Automated verification

```bash
python3 scripts/path_template_contract_test.py
```

The audit verifies:

- every skill has a portable resource contract and index;
- every indexed local link is contained and exists;
- every bundled template, schema, validator, transition contract, supporting document, and example is indexed;
- YAML, JSON, JSONL, CSV, and Python resources parse or compile;
- generated adapters contain no hard-coded user paths or backslash resource identifiers;
- OpenCode trusted external paths are recursive and read-only;
- deterministic path joining matches Linux, macOS, and Windows semantics.

Installation smoke testing additionally resolves a real copied resource from a temporary home directory containing spaces and Unicode.
