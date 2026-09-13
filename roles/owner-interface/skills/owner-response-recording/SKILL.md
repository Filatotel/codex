---
name: owner-response-recording
description: Compile the Owner's actual natural-language answer to an already-presented genuine Owner gate into the existing OWNER_DECISION_RECORD without inventing intent.
---

# Owner Response Recording

## Purpose

Use this skill after the Owner has answered a genuine decision surface produced by `owner-decision-surface`.

## Goal

Normalize only what the Owner actually said, map it deterministically to the already-presented canonical option set, preserve explicit qualifications, and materialize the existing `OWNER_DECISION_RECORD` contract only when the decision is unambiguous.

```text
LIAISON NORMALIZATION != LIAISON DECISION
```

## When to use

Use this skill when:

- an exact Owner decision surface and its canonical option mapping are available;
- the Owner replies with a compact human label, canonical option, or unambiguous natural equivalent;
- the Owner adds bounded qualifications, constraints, or a condition that qualifies one selected option;
- a durable Owner decision must be returned to Control Director.

Do not use this skill when:

- no genuine Owner gate was presented;
- the answer could map to multiple materially distinct options;
- the Owner omitted the selection and only repeated a recommendation/rationale;
- the Owner delegates authority to Liaison instead of choosing;
- the answer requires a branching conditional choice that the existing single-`selected_option` schema cannot faithfully represent.

## Inputs

Require:

- exact decision/question ref;
- exact option set that was presented;
- deterministic human-label -> canonical-option mapping;
- the Owner's actual response text or durable response ref;
- relevant assignment/input-state/provenance refs needed by the existing record contract;
- consequences/constraints that were presented, only as needed to preserve explicit acknowledgements or qualifications.

The existing authoritative schema is `schemas/owner-decision-record.schema.json`. Do not create a replacement or parallel decision artifact family.

## Execution contract

**Required execution capabilities for mandatory reasoning/compilation steps:** model reasoning plus reads of the supplied decision surface, Owner response, and authoritative `OWNER_DECISION_RECORD` contract.

**Required capability for a durable-materialization claim:** `durable_artifact_write`.

**Supported execution modes:**

| Mode | Required capabilities | Claim/evidence boundary |
|---|---|---|
| compile-only | supplied/readable gate + response + schema | May emit a schema-shaped candidate and clarification/schema-limit verdicts; must not claim a durable decision was recorded. |
| durable record | compile-only prerequisites + `durable_artifact_write` | May materialize and return an `OWNER_DECISION_RECORD` bound to the exact Owner response and decision surface. |

**Conditional / optional capabilities:** schema validator when available. Validation strengthens structural evidence but never authorizes semantic inference.

**Mandatory evidence paths and equivalent fallbacks:** selected option must be provably one member of the exact `options_presented` set and traceable through the decision-surface mapping or exact canonical wording in the Owner response. Material qualifications must be traceable to the Owner's words. There is no equivalent fallback for semantic ambiguity.

**Unsupported environment behavior:** if durable recording is mandatory but `durable_artifact_write` is unavailable, return `ASSIGNMENT_NOT_ADMISSIBLE` for the durable claim. If the response is ambiguous, return a bounded clarification requirement. Never weaken either failure into inferred consent.

## Required outputs

On unambiguous selection, produce the repository's existing `OWNER_DECISION_RECORD` semantics with:

- `artifact_type: OWNER_DECISION_RECORD`;
- `produced_by_role: owner-interface`;
- `status: RECORDED` only for an actually materialized durable record;
- exact `question_ref`;
- exact canonical `options_presented`;
- exact canonical `selected_option`;
- explicit `owner_constraints` stated by Owner, without additions;
- explicit `qualifications` when present;
- `consequences_acknowledged` only to the extent actually acknowledged; an empty array is preferable to invented acknowledgement;
- required envelope/provenance/related-artifact fields from the current contract;
- optional authority/specialized fields only when the underlying authorized gate actually supplies their semantics.

On ambiguity or authority attack, produce no selected Owner decision record. Return only the bounded clarification/refusal result needed to preserve the original gate.

## Deterministic normalization rules

### 1. Compact natural answer

If the response maps to exactly one presented label/canonical option, compile that exact option.

Example:

```text
Presented mapping:
"Keep current behavior" -> OPTION_A
"Use safer default" -> OPTION_B

Owner: "Safer default. Only for this release."
selected_option = OPTION_B
owner_constraints/qualifications preserve "Only for this release."
```

Do not store the human paraphrase as a new semantic option when a canonical option already exists.

### 2. Canonical answer

If Owner states `OPTION_B` exactly and it was presented, use `OPTION_B` without reinterpretation.

### 3. Bounded qualifications and constraints

Preserve every material Owner qualification. Do not:

