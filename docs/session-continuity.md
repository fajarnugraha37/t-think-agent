# Session entry and cross-session continuity

`t-think` treats repository state as authoritative and conversation history as optional navigation context. An unfinished work item can be resumed from another chat, another process, or another supported client without asking the human to restate facts that were already persisted.

## Root session entry

On the first invocation of the root `t-think` agent, unless the user explicitly invokes `/t-problem-alignment`, `/t-resume <work-id>`, or `/t-work-items`, the agent runs:

```bash
python3 <install-root>/bin/t-thinkctl.py entry \
  --repository-root <repository-root> \
  --limit 3
```

The operation is read-only. It derives candidates from `.t-think/*/state.yaml` and shows at most the three most recently active unfinished work items:

```text
What do you want to do?

● Start a new task
○ Continue TSREX-RAW-001
  STANDARD · IMPLEMENTATION_REVIEW · interrupted
○ Continue TSREX-CORE-001
  FULL · SOLUTION_DESIGN · waiting_human
○ Continue TSREX-DOC-003
  QUICK · VERIFICATION · blocked
○ Show all unfinished work items
○ Inspect existing work items
```

`Show all unfinished work items` is rendered only when more than three unfinished items exist. `Inspect existing work items` is a read-only catalogue; use `--all` to include completed, abandoned, and archived items.

```bash
python3 <install-root>/bin/t-thinkctl.py work-items --repository-root .
python3 <install-root>/bin/t-thinkctl.py work-items --repository-root . --all
```

## Explicit entry commands

```text
/t-problem-alignment <problem statement>   start a new work item
/t-resume <work-id>                        resume one persisted work item
/t-work-items                              inspect persisted work items
```

An explicit new-task command bypasses the session menu and immediately asks the mandatory work-ID and lane questions.

## Persistent work-item state

Each work item owns a dedicated session directory:

```text
.t-think/<work-id>/
├── state.yaml
└── session/
    ├── resume.yaml
    ├── activity.jsonl
    └── lease.yaml
```

### `state.yaml`

Canonical lifecycle and routing state. New work items use work-state schema `2.4.0` and record:

- lifecycle phase;
- governance lane;
- work status;
- last activity timestamp;
- current session ID;
- paths to the checkpoint, journal, and lease;
- monotonically increasing session generation.

Work status is independent from lifecycle phase:

```text
active
waiting_human
blocked
interrupted
completed
abandoned
archived
```

### `session/resume.yaml`

A compact machine-readable checkpoint containing:

- current objective;
- last completed action;
- exact next action;
- current in-flight delegation;
- completed and remaining composite tracks;
- open findings and pending human questions;
- approved write targets and changed files;
- outstanding verification obligations;
- latest workspace-hygiene summary.

### `session/activity.jsonl`

Append-only audit journal. Each line is an independent JSON event with a timestamp, work ID, session ID, lifecycle phase, event type, and optional structured details.

### `session/lease.yaml`

Concurrency guard for the active work item. Only one mutating root session may hold the lease. The default stale interval is 900 seconds.

## Deterministic resume

```bash
python3 <install-root>/bin/t-thinkctl.py resume TSREX-RAW-001 \
  --repository-root . \
  --platform opencode
```

Resume performs these operations in order:

1. load and validate `state.yaml`;
2. migrate pre-session work state when necessary;
3. audit `.t-think/<work-id>/` layout and scratch hygiene;
4. load and validate `session/resume.yaml`;
5. scan delegation packets and their declared result paths;
6. detect an interrupted in-flight delegation;
7. reconstruct the next legal lifecycle action;
8. acquire the work-item lease;
9. persist a new checkpoint and activity event.

A delegation is complete only when its declared result file exists and validates as a completed subagent result. A packet without a valid completed result is treated as interrupted. The replacement uses a new invocation ID; the previous invocation is retained as evidence.

Read-only inspection does not acquire a lease and must not modify state or journal files:

```bash
python3 <install-root>/bin/t-thinkctl.py resume TSREX-RAW-001 \
  --repository-root . \
  --read-only
```

## Lease behavior

When another non-stale session owns the work item, mutating resume is rejected. The root agent offers only:

- open read-only;
- cancel.

When a lease is stale, takeover still requires an explicit choice:

```bash
python3 <install-root>/bin/t-thinkctl.py resume TSREX-RAW-001 \
  --repository-root . \
  --session-id SESSION-NEW \
  --takeover-stale
```

Long-running work refreshes the lease:

```bash
python3 <install-root>/bin/t-thinkctl.py heartbeat \
  --file .t-think/TSREX-RAW-001/state.yaml \
  --session-id SESSION-NEW
```

Before a root session ends, checkpoint and release it:

```bash
python3 <install-root>/bin/t-thinkctl.py release \
  --file .t-think/TSREX-RAW-001/state.yaml \
  --session-id SESSION-NEW \
  --reason user_session_ended
```

A released unfinished work item becomes `interrupted`, making it visible in the next session-entry menu.

## Checkpoint protocol

Checkpointing is mandatory:

- after a lifecycle transition;
- before and after a delegation;
- after a batch of source modifications;
- after a review finding;
- before asking the human a semantic question;
- after a tool error or timeout;
- before the root response ends.

Example:

```bash
python3 <install-root>/bin/t-thinkctl.py checkpoint \
  --file .t-think/TSREX-RAW-001/state.yaml \
  --status active \
  --last-action "Builder completed TASK-003" \
  --next-action "Run independent technical review" \
  --next-action-type delegation \
  --changed-file src/raw-capture.ts \
  --verification-pending "npm test"
```

After validating a worker result:

```bash
python3 <install-root>/bin/t-thinkctl.py record-result \
  --file .t-think/TSREX-RAW-001/state.yaml \
  --result .t-think/TSREX-RAW-001/results/INV-123.yaml
```

`record-result` clears the matching in-flight delegation, updates completed and remaining tracks, persists unresolved findings, and identifies the next action.

## Legacy work items

A pre-v2.6 work item with work-state schema `2.3.0` remains readable. The first mutating resume creates the `session/` directory, upgrades the state to schema `2.4.0`, writes a checkpoint and journal, and preserves existing lifecycle artifacts. A read-only inspection performs no migration or write.

## Failure rules

- Chat prose never proves completion.
- Missing, partial, malformed, or non-completed result artifacts never satisfy a delegation.
- A worker may not continue from an orphaned private context.
- A second mutating session may not bypass an active lease.
- `Show all` and inspection never alter timestamps, status, checkpoint, lease, or activity journal.
- Session files may exist only under `.t-think/<work-id>/session/` with the canonical names defined above.
