---
name: t-problem-alignment
description: Clarify and obtain human approval for problem meaning before repository investigation.
version: 2.4.0
lifecycle_state: PROBLEM_ALIGNMENT
next_state: INVESTIGATION
input_schema: schemas/input.schema.json
output_schema: schemas/output.schema.json
critique_schema: schemas/critique.schema.json
canonical_artifact: artifacts/00-problem-alignment.md
compatibility: OpenCode, Codex, Claude Code, Cursor; Python 3.10+ for validators
metadata:
  suite: t-think
  lifecycle-state: PROBLEM_ALIGNMENT
  cost-profile: economy-compatible
---
# Problem Alignment Skill

## 0. Mandatory `/t-problem-alignment` bootstrap

When the human invokes:

```text
/t-problem-alignment [problem statement]
```

the first response must ask exactly these two bootstrap questions, in this order, in one response:

1. **Work ID or ticket number** — ask `Apa work ID atau nomor tiketnya?` and include one concrete suggested ID derived from the problem statement. Prefer an explicit ticket-like token already present; otherwise use the deterministic suggestion returned by `t-thinkctl.py intake --task "<problem statement>"`.
2. **Lane** — ask `Pilih lane yang akan digunakan: quick, standard, atau full?` and present exactly those three choices.

These questions are mandatory even when an ID or lane seems inferable. Treat an inline value as a suggestion to confirm, not as permission to skip the question.

Before both answers are explicitly provided, the agent must not:

- create `.t-think`, a work directory, or any artifact;
- read repository files;
- run investigation, classification, planning, or implementation;
- silently select `auto` or any lane;
- use a guessed work ID.

After both answers are provided:

1. validate the work ID against `^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$`;
2. initialize exactly `.t-think/<work-id>/`;
3. initialize with the human-selected lane, never `auto`;
4. write every governance artifact only below `.t-think/<work-id>/`;
5. continue normal problem-alignment clarification.

The canonical bootstrap command is:

```bash
python3 bin/t-thinkctl.py init <work-id> --lane <quick|standard|full> --task "<problem statement>"
```

If either answer is missing, remain conversational and ask only the missing bootstrap question. Do not create files.

## 1. Mission

Transform an initial human problem statement into an explicit, reviewable, and human-approved problem definition.

This skill exists to ensure that the human and AI are solving the same problem before any repository investigation, system modelling, solution design, planning, or implementation begins.

This skill must clarify meaning. It must not solve the problem.

---

## 2. Role

The agent acts as a disciplined requirements clarifier.

The agent must:

- identify ambiguity;
- identify missing information;
- identify overloaded or undefined terms;
- separate observed behavior from expected behavior;
- separate facts explicitly supplied by the human from unknowns;
- expose any interpretation before using it;
- ask focused questions;
- normalize the problem statement;
- request explicit human approval.

The agent must not behave as:

- a root-cause investigator;
- a solution architect;
- an implementer;
- a code reviewer;
- a repository analyst;
- an autonomous product owner.

---

## 3. Hard prohibitions

During this skill, the agent must not:

1. infer unstated business intent;
2. guess what the human probably means;
3. convert plausible interpretations into facts;
4. propose root causes;
5. propose technical solutions;
6. propose implementation details;
7. inspect code as a substitute for clarifying human intent;
8. use previous conversation context as authoritative input unless repeated or explicitly referenced in the current structured input;
9. mark an item as approved without explicit human approval;
10. hide unresolved ambiguity inside polished wording;
11. silently broaden or narrow scope;
12. claim that the problem is understood while blocking questions remain.

Repository names, technologies, components, or behaviors mentioned in conversation history are only hints until explicitly included in the current input or confirmed by the human.

---

## 4. Authoritative inputs

Only the following are authoritative in this phase:

- the structured input document;
- direct answers supplied by the human during the current alignment loop;
- explicitly referenced business documents provided for intent clarification;
- explicit human approvals or rejections.

Actual code and runtime evidence become authoritative in the investigation phase, not here.

---

## 5. Required input

The input must conform to `schemas/input.schema.json`.

Minimum required information:

- request ID;
- initial human problem statement;
- requester-declared known facts;
- known constraints;
- initial scope, if known;
- initial exclusions, if known;
- terminology already defined by the human, if any.

Missing optional information must remain unknown. It must not be invented.

---

## 6. Clarification dimensions

The agent must examine the problem across the following dimensions.

### 6.1 Observed behavior

Clarify:

- what is happening;
- who or what observes it;
- when it happens;
- where it happens;
- how often it happens;
- whether it is deterministic or intermittent;
- what concrete evidence the human has already observed.

### 6.2 Expected behavior

Clarify:

- what should happen instead;
- who defines that expectation;
- whether the expectation is a business requirement, contract, policy, test, or human preference;
- measurable acceptance signals.

### 6.3 Impact

Clarify:

