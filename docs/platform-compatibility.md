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

## Root session entry

All four root adapters embed the same mandatory session-entry contract. The portable guarantee is **the first invocation of the root `t-think` agent**, not a client application startup hook. OpenCode, Codex, Claude Code, and Cursor differ in whether they expose a reliable hook at the moment an agent UI is opened, so correctness does not depend on such a hook.

On first root invocation without an explicit `/t-problem-alignment`, `/t-resume`, or `/t-work-items` command, the adapter invokes the installed runtime's `entry` command and renders the three most recent unfinished work items plus conditional `Show all`. Worker agents never render the menu.

Session state remains repository-local under `.t-think/<work-id>/session/`; no platform stores authoritative progress in its private agent/skill configuration directory. This allows a work item started in one supported client to be resumed in another client, subject to the work-item lease.
