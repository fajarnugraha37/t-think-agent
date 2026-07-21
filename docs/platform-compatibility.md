# Platform compatibility and resource isolation

The bundle installs one root orchestrator and ten terminal workers for OpenCode, Codex, Claude Code, and Cursor. Each platform receives its own physical copy or symlink view of all twenty skill packages.

| Platform | Agent configuration | Skill/resource strategy |
|---|---|---|
| OpenCode | `~/.config/opencode/agents` | native OpenCode-only `~/.config/opencode/skills` |
| Codex | `~/.codex/t-think.config.toml`, `~/.codex/agents` | direct reads from `~/.codex/t-think/skills` embedded in TOML |
| Claude Code | `~/.claude/agents` | direct reads from `~/.claude/t-think/skills`; global Skill tool omitted |
| Cursor | `~/.cursor/agents` | direct reads from `~/.cursor/t-think/skills` embedded in agent files |

Shared skill directories are deliberately not used. This prevents OpenCode or another client from selecting a stale or foreign t-think copy.

Codex keeps depth-one custom workers terminal. Claude workers omit both `Agent` and `Skill`. All adapters inherit the session model and preserve the workspace-autonomous, Git-read-only, `gh`-denied contract.
