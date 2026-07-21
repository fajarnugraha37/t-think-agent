# Evidence Taxonomy

## Claim versus source

A claim is the statement being asserted. A source is the inspectable origin supporting or informing that claim.

Do not confuse:

- “file X contains method Y” — claim;
- `src/.../X.java:10-20` at commit SHA — source.

## Direct system facts

A `SYSTEM_OBSERVED` fact needs at least one source with:

```yaml
authority: DIRECT
source_context: ACTUAL_SYSTEM
```

Examples include source code at an exact commit, command output, test output, runtime behavior, traces, logs, database query evidence, or deployed configuration.

## Human-reported facts

A human report can prove only that the human reported an observation. It does not independently prove actual system behavior.

## Inferences

An inference must be reconstructable from cited claim IDs and a concise rationale. Include alternatives and falsification conditions.

## Negative claims

Negative claims require explicit search scope. Prefer “not found in inspected scope” over universal absence.

## Generated artifacts

The evidence ledger and investigation log are indexes and interpretations. They do not become independent proof of their own claims.
