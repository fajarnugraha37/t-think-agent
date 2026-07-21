# Semantic decision guard

The following are semantic decisions and cannot be introduced here: business rules, public contracts, persistence strategy, transaction or concurrency semantics, retry/fallback behavior, state transitions, security trade-offs, compatibility compromises, dependencies, and migration strategy.

When one is required, emit a blocking `SEMANTIC_DECISION_REQUIRED` finding and route to `SOLUTION_DESIGN`.
