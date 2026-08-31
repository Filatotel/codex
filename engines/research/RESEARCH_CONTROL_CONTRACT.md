# Research Engine Control Contract

## Core separations

`Source != Evidence != Finding != Project Decision`.

Research may establish `SUPPORTED`, `CHALLENGED`, `UNKNOWN`, `CONTRADICTORY`, `INSUFFICIENT_EVIDENCE`, `PROXY_ONLY`, or `READY_FOR_OWNER_DECISION`. Only Owner/K0 can establish project acceptance where Owner authority is reserved.

## Default lifecycle

```text
OWNER / CANON INPUT
→ R0 RESEARCH FOUNDATION
→ R-WHAT
→ AUTOMATED VERIFICATION
→ OWNER_SCOPE_GATE (only when project scope authority is needed)
→ R-WHERE
→ AUTOMATED VERIFICATION
→ MACHINE RESEARCH WORK PACKAGES
→ SOURCE / EVIDENCE EXTRACTION
→ FINDINGS
→ AUTOMATED SYNTHESIS / ADVERSARIAL VALIDATION
→ OWNER_RESEARCH_SUFFICIENCY_ADJUDICATION (only when a project choice is genuinely needed)
→ OPTIONAL MACHINE GAP LOOP
→ RESEARCH FREEZE / RELEASE
→ CANON RECONCILIATION PACKAGE
→ CANON ENGINE
```

There is no ordinary transition to participant collection, surveys, interviews, focus groups, native-speaker recruitment, external reviewer approval, expert panels, or human validation.

## Question admission

Every candidate question is validated against `schemas/research-question.schema.json` and `tools/research_policy.py` before activation. Missing machine-executability fields fail closed. A question that requires a non-owner human is `REJECTED_DEFAULT_RESEARCH_ARCHITECTURE`; the engine redesigns the method or records a limitation.

## Work-package admission

Every work package is validated against `schemas/research-work-package.schema.json` and the policy validator before activation. It declares an allowed AI `EXECUTOR_ROLE` and fixes `VERIFIER_ROLE=AI_R_VERIFIER`. `MACHINE_EXECUTABLE=true` and all human dependency flags must be explicit false. Owner gates, if any, must be explicit `OWNER_*` authority terms.

## Verifier contract

Normal Research Engine verification is automated. R-VERIFIER checks scope, provenance, source fit, reproducibility, evidence/finding separation, contradiction handling, overclaim boundaries, freeze integrity, and machine-only compliance. It never repairs and never recruits.

Verification output MUST include:

- `MACHINE_EXECUTABLE: PASS | FAIL`
- `THIRD_PARTY_HUMAN_DEPENDENCY: 0 | >0`
- `OWNER_MANUAL_RESEARCH_DEPENDENCY: 0 | >0`
- `EXTERNAL_HUMAN_REVIEW_DEPENDENCY: 0 | >0`
- `HUMAN_COLLECTION_PATH: 0 | >0`
- `AMBIGUOUS_HUMAN_GATE_TERMINOLOGY: 0 | >0`

Any prohibited value above zero is `STATUS = FAIL`.

## Repair contract

R-REPAIR repairs only a bounded verifier finding. Human-dependent methods are replaced, when feasible, by pre-existing datasets, public corpora, deterministic computation, model/ensemble annotation, structural analysis, published literature, official standards, or explicit proxies. If no valid machine method exists, record `UNKNOWN`, `INSUFFICIENT_PUBLIC_EVIDENCE`, or `UNMEASURED_HUMAN_CONSTRUCT`. Never introduce a new human dependency.

## Source provenance

Active provenance classes include `PRIMARY_EXTERNAL_DATA`, `PUBLIC_DATASET`, `CORPUS`, `SCHOLARLY_ANALYSIS`, `DICTIONARY_REFERENCE`, `OFFICIAL_REFERENCE`, `COMMUNITY_ARCHIVE`, `EXTERNAL_PREEXISTING_HUMAN_DATA`, `SOFTWARE_DATASET`, `PROXY`, and `OTHER`.

`LEGACY_HUMAN_TEST` is compatibility-only and requires `PROJECT_GENERATION_PROHIBITED=true`. It cannot be selected as a new default data-generation method.

## Machine experiments and freeze

Default experiments conform to `schemas/machine-experiment.schema.json`; participant/recruitment/consent fields are PROHIBITED. Method freeze conforms to `schemas/research-method-freeze.schema.json` and freezes question, input identity, method/tool versions, prompt/rules, sampling, seed policy, metrics, aggregation, thresholds, limitations, and planned sensitivity analysis before substantive result inspection.

## Gap rule and overclaim guard

Direct human constructs may remain unmeasured. Machine proxies must be labeled as proxies and must not be called human responses, direct listener measurement, direct preference measurement, native-speaker validation, or population validation.

## Separate human-research compatibility boundary

The default engine cannot create or enter a `human-research/` namespace. `tools/research_policy.py::validate_human_research_authorization` requires an exact Owner/K0 authorization object, and `validate_separate_human_work_package` checks exact project/question/namespace equality. This is a separate workstream, not a Research Engine fallback and not a reusable authorization.