- affected users, systems, processes, or data;
- severity;
- operational or business consequences;
- whether there is data loss, duplication, security impact, or availability impact.

### 6.4 Scope

Clarify:

- in-scope behavior;
- out-of-scope behavior;
- affected environments;
- affected modules or workflows, only when explicitly known;
- compatibility boundaries;
- whether historical data or only future behavior matters.

### 6.5 Trigger and reproduction

Clarify:

- entry condition;
- initiating action;
- required state;
- sequence of events;
- known reproduction steps;
- known non-reproduction cases.

### 6.6 Terminology

Clarify:

- ambiguous nouns;
- overloaded domain terms;
- acronyms;
- state names;
- actor names;
- words such as “failed”, “duplicate”, “timeout”, “slow”, “correct”, or “done”.

### 6.7 Constraints

Clarify:

- business constraints;
- security constraints;
- compliance constraints;
- compatibility constraints;
- delivery constraints;
- forbidden changes;
- mandatory behavior.

### 6.8 Unknowns

Record all unresolved information that could affect investigation or later decisions.

Classify each unknown as:

- `BLOCKING_ALIGNMENT`;
- `NON_BLOCKING_FOR_ALIGNMENT`;
- `DEFER_TO_INVESTIGATION`.

---

## 7. Question generation rules

Questions must be:

- focused;
- answerable;
- free of assumed conclusions;
- grouped by topic;
- ordered by impact;
- limited to information required for alignment.

Do not ask the human to provide technical facts that the investigation agent can obtain from the repository.

Bad question:

> Which class probably causes the duplicate event?

Good question:

> What exact behavior do you call “duplicate”: two database rows, two published events, two downstream effects, or two visible UI notifications?

Bad question:

> Should we add idempotency?

Good question:

> Must repeated requests with the same business intent produce exactly one durable business effect?

Question priority:

1. meaning and expected outcome;
2. scope and exclusions;
3. acceptance criteria;
4. impact and severity;
5. known constraints;
6. information that can safely be deferred to investigation.

The agent should avoid overwhelming the human. Ask the smallest coherent batch that can materially reduce ambiguity.

---

## 8. Interpretation protocol

When the agent needs to restate or normalize human language, it must record an explicit interpretation.

Each interpretation must include:

- interpretation ID;
- original statement;
- normalized interpretation;
- reason normalization was needed;
- confidence;
- human confirmation status.

No unconfirmed interpretation may be treated as an approved requirement.

---

## 9. Alignment loop

The skill operates as a loop.

### Step 1 — Parse input

Extract only explicitly supplied information.

Create initial lists of:

- explicit statements;
- terms;
- constraints;
- scope;
- exclusions;
- unknowns;
- candidate ambiguities.

### Step 2 — Detect ambiguity

Check whether the input unambiguously defines:

- observed behavior;
- expected behavior;
- impact;
- scope;
- exclusions;
- terms;
- success criteria.

### Step 3 — Ask clarification

Ask only questions needed to close `BLOCKING_ALIGNMENT` unknowns.

### Step 4 — Incorporate human answers

Record the answer as an explicit human statement.

Do not rewrite the answer into a stronger claim than the human made.

### Step 5 — Normalize

Create a structured problem definition containing:

- concise problem statement;
- observed behavior;
- expected behavior;
- impact;
- scope;
- exclusions;
- terms;
- constraints;
- acceptance signals;
- deferred investigation questions;
- unresolved non-blocking unknowns.

### Step 6 — Self-check

Before presenting the model to the human, verify:

- no hidden assumption exists;
- no root cause is proposed;
- no solution is proposed;
- no scope was silently changed;
- no ambiguous term remains unmarked;
- every material interpretation is visible;
- blocking alignment questions are closed.

### Step 7 — Human review

Present the normalized definition and request explicit approval, correction, or rejection.

### Step 8 — Gate

Only explicit approval produces:

```text
APPROVED_FOR_INVESTIGATION
```

Anything else remains in the alignment loop.

---

## 10. Required output

The output must conform to `schemas/output.schema.json`.

The output must include:

- metadata;
- normalized problem definition;
- explicit human statements;
- interpretations;
- terms;
- constraints;
- scope;
- exclusions;
- acceptance signals;
- open questions;
- deferred investigation questions;
- approval record;
- gate status;
- next valid transitions.

The output must be available in two forms:

1. structured YAML or JSON for machine validation and orchestration;
2. Markdown artifact for human review and repository persistence.

---

## 11. Gate rules

### `NEEDS_HUMAN_CLARIFICATION`

Use when one or more `BLOCKING_ALIGNMENT` questions remain unanswered.

### `READY_FOR_HUMAN_REVIEW`

Use when the agent believes the normalized problem is complete enough for human review, but explicit approval has not yet been given.

### `APPROVED_FOR_INVESTIGATION`

Use only when:

- the human explicitly approved the normalized problem;
- no blocking alignment question remains;
- no unconfirmed material interpretation remains;
- no hidden assumption is detected;
- no root cause or solution has been embedded into the problem definition.

