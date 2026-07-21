# Platform compatibility

The canonical workflow is platform-neutral. Native adapters are generated from `orchestrator/agent-registry.yaml` and the canonical role prompts.

| Platform | Root orchestrator | Role workers | Skills | Native containment |
|---|---|---|---|---|
| OpenCode | global primary Markdown agent | eight global subagents | shared `~/.agents/skills` | per-agent tool permissions and task allowlist |
| Codex | opt-in root profile `~/.codex/t-think.config.toml` | eight custom agents in `~/.codex/agents` | shared `~/.agents/skills` | root depth 0, `max_depth = 1`, per-worker sandbox mode |
| Claude Code | user agent launched with `claude --agent t-think` | eight user subagents | user skills linked/copied from shared store | root `Agent(...)` allowlist; workers omit `Agent` |
| Cursor | global foreground agent | eight global foreground role agents | shared `~/.agents/skills` | read-only worker metadata where supported |

## Codex root-profile rationale

A Codex custom agent file defines a spawned session. With nesting depth one, a child `t-think` could not spawn role workers. The bundle therefore injects the canonical `t-think` instruction into an opt-in root profile and installs only the eight terminal role agents as custom workers.

Launch:

```bash
codex --profile t-think
```

The profile permits up to four native threads so `balanced` and `high-assurance` can use bounded read-only parallelism; the lifecycle `economy` profile still limits actual concurrency to one. It does not pin a model or reasoning effort.

## Portable enforcement

Native tool systems differ. The portable source of truth is therefore:

1. canonical role and phase registries;
2. schema-valid delegation packets;
3. approved write targets from the frozen checklist;
4. protected-path and workspace-containment policy;
5. post-run boundary reports;
6. result-envelope validation before state transition.

A permissive native runtime does not broaden lifecycle authority.

## Official documentation checked during bundle construction

- OpenCode agents, skills, and permissions
- Codex subagents, custom agents, profiles, and configuration reference
- Claude Code user subagents, skills, and tool restrictions
- Cursor subagents and Agent Skills

Global means user-level on the current machine. Remote or cloud execution environments require their own installation.
