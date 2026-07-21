# Material Option Distinctness

Options are materially distinct when they produce different engineering guarantees or operational consequences. Compare enforcement boundary, source of truth, consistency model, transaction and concurrency semantics, compatibility, migration, failure behavior, ownership, and residual risk.

The following are not distinct by themselves:

- different class or method names;
- different helper decomposition;
- equivalent library choices;
- different prose for the same enforcement mechanism;
- a base option plus unrelated cleanup;
- synchronous and asynchronous wording when the committed guarantee is unchanged.

The validator computes a conservative fingerprint from mechanism, enforcement points, distinguishing dimensions, transaction semantics, concurrency semantics, and failure semantics. Human critique must still assess deeper semantic equivalence.
