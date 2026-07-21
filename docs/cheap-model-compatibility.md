# Economy-model compatibility

`t-think` does not depend on a flagship model. Reliability is shifted from hidden model memory to explicit state, small role prompts, one active phase skill, schemas, validators, immutable digests, bounded retries, independent contexts, and human semantic gates.

## Default economy contract

- role subagents are enabled;
- execution is sequential;
- maximum active skills: one;
- maximum active workers: one;
- delegation depth: one;
- model and reasoning settings: inherited;
- context: fresh role invocation with only required upstream artifacts;
- output: template-first and schema-valid;
- uncertainty: `UNKNOWN`, `CONFLICT`, `BLOCKED`, or loopback;
- retries: at most one constrained retry per validation category;
- transition authority: `t-think` only after machine validation.

The purpose of a real subagent in economy mode is context and authority isolation, not parallelism.

## Prompt-budget controls

- canonical `t-think` core remains compact;
- role prompts remain small and stable;
- full skill instructions are loaded only for the active phase;
- raw command output and logs are saved as evidence and summarized;
- artifact references and digests replace repeated document copies;
- completion criteria are explicit and enumerable;
- workers do not receive the entire conversation;
- workers cannot recursively delegate.

## Escalation instead of default expense

Use a stronger model only after a recorded trigger, such as repeated failure, security-sensitive reasoning, destructive migration, unresolved concurrency proof, contradictory evidence, or nondeterministic verification. The phase contract, artifacts, permissions, and human gates do not change during escalation.

## Tested offline

The bundle tests:

- role and phase routing;
- model-neutral adapters;
- prompt-size ceilings;
- context/delegation depth contracts;
- source-write authority;
- ignored-file, protected-path, and outside-workspace violations;
- result-envelope and transition validation;
- copy and symlink installation;
- all phase validators and unit tests.

These tests prove the governance machinery, not identical reasoning quality from every third-party model. A weak model is expected to stop safely when evidence or reasoning is insufficient.
