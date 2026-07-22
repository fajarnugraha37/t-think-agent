# Repository Intelligence Policy

This policy is shared by `t-think` and every terminal `t-*` worker. It adds Graphify as an optional, fail-open repository-intelligence layer. It does not change lifecycle authority, write permissions, evidence requirements, or platform isolation.

## Deterministic decision

1. Resolve repository root with read-only Git metadata when available; otherwise use the current working directory.
2. Decide whether structural discovery is needed.
3. Structural discovery is needed for unfamiliar repositories, cross-file or cross-module work, architecture discovery, dependency or call-chain analysis, request/execution/data/message flows, implementation ownership, configuration relationships, and change-impact analysis.
4. Structural discovery is not needed for a known exact file or symbol, a trivial localized edit, formatting-only work, user-provided exact paths, generated/vendor inspection, or direct build/test/lint execution.
5. When structural discovery is needed, use Graphify first only when all are true:
   - a locally supported Graphify executable or integration is available;
   - its locally installed documentation or help identifies the read-only availability/query operation being used;
   - the current repository graph is reported usable or the integration confirms queries can run;
   - the current agent has permission for that read-only operation.
6. Otherwise continue immediately with source inspection, search, LSP/symbol resolution, compiler/type checker, configuration inspection, and tests.

Never invent Graphify commands. Before running or documenting a command, read the locally installed Graphify `SKILL.md`, integration documentation, project script, `graphify --help`, or relevant subcommand help. Do not install, upgrade, initialize, generate, rebuild, update, or mutate a graph automatically.

## Graphify-first uses

Use focused Graphify queries for architecture, dependencies, callers/callees, cross-module behavior, producer-consumer and event/message flows, persistence paths, API-to-service-to-database paths, configuration relationships, ownership, and potentially affected modules, files, schemas, tests, and documentation.

Prefer the smallest query that answers the structural question. Do not load an entire graph or paste verbose graph output into delegation or chat.

## Evidence boundary

Graphify output is navigation and impact-analysis evidence, not final authority. Verify implementation-critical findings against source code and relevant executable or runtime evidence. Static extraction may miss or incompletely represent reflection, dependency injection, dynamic dispatch, generated code, framework conventions, runtime configuration, event/message routing, database-side logic, plugins, and external systems.

Classify graph-derived findings separately from source-verified facts. When Graphify conflicts with source, source and executable evidence win.

## Freshness

Treat findings as `possibly_stale` when relevant source/config/generated files changed after graph generation, the branch differs materially from the graph source, Graphify reports staleness, or findings conflict with source. Do not perform expensive freshness checks for trivial work. When staleness matters, lower confidence and verify directly. Update the graph only when explicit authorization or an existing project policy permits it.

## Failure behavior

Graphify is fail-open. If unavailable, missing, stale, unauthorized, or a query fails:

- do not stop the task;
- continue with normal repository tools;
- record `unavailable`, `failed`, or `possibly_stale` when repository intelligence is included in delegation;
- mention the limitation to the user only when it materially reduces confidence or completeness;
- never install Graphify or create/update a graph automatically.

## Orchestration and delegation

`t-think` owns the first availability decision and initial focused discovery by default. It passes a compact `repository_intelligence` object in the delegation packet. Workers reuse those findings and do not repeat completed queries unless their bounded objective requires a deeper unresolved relationship.

The object contains status, repository root, queries performed, concise findings, affected areas, uncertainties, and mandatory verification checks. `not_needed` is valid and preferred for local work.

## Role behavior

- `t-investigator` and `t-modeler`: use Graphify first for structural discovery when the packet does not already answer the question; distinguish graph findings from verified facts and preserve uncertainty.
- `t-planner`: consume the expected impact surface, map components/contracts/schemas/tests/docs, inspect dynamic relationships directly, and include executable validation steps. Do not convert every graph edge into a task.
- `t-builder`: use findings only to narrow search; inspect actual source before editing; never treat graph findings as write authorization; run relevant compiler/tests/lint.
- `t-reviewer`, `t-security-reviewer`, and `t-breaking-reviewer`: compare the diff with the expected impact surface, look for missed callers/consumers/configuration/schemas/migrations/tests/docs, account for stale graphs, and verify assumptions directly.
- `t-verifier`: use Graphify only to locate affected flows or consumers; derive final test scope from changed behavior and source evidence.
- `t-reconciler`: confirm graph-derived assumptions were verified and unresolved uncertainty is represented in residual risk.
- `t-critic`: challenge unsupported graph conclusions and duplicated or excessive discovery.

Small or local work should inherit this policy without running Graphify.