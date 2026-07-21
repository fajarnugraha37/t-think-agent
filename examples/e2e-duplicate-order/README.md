# End-to-End Simulation — Duplicate Order Creation

This example is a realistic walkthrough for a Jakarta REST/Java order API using PostgreSQL and Kafka. It demonstrates successful gates plus four critique-driven loopbacks. The files are illustrative orchestration fixtures; each phase skill also contains fully validator-tested examples under its own `examples/` directory.

## Loopbacks demonstrated

1. Model critique → System Model: concurrent multi-pod path missing.
2. Plan critique → Implementation Plan: migration ordering unsafe.
3. Checklist critique → Implementation Checklist: non-atomic operation.
4. Self Review → Bounded Implementation: required metric omitted.

See `lifecycle-run.yaml`, `critique-log.jsonl`, and `traceability-summary.csv`.
