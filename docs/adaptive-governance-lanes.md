# Adaptive governance lanes

The authoritative lane paths are in `orchestrator/lane-registry.yaml`. Quick has five working phases, standard nine, and full twelve. Promotion is monotonic and loops back to the earliest newly required phase. Composite phase details are in `orchestrator/composite-phase-policy.yaml`. Independent technical review is mandatory in every lane; security and breaking review are mandatory in standard/full.
