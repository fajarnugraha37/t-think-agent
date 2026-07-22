# Graphify-first repository intelligence

`t-think` treats Graphify as an optional repository-navigation and impact-analysis layer. The canonical behavior lives in `orchestrator/repository-intelligence-policy.md`.

## Ownership

The root orchestrator decides whether structural discovery is needed, resolves repository scope, checks local Graphify documentation or help before using any command, runs focused read-only discovery when Graphify is usable, and creates a compact repository-intelligence evidence artifact.

The artifact is validated with `schemas/repository-intelligence.schema.json` and attached to a delegation through the existing `artifact_inputs` contract. This preserves the current delegation schema and lets terminal workers reuse completed discovery instead of repeating it.

## Availability

Graphify is usable only when all are true:

1. a locally supported executable or integration is available;
2. locally installed Graphify documentation, a `SKILL.md`, project script, or command help identifies the read-only operation being used;
3. the current repository graph is reported usable or queries are confirmed to work;
4. the current agent has permission to execute the read-only operation.

Repository root detection prefers read-only Git metadata and otherwise uses the current working directory. The policy never assumes a graph directory.

## When Graphify is used

Use focused queries for unfamiliar or cross-boundary work involving architecture, dependencies, callers and callees, request or execution flow, event and message flow, persistence, configuration relationships, implementation ownership, and change-impact analysis.

Skip Graphify for known exact files or symbols, trivial localized edits, formatting-only changes, build/test/lint execution, user-provided paths, generated or vendored code, and work where graph traversal adds no value.

## Fail-open behavior

Missing executable, missing graph, stale data, denied operation, or failed query never blocks normal work. Agents continue with source inspection, search, LSP or symbol resolution, compiler or type checker, configuration inspection, and tests.

The system never installs, upgrades, initializes, generates, rebuilds, updates, or mutates Graphify automatically.

## Verification boundary

Graph output is navigation and impact-analysis evidence, not final authority. Implementation-critical claims must be verified against source and executable evidence.

Static extraction can miss or incompletely represent reflection, dependency injection, dynamic dispatch, generated code, framework conventions, runtime configuration, event or message routing, database-side logic, plugins, and external systems.

## Freshness

Treat findings as `possibly_stale` when relevant source, configuration, or generated files changed after graph generation; the active branch differs materially from the graph source; Graphify reports staleness; or graph findings conflict with source.

When staleness matters, lower confidence and verify directly. Graph refresh is allowed only when explicit authorization or an existing project policy permits it.

## Platform adapters and installation

`orchestrator/repository-intelligence-policy.md` is the single semantic source. `scripts/generate_adapters.py` includes it only in the four root `t-think` adapters for OpenCode, Codex, Claude Code, and Cursor. Worker adapters remain small and receive repository intelligence through delegation evidence.

Both `bin/install.sh` and `bin/install.ps1` regenerate adapters before installation. This prevents a checkout or release bundle from installing stale generated adapter output. The generator does not execute Graphify and does not alter a project graph.

## Delegation example

```yaml
artifact_inputs:
  - ref: .t-think/ORDER-2471/evidence/repository-intelligence.yaml
    sha256: <sha256>
```

The referenced artifact follows:

```yaml
graphify_status: available
repository_root: /workspace/project
queries_performed:
  - focused impact query for order creation flow
findings:
  - entity: OrderResource
    relationship: calls OrderService and publishes OrderCreated
    evidence: focused Graphify query result
    confidence: medium
affected_areas:
  - order-api
  - order-service
  - order-events
uncertainties:
  - runtime event routing may add consumers
verification_required:
  - inspect source callers and dependency-injection bindings
  - run compiler and affected contract tests
```

## End-to-end example

A cross-module change follows this flow:

1. `t-think` detects that structural discovery is useful.
2. It checks local Graphify documentation and availability quietly.
3. It performs focused structural and impact queries when usable.
4. It validates and delegates concise findings and uncertainties.
5. The planner maps affected contracts, schemas, tests, and documentation.
6. The builder verifies source before editing and remains restricted to approved targets.
7. Reviewers compare the diff against the expected impact surface.
8. Compiler, tests, configuration checks, and runtime evidence provide final validation.