- broaden "only for staging" into production authority;
- drop "not before audit";
- convert "prefer" into a binding constraint;
- convert a binding "only if" into optional prose.

Use `owner_constraints` for explicit binding limits and `qualifications` for other explicit decision qualifications. If the distinction is materially unclear, request clarification rather than silently classifying it.

### 4. Conditional choices

A condition that qualifies one selected option can be preserved when the existing record faithfully represents it, for example: "Choose B, but only after audit passes." -> `selected_option = B` plus the explicit condition in constraints/qualifications.

A branching choice such as "B if X, otherwise A" does not have one unconditional `selected_option`. Because the current schema exposes one required `selected_option`, do not manufacture either A or B. Return `SCHEMA_LIMITATION` with the exact representational gap unless the Owner resolves the branch into one current selection.

### 5. Ambiguous response

If multiple materially distinct options remain plausible, return `CLARIFICATION_REQUIRED` and ask only the smallest question needed to distinguish them. No record may claim a selection.

Examples that fail closed:

- "Either is fine" when A and B are materially distinct;
- "Go with that" when multiple referents are plausible;
- "yes" when the surface was not framed as one unambiguous yes/no mapping;
- response that selects one label but adds a qualification that materially conflicts with the option semantics.

### 6. Authority delegation attack

Owner input such as "use your judgment and approve for me" does not select a presented Owner-reserved option. Liaison may restate its prior recommendation but must return the unresolved Owner gate. No `OWNER_DECISION_RECORD` with a selected option is permitted.

## Procedure

1. Bind the response to the exact previously presented question and mapping.
2. Confirm that `options_presented` are the exact canonical options from that surface.
3. Extract only explicit selection language, constraints, qualifications, and acknowledgements from the Owner response.
4. Resolve the selection through the canonical option or deterministic human-label mapping.
5. If zero or multiple canonical options remain materially possible, return `CLARIFICATION_REQUIRED`; do not construct a selected record.
6. If the response attempts to delegate Owner authority to Liaison, refuse self-selection and preserve the gate.
7. If the response is an explicit conditional, determine whether it qualifies one selected option or encodes multiple future selections. For a multi-branch selection not faithfully representable by the current schema, return `SCHEMA_LIMITATION` rather than widening the schema.
8. Populate only fields supported by the existing schema and exact source semantics. Do not add authority scope that the Owner did not decide.
9. Validate structure when a validator is available. Structural validity does not cure semantic ambiguity.
10. Materialize `status: RECORDED` only when durable write capability is available and the semantic mapping is exact.
11. Return the durable record and affected state/control refs to Control Director. Liaison does not itself authorize the downstream transition.

## Existing schema authority

`schemas/owner-decision-record.schema.json` remains authoritative. This skill must not create:

- `OWNER_DECISION_RECORD_V2`;
- `LIAISON_DECISION`;
- `OWNER_AUTHORITY_PROXY`;
- any second Owner-decision artifact family.

If an essential bounded Owner answer cannot be represented without changing its meaning, stop with `SCHEMA_LIMITATION` and identify the exact missing representational capability. Do not redesign the schema inside this skill/workstream.

## Anti-patterns

Avoid:

- choosing the system recommendation because Owner did not object;
- treating silence, politeness, or "looks good" as a selection when the mapping is not exact;
- selecting an omitted option;
- dropping constraints to make the record fit;
- turning ambiguous reference words into consent;
- adding broader scope/authority than the question and response contain;
- creating a record after Liaison self-delegation language;
- treating schema-valid output as proof that the human actually made that decision.

These guard `E-OWNER-DECISION-PRESENTATION-GAP`, `E-MACHINE-FORM-LEAKAGE`, and `E-LIAISON-AUTHORITY-ESCALATION` while preserving the existing authority model.

## Verification checklist

- [ ] Exact question and presented option set are bound.
- [ ] Selected option maps to exactly one presented canonical option.
- [ ] No omitted option was inferred.
- [ ] Material Owner constraints and qualifications survive normalization.
- [ ] Consequence acknowledgement is not invented.
- [ ] Ambiguity returns clarification without a selected record.
- [ ] Authority delegation cannot become Liaison selection.
- [ ] Unsupported branching conditional choices fail with exact schema limitation.
- [ ] Existing `OWNER_DECISION_RECORD` remains the only decision record contract.
- [ ] Liaison creates no Canon, Control Director, Executor, verification, or promotion authority.

## Minimal verdict format

- Status: RECORDED / CANDIDATE_ONLY / CLARIFICATION_REQUIRED / SCHEMA_LIMITATION / ASSIGNMENT_NOT_ADMISSIBLE
- Question ref
- Options presented
- Selected canonical option, only when exact
- Owner constraints
- Qualifications
- Consequences acknowledged
- Provenance refs
- Durable record ref, only when actually written
- Clarification or exact schema limitation, when applicable
