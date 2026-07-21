# Model Taxonomy

Model elements describe bounded system concepts, not proposed solutions.

- Structural: `ACTOR`, `ENTRY_POINT`, `COMPONENT`, `MODULE`, `DATA_STORE`, `DATA_ENTITY`, `EXTERNAL_DEPENDENCY`.
- Behavioral: `PROCESS`, `OPERATION`, `MESSAGE`, `EVENT`, `STATE`, `STATE_TRANSITION`.
- Boundaries: `TRANSACTION_BOUNDARY`, `CONCURRENCY_BOUNDARY`, `RETRY_BOUNDARY`, `SECURITY_BOUNDARY`, `OWNERSHIP_BOUNDARY`.
- Semantics: `SOURCE_OF_TRUTH`, `CONTRACT`, `CONFIGURATION`, `OBSERVABILITY_POINT`, `INVARIANT`.
- Problem explanation: `ACTUAL_BEHAVIOR`, `INTENDED_BEHAVIOR`, `BEHAVIOR_GAP`, `FAILURE_PATH`, `MODEL_LIMITATION`.

Every active element must cite actual investigation evidence. Inference-backed elements must include a structured reasoning summary, alternative explanations, falsification conditions, and limitations.