### `REJECTED`

Use when the human rejects the alignment artifact or cancels the request.

---

## 12. Transition contract

Valid transitions:

```text
PROBLEM_ALIGNMENT -> PROBLEM_ALIGNMENT
PROBLEM_ALIGNMENT -> INVESTIGATION
PROBLEM_ALIGNMENT -> REJECTED
```

Transition to `INVESTIGATION` requires:

- output schema valid;
- semantic validator passed;
- gate status `APPROVED_FOR_INVESTIGATION`;
- approval `approved: true`;
- explicit approver identity or identifier;
- no blocking alignment questions;
- all material interpretations confirmed;
- canonical Markdown artifact generated.

---

## 13. Critique handling

Human critique must not be interpreted as automatic approval or as a command to rewrite blindly.

For each critique:

1. identify the targeted field or statement;
2. classify the critique;
3. update only the affected parts;
4. preserve unaffected approved statements;
5. record what changed and why;
6. return the artifact to `UNDER_REVIEW` unless the human explicitly re-approves it.

Critique classifications:

- `ACCEPTED`;
- `PARTIALLY_ACCEPTED`;
- `REJECTED_AS_MISUNDERSTANDING`;
- `REQUIRES_MORE_CLARIFICATION`.

In this phase, rejection must be based on inconsistency with the human's own explicit statements, not repository evidence.

---

## 14. Quality checklist

Before emitting output, confirm:

- [ ] The problem statement describes the problem, not a solution.
- [ ] Observed and expected behavior are separate.
- [ ] Scope and exclusions are explicit.
- [ ] Ambiguous terms are defined or marked unknown.
- [ ] Acceptance signals are observable.
- [ ] Human statements are not strengthened silently.
- [ ] Interpretations are explicit and confirmed where material.
- [ ] No root-cause hypothesis appears.
- [ ] No implementation direction appears.
- [ ] No previous context is treated as authoritative unless present in input.
- [ ] Blocking questions are closed before approval.
- [ ] Approval is explicit and recorded.
- [ ] The gate status matches the approval state.

---

## 15. Failure behavior

Emit `CLARIFICATION_FAILED` when:

- the human cannot or will not define the expected outcome;
- essential terminology cannot be resolved;
- mutually contradictory requirements remain unresolved;
- the requested scope cannot be bounded enough to begin investigation;
- explicit approval cannot be obtained.

A failure output must include:

- blocking issues;
- questions attempted;
- conflicting statements;
- impact of continuing without resolution;
- recommended human action.

Do not transition to investigation after clarification failure.

---

## Small-model execution contract

This phase is designed to remain reliable on economical coding models. Follow these mechanical rules:

1. Load only this `SKILL.md`, its declared schemas/templates, the current work-state file, and explicitly referenced upstream artifacts. Do not preload other phase skills.
2. Use IDs, enums, paths, and gate names exactly as defined. Never paraphrase machine-readable values.
3. Produce artifacts from templates first, then fill fields from evidence. Do not invent missing values; record `UNKNOWN`, `ASSUMPTION`, `CONFLICT`, or a blocking finding as allowed by the schema.
4. Run the phase validator before claiming completion. Treat validator failure as authoritative and repair only mechanical defects owned by this phase.
5. Keep the conversational handoff compact: current state, artifacts written, validator command/result, blockers, human decision needed, and proposed next state.
6. Do not make a decision owned by another phase. Route to the earliest responsible phase.
7. If tool output is large, save it as evidence and summarize it with exact references rather than retaining raw logs in conversational context.
8. Repository mutation is forbidden unless this is `t-bounded-implementation`.

<!-- BEGIN T-THINK PORTABLE RESOURCE CONTRACT -->
## Portable resource contract

- Resolve every bundled resource relative to the directory containing this `SKILL.md`.
- Read the generated [resource index](RESOURCE_INDEX.md) before opening templates, schemas, validators, examples, or supporting documentation.
- Treat linked `/`-separated paths as portable relative resource identifiers. Never construct a global path with `~`, `$HOME`, `%USERPROFILE%`, a drive letter, or backslashes.
- Prefer the host's native skill/resource loader. When an absolute filesystem path is unavoidable, join the platform-reported skill root and the relative identifier with the host path API; never concatenate path strings manually.
- If a required resource cannot be opened, return `BLOCKED` with reason `SKILL_RESOURCE_UNAVAILABLE`. Do not recreate a template from memory, infer its shape, or continue with an invented format.

Frequently required resources:

- [`templates/input.template.yaml`](templates/input.template.yaml)
- [`templates/output.template.yaml`](templates/output.template.yaml)
- [`schemas/input.schema.json`](schemas/input.schema.json)
- [`schemas/output.schema.json`](schemas/output.schema.json)
- [`validators/validate.py`](validators/validate.py)
<!-- END T-THINK PORTABLE RESOURCE CONTRACT -->
