# Platform compatibility

The bundle installs one root orchestrator and ten terminal workers for OpenCode, Codex, Claude Code, and Cursor. Codex uses a root profile because depth-one custom workers must remain terminal. Claude workers omit the Agent tool. All adapters inherit the session model and use shared `t-*` skills.
