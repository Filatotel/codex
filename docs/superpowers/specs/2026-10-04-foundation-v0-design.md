# Foundation V0 project formation design

Date: 2026-10-04
Status: design freeze candidate
Issue owner: #53
Baseline: `main` at `65476b45d420d025506fa87b6c41ddb380ce698e` after Liaison cognitive base merge (#97).

## 1. Purpose

Materialize the currently planned but unavailable `foundation` Engine as the governed project-formation layer between Liaison cognitive intake and Canon.

Foundation V0 exists for the case where an Owner has more than an ordinary question but less than an already-governed project truth: a raw idea, early concept, partially understood project, or project-formation conversation that should become durable working state without silently becoming Canon.

The target path is:

```text
OWNER RAW IDEA
→ Liaison (#54)
  owner-intent-sensemaking
  project-context-orientation
→ ROUTE
→ Foundation Engine (#53)
→ form_project_foundation
   ├─ develop-project-seed
   ├─ define-project-outcome
   ├─ classify-consequential-unknowns
   └─ design-discovery [only when materially useful]
→ PROJECT_SEED
→ PROJECT_OUTCOME
→ CONSEQUENTIAL_UNKNOWN_MAP
→ FOUNDATION_READY_FOR_OWNER_GATE
→ STOP
```

Foundation V0 does not accept Canon, mutate Canon, start Research automatically, start Production, or decide on behalf of Owner.

## 2. Architectural position

The semantic boundaries are:

```text
NATIVE LLM REASONING
→ Liaison cognitive intake
→ Foundation project formation
→ Owner Foundation Gate [later wave]
→ Canon Engine
→ governed Canon Foundation 0.x
```

Required distinctions:

```text
RAW OWNER IDEA
!= PROJECT_SEED
!= CANON

FOUNDATION WORKING STATE
!= OWNER-ACCEPTED PROJECT TRUTH

MODEL PROPOSAL
!= OWNER INTENT

DURABLE
!= AUTHORITATIVE
```

The Foundation Engine is therefore not a weaker Canon Engine and not a second Liaison. It owns durable non-authoritative project-formation state.

The Canon Engine remains the sole owner of governed Canon truth lifecycle. The Liaison remains the human-facing cognitive intake and Owner projection role.

## 3. Why an Engine rather than Liaison-only skills

The Liaison cognitive base added by #97 answers:

```text
RAW OWNER REQUEST
→ RESPOND_IN_PLACE | CLARIFY | ROUTE
```

It intentionally does not own durable project formation.

When `ROUTE` is selected because a raw idea is intended to become a project, the work needs a semantic owner with explicit outputs, workflow composition, durable artifact rules, Router capability ownership, and execution/admissibility semantics. That owner is Foundation.

Keeping project formation only inside Liaison would collapse two different responsibilities:

- understanding what the Owner is asking;
- building durable but still non-authoritative project working state.

Foundation V0 preserves that boundary while still allowing the same physical ChatGPT conversation to perform Liaison and Foundation as separate logical phases.

## 4. V0 scope

Foundation V0 materializes exactly one Engine workflow:

```text
form_project_foundation
```

It composes four cognitive skills:

1. `develop-project-seed` — required;
2. `define-project-outcome` — required;
3. `classify-consequential-unknowns` — required;
4. `design-discovery` — optional and loaded only when problem/solution exploration materially improves the working foundation.

The workflow produces exactly three Foundation-owned durable artifact types:

```text
PROJECT_SEED
PROJECT_OUTCOME
CONSEQUENTIAL_UNKNOWN_MAP
```

`FOUNDATION_READY_FOR_OWNER_GATE` is a workflow/result status, not a fourth durable artifact type.

## 5. Engine registration

`SYSTEM_MANIFEST.yaml` currently declares:

```yaml
planned_engines:
  - engine_id: foundation
    status: not_materialized
```

Foundation V0 moves `foundation` into `engine_registry` with `status: available` and the minimum semantic capability:

```text
form_project_foundation
```

V0 should not expose every internal cognitive skill as a separate root capability unless a concrete routing need appears later. The Router selects project formation; the Foundation manifest owns composition of its internal skills.

This keeps the root routing vocabulary smaller than the skill library.

## 6. Foundation manifest contract

Create:

```text
engines/foundation/MANIFEST.yaml
```

The manifest owns:

- raw-to-working project formation after Liaison routes into governed project formation;
- working project seed creation/refinement;
- requested outcome definition;
- consequential unknown classification;
- optional bounded design discovery before Canon;
- production of the three non-authoritative durable Foundation artifacts.

It does not own:

- Owner/K0 authority;
- Liaison intent interpretation before route selection;
- accepted Canon truth;
- Canon mutation/freeze/reopen;
- substantive external Research;
- evidence collection for external factual claims;
- Production planning or implementation;
- independent Verification;
- generic routing/orchestration;
- physical SBC/PAK/provider transport.

Suggested V0 inputs:

- exact Owner request / supplied project material preserved as provenance;
- Liaison bounded routing frame;
- relevant pre-existing project state when one exists;
- exact assignment;
- destination capability profile and assignment admissibility where required by the generic execution chain.

Suggested V0 outputs:

- `PROJECT_SEED`;
- `PROJECT_OUTCOME`;
- `CONSEQUENTIAL_UNKNOWN_MAP`;
- ordinary `executor_result` / workflow result with terminal status or blocker.

The manifest should reuse existing shared execution roles instead of creating a Foundation persona. The executing role is `roles/executor/ROLE.md`; the consuming/control role remains `roles/control-director/ROLE.md` where governed control is active.

In manual V0 the same physical ChatGPT chat may perform the logical role transition, consistent with the Liaison contract:

```text
Liaison
→ Foundation workflow / Executor logical phase
→ Foundation result
→ Liaison projection
→ Owner
```

Same physical chat does not imply same semantic role or authority.

## 7. Workflow contract

Create one workflow:

```text
engines/foundation/workflows/form-project-foundation.md
```

The workflow should be iterative in reasoning but bounded in durable outputs.

Conceptual procedure:

```text
1. consume the Liaison routing frame and exact supplied Owner material
2. develop a useful PROJECT_SEED working interpretation
3. establish PROJECT_OUTCOME sufficiently for the current formation stage
4. identify consequential unresolved items
5. use design-discovery only if exploration is needed to make seed/outcome coherent
6. classify unresolved items into CONSEQUENTIAL_UNKNOWN_MAP
7. reconcile the three artifacts for contradictions and provenance loss
8. if materially sufficient for an Owner Foundation Gate:
      return FOUNDATION_READY_FOR_OWNER_GATE
   else:
      return the smallest bounded clarification/blocker needed
9. stop; do not invoke Canon acceptance, Research execution, or Production
```

The workflow may iterate internally among the four skills. It must not create a procedural interrogation loop with the Owner.

The workflow should prefer a reasonable working interpretation the Owner can correct over asking for exhaustive formalization.

## 8. Cognitive skill design law

Foundation skills guide an intelligent LLM; they do not replace model intelligence with a deterministic questionnaire.

Each Foundation cognitive skill should separate:

### Thinking guidance

Use judgment-oriented language such as:

- consider;
- look for;
- compare;
- infer cautiously;
- propose;
- reframe;
- simplify;
- test coherence;
- ask when material.

### Hard invariants

Use strict requirements only for real authority/evidence boundaries, including:

- do not invent Owner intent;
- do not silently promote a proposal or working interpretation into Canon;
- do not claim external factual/feasibility evidence that was not obtained;
- do not automatically start Research because an unknown exists;
- do not freeze architecture merely because one plausible implementation was proposed;
- do not turn a working Foundation artifact into Owner/K0 authority;
- preserve explicit Owner constraints and disagreement.

The skills must not require a fixed questionnaire or arbitrary completeness score.

## 9. Skill: `develop-project-seed`

Create:

```text
engines/foundation/skills/develop-project-seed/SKILL.md
```

Purpose: turn a raw idea or incomplete project concept into a coherent working interpretation that is useful enough to reason about and correct.

The skill should use native model reasoning aggressively and look for, when material:

- underlying objective;
- intended user/beneficiary/value;
- protected Owner intent;
- hard constraints;
- non-goals;
- explicitly known decisions;
- obvious contradictions;
- hidden assumptions;
- important missing decisions;
- project identity candidate or useful working name where available.

It should separate:

```text
EXPLICIT OWNER STATEMENT
STRONGLY IMPLIED CONTEXT
MODEL WORKING INTERPRETATION
MODEL PROPOSAL
UNRESOLVED MATERIAL QUESTION
```

The artifact must not erase those distinctions.

The preferred interaction style is:

```text
"I understand the project approximately as ..."
```

followed by correction when needed, rather than an exhaustive form.

## 10. Skill: `define-project-outcome`

Create:

```text
engines/foundation/skills/define-project-outcome/SKILL.md
```

Purpose: establish what the Owner actually wants to exist when the current project is complete, before Research or Production is planned.

It should reason about:

- target outcome;
- completion condition;
- required deliverables;
- optional deliverables when already relevant;
- intended audience/user where material;
- non-goals;
- whether downstream realization is required at all.

It must not assume that every project ends in software or Production.

Valid outcomes may include:

- a concept/Canon itself;
- an evidence-backed plan;
- research result;
- document/presentation;
- website;
- software product;
- operating process;
- multi-deliverable program.

The output remains working Foundation state until later Owner/Canon acceptance.

## 11. Skill: `classify-consequential-unknowns`

Create:

```text
engines/foundation/skills/classify-consequential-unknowns/SKILL.md
```

Purpose: keep unresolved uncertainty explicit and decide what kind of uncertainty it is without automatically resolving it.

V0 classification vocabulary:

```text
OWNER_PREFERENCE
EXTERNAL_FACT
FEASIBILITY
ARCHITECTURE_DECISION
IMPLEMENTATION_DEPENDENT
NICE_TO_KNOW
```

Interpretation:

- `OWNER_PREFERENCE`: belongs to Owner; Research cannot answer it for them;
- `EXTERNAL_FACT`: may later become a Research candidate if consequential;
- `FEASIBILITY`: may later require evidence/prototype/research;
- `ARCHITECTURE_DECISION`: may require exploration/evidence and later authority, but is not automatically Canon;
- `IMPLEMENTATION_DEPENDENT`: defer until the relevant implementation context exists;
- `NICE_TO_KNOW`: keep off the critical path unless its consequence changes.

Classification itself does not dispatch Research, create an Owner decision record, or authorize architecture.

Unknowns that are not consequential for the declared outcome need not be materialized merely for completeness.

## 12. Skill: `design-discovery`

Create:

```text
engines/foundation/skills/design-discovery/SKILL.md
```

Purpose: help the Owner and model explore problem/solution space before Canon without prematurely freezing architecture.

It may:

- propose alternative interpretations;
- compare solution shapes;
- simplify scope;
- expose contradictions;
- test whether a proposed feature actually serves the outcome;
- propose different project boundaries;
- surface trade-offs;
- identify assumptions that should remain open.

It must remain optional. The workflow should not load it for a straightforward project seed just because the skill exists.

V0 creates no separate `DESIGN_DISCOVERY_RESULT` durable artifact. Materially useful discovery is folded into the current working seed/outcome/unknown map while preserving proposal versus Owner-statement provenance.

## 13. Artifact model

Foundation artifacts are durable working state, not semantic authority.

They should use the repository's existing common durable artifact envelope where applicable rather than create a parallel envelope.

### `PROJECT_SEED`

Create schema:

```text
engines/foundation/schemas/project-seed.schema.json
```

Required semantic payload should stay small. At minimum it needs:

- `artifact_type: PROJECT_SEED`;
- working interpretation / project summary;
- explicit non-authoritative status;
- preservation of material Owner constraints/protected intent when supplied;
- unresolved material questions or clear references to the unknown map;
- provenance through the common envelope.

Dimensions such as intended users, constraints, non-goals, known decisions, assumptions, and project identity candidate should be optional/bounded rather than mandatory empty form fields.

### `PROJECT_OUTCOME`

Create schema:

```text
engines/foundation/schemas/project-outcome.schema.json
```

At minimum:

- `artifact_type: PROJECT_OUTCOME`;
- working target outcome;
- completion condition or explicit unresolved completion condition;
- required deliverables known at this stage;
- optional deliverables only when meaningful;
- relevant audience/user and non-goals when material;
- explicit non-authoritative status;
- provenance through the common envelope.

### `CONSEQUENTIAL_UNKNOWN_MAP`

Create schema:

```text
engines/foundation/schemas/consequential-unknown-map.schema.json
```

Each materialized item should include at least:

- stable bounded item identity within the artifact;
- unknown/question statement;
- one V0 classification;
- why it matters / downstream consequence;
- current state such as open or deferred.

The map does not need to contain every unknown thought. It contains unknowns consequential to current project formation/outcome.

The schema must not encode automatic Research dispatch authority.

## 14. Non-authority law

Foundation durability exists so project formation can survive across chats and later stages. Durability must not be confused with authority.

Required law:

```text
PROJECT_SEED.authoritative = false
PROJECT_OUTCOME.authoritative = false
CONSEQUENTIAL_UNKNOWN_MAP.authoritative = false
```

Exact schema expression may use a status/authority field consistent with repository conventions, but V0 must make the non-authoritative nature machine-checkable rather than relying only on prose.

No Foundation artifact may satisfy a Canon mutation authority requirement merely because it is durable or produced by a valid assignment.

A later Owner Foundation Gate may authorize selected Foundation meaning to enter Canon. That gate is outside this V0 implementation wave.

## 15. Clarification policy

The Liaison and Foundation layers share the same cognitive principle:

```text
ASK ONLY WHEN DIFFERENT PLAUSIBLE ANSWERS
WOULD MATERIALLY CHANGE
THE PROJECT, ROUTE, AUTHORITY, OUTPUT, OR NEXT ACTION.
```

Foundation V0 has no mandatory minimum question count.

Zero clarification questions is valid when the supplied request/material is already sufficient to produce useful working Foundation state.

This resolves the older bootstrap guidance that mentioned an adaptive `3–20` question range: that range must not be interpreted as a protocol requirement or minimum. The newer Liaison/Foundation cognitive law governs V0 behavior.

Questions should be one bounded material question at a time when interaction is required. The model may instead state a working interpretation and allow Owner correction when that is safer and more efficient.

## 16. External facts and Research boundary

Foundation may use ordinary model knowledge for ideation and explanation, but it must distinguish general reasoning from evidence-backed external project facts.

If project formation depends on a factual or feasibility claim that requires current/external verification, Foundation classifies the uncertainty but does not silently treat model memory as evidence.

Required chain after this V0 wave remains conceptually:

```text
CONSEQUENTIAL_UNKNOWN_MAP
→ later Research admission/planning where justified
→ evidence/findings
→ later Canon reconciliation / Owner authority
```

Foundation V0 stops before Research dispatch.

## 17. Canon boundary

The existing Canon Engine already owns:

- `CANON_FOUNDATION`;
- Canon state registration;
- Canon change/reconciliation;
- validation;
- freeze/reopen.

Foundation V0 must not duplicate those artifacts or skills.

The Foundation workflow ends at:

```text
FOUNDATION_READY_FOR_OWNER_GATE
```

not:

```text
CANON_FOUNDATION_CREATED
```

A later separate #53 wave will define the exact Owner Foundation Gate and handoff from accepted Foundation meaning into the existing `establish_canon_foundation` Canon workflow.

Until that later wave exists, `FOUNDATION_READY_FOR_OWNER_GATE` is an explicit stop boundary.

## 18. Router changes

`ROUTER.md` currently has a non-materialized Foundation gate. Foundation V0 replaces only the Foundation part of that behavior.

Add a route for:

```text
form_project_foundation → foundation
```

Routing behavior:

1. Liaison must already have selected `ROUTE` because governed project formation is intended.
2. Router selects Foundation by semantic capability/authority boundary.
3. Load only `engines/foundation/MANIFEST.yaml`.
4. Select `form_project_foundation`.
5. Load its required skills plus `design-discovery` only if selected by the workflow/assignment.
6. Apply the existing compiler/executability/admissibility chain where an executable assignment is required.
7. Activate the declared role without granting Owner or Canon authority.

The Router must not send a raw project idea directly to Canon merely because `establish_canon_foundation` exists.

The Router must not borrow Software skills to simulate Foundation.

## 19. Progressive disclosure

The #97 loading law remains unchanged:

```text
AWARE
→ INSPECT
→ LOAD
→ APPLY
→ MATERIALIZE
```

For a raw idea:

- `AWARE`: Liaison/root manifest knows Foundation exists;
- `INSPECT`: only after `ROUTE` to project formation, inspect Foundation manifest/workflow;
- `LOAD`: load the three required Foundation skills and optional `design-discovery` only when materially needed;
- `APPLY`: skills guide native reasoning;
- `MATERIALIZE`: write the three working artifacts only under valid assignment/durable-output conditions.

No global skill discovery.

## 20. Error and stop conditions

Foundation V0 should fail or stop explicitly for bounded reasons rather than fabricate project certainty.

Expected classes/conditions include:

- materially ambiguous Owner intent that cannot be preserved faithfully;
- contradiction between supplied Owner constraints that changes the project;
- insufficient information to define even a working outcome;
- external fact/feasibility dependency incorrectly presented as established evidence;
- attempt to treat Foundation output as accepted Canon;
- attempt to auto-dispatch Research from the unknown map;
- attempt to auto-enter Production;
- missing generic execution/durable-write prerequisites when materialization is required.

Where a useful non-authoritative working interpretation is possible, uncertainty should remain explicit instead of becoming a blocker merely because the project is incomplete.

## 21. Structural files expected in the implementation wave

The implementation plan may refine exact test filenames, but the architecture expects approximately:

```text
SYSTEM_MANIFEST.yaml
ROUTER.md
engines/foundation/MANIFEST.yaml
engines/foundation/workflows/form-project-foundation.md
engines/foundation/skills/develop-project-seed/SKILL.md
engines/foundation/skills/define-project-outcome/SKILL.md
engines/foundation/skills/classify-consequential-unknowns/SKILL.md
engines/foundation/skills/design-discovery/SKILL.md
engines/foundation/schemas/project-seed.schema.json
engines/foundation/schemas/project-outcome.schema.json
engines/foundation/schemas/consequential-unknown-map.schema.json
schemas/README.md [only if shared schema index requires it]
tools/validate_structure.py [only enough to register/protect the new Engine surfaces]
tests/... Foundation behavioural/structure/schema/route coverage
```

No unrelated Canon, Research, Software, Verification, SBC, PAK, provider, or resource-governance rewrite belongs in this wave.

## 22. Testing strategy

Implementation must use TDD and prove both semantics and boundaries.

Minimum behavioral cases:

1. raw project idea routed from Liaison reaches Foundation, not Canon or Software;
2. already-sufficient project description may produce Foundation working state with zero forced clarification questions;
3. material ambiguity produces a bounded clarification rather than invented Owner intent;
4. `design-discovery` remains optional, not globally loaded;
5. Foundation outputs are durable but machine-checkably non-authoritative;
6. `PROJECT_SEED`, `PROJECT_OUTCOME`, and `CONSEQUENTIAL_UNKNOWN_MAP` validate against their schemas/common envelope requirements;
7. unknown classification accepts exactly the V0 vocabulary and rejects undeclared classes;
8. `OWNER_PREFERENCE` is not converted into Research work;
9. `EXTERNAL_FACT`/`FEASIBILITY` may be represented as candidates/unknowns but do not dispatch Research;
10. no Foundation output can satisfy Canon mutation/freeze authority by itself;
11. workflow stops at `FOUNDATION_READY_FOR_OWNER_GATE` and does not create `CANON_FOUNDATION`;
12. existing Software/Research/Verification/Canon representative routes remain unchanged;
13. root structural validator recognizes Foundation as a materialized Engine;
14. global skill discovery remains forbidden.

Full repository suite and `tools/validate_structure.py` must pass on the exact PR head/merge ref before merge.

## 23. Acceptance criteria

Foundation V0 is accepted when all of the following are true:

1. `foundation` is `available` in the root engine registry rather than `not_materialized`.
2. Router can select `form_project_foundation` from a Liaison `ROUTE` decision.
3. One Foundation manifest/workflow composes the four approved cognitive skills with `design-discovery` optional.
4. A raw Owner idea can become durable `PROJECT_SEED`, `PROJECT_OUTCOME`, and `CONSEQUENTIAL_UNKNOWN_MAP` without becoming Canon.
5. The three artifacts preserve provenance and explicit non-authority.
6. The model can use native reasoning and working interpretations rather than a fixed intake form.
7. No mandatory minimum number of Owner questions exists.
8. Consequential unknowns are classified without automatic Research dispatch.
9. Foundation stops at `FOUNDATION_READY_FOR_OWNER_GATE`.
10. Canon Engine remains the sole owner of governed Canon Foundation/truth lifecycle.
11. Existing root Router/compiler/executability laws remain in force rather than being duplicated inside Foundation.
12. Existing Engines continue to pass regression coverage.

## 24. Explicit non-goals for this wave

Foundation V0 does not implement:

- Owner Foundation Gate artifact/decision semantics;
- automatic conversion of Foundation artifacts into `CANON_FOUNDATION`;
- Canon carrier creation or migration;
- Research Need Map execution orchestration beyond the bounded unknown classification artifact;
- Research dispatch;
- Production Foundation;
- production implementation;
- project storage-topology provisioning (`DRIVE_ONLY`, `REPO_ONLY`, `DRIVE_THEN_REPO`);
- account/connectors provisioning;
- automation activation gate;
- SBC Browser or PAK transport;
- multi-chat physical session orchestration;
- a new Liaison, Control Director, Executor, or Foundation persona;
- a new common artifact envelope;
- a second Router;
- completion of all remaining #53 lifecycle sections.

These remain later bounded waves under #53 or their existing owning issues.

## 25. Issue alignment and sequencing

This design implements only the first materialization wave under #53.

Current sequence becomes:

```text
#97 MERGED: Liaison Cognitive Base
→ THIS WAVE: Foundation V0
→ NEXT #53 WAVE: Owner Foundation Gate + exact handoff into existing Canon Engine
→ later #53: outcome/research/canon lifecycle extensions as needed
→ #58/#54: manual multi-chat conformance where physical handoff is useful
```

The wave is an architecture addition: it materializes the already-planned `foundation` Engine and does not replace an existing Engine. Therefore the architecture-replacement destructive/preserve Owner gate is not invoked.
