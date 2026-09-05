# Canon Authority

This document is the Project Resolver adaptation of authoritative Canon semantics preserved from `Filatotel/new-book-skills@ed29f77cf94b7ce3f6e12a66ab8a60268adca660`, especially `protocols/CANON_PROTOCOL.md`, `docs/SEED_CANON_MODEL.md`, and the migrated Canon skills.

## Definition

Canon is an **explicit governed project declaration** that downstream work must preserve until it is explicitly superseded through authorized change.

A proposition is not Canon merely because it appears in research notes, evidence, a finding, implementation, source code, prose, translation, test, fixture, report, or remembered/chat intent. Those surfaces may provide information or evidence. They do not silently create authority.

## Item authority states

Canon records may use:

- `PROPOSED` — candidate state; not downstream authority;
- `ACCEPTED` — explicitly accepted within stated authority/scope;
- `FROZEN` — accepted and protected against incidental mutation for a declared lifecycle scope;
- `SUPERSEDED` — retained as history/provenance, no longer current authority.

These item states are distinct from Canon maturity/version (`0.x`, `1.0`, `2.0`).

## Core rules

1. **Explicit beats inferred.** Plausibility, implementation convenience, or repeated wording does not grant acceptance.
2. **Upstream authority beats downstream realization.** Production may expose a Canon defect or gap; it may not repair Canon silently.
3. **Implementation fact is not Canonical fact.** Runtime/software behavior may trigger a proposal but cannot make itself law.
4. **Research evidence/finding is not an accepted project decision.** Findings enter Canon through reconciliation plus explicit Canon authority.
5. **Translation is realization.** Language-specific solutions do not automatically mutate source Canon.
6. **Validation derives from authority.** A validator/test can show inconsistency; passing cannot grant Owner acceptance.
7. **Scope is part of meaning.** Apparently opposite declarations can coexist when their time, audience, condition, or scope differs.
8. **Equal-authority conflict has no implicit winner.** Do not resolve by last-read/newest/convenient carrier; register the smallest conflict and gate mutation.

## Facts, assumptions, unknowns, ambiguity, contradictions

### Fact

A Canon fact is an accepted proposition supported by declared authority/provenance. An inference remains proposed until accepted.

### Assumption

An assumption is an explicitly tracked proposition the project is temporarily relying on **as an assumption**, not as established truth. Accepting an assumption record means accepting its use/status, not asserting factual certainty.

### Unknown

An unknown records a question/state the project has not resolved. Canon Foundation 0.x may freeze with explicit unknowns. Freezing an unknown means preserving that it is unknown; it does not turn the missing answer into truth.

### Intended ambiguity

Intended ambiguity is a positive protected decision not to collapse a distinction or reading within a stated scope. It requires explicit authority and preservation requirements. Creator/project indecision is not intended ambiguity.

### Contradiction

A contradiction record describes incompatible or apparently incompatible claims and their scope/status. Blocking accepted conflicts cannot be auto-fixed by the Canon Engine; they require controlled authority/change handling. Intentional tension or scoped apparent conflict may be nonblocking when explicitly declared.

## Canon registries

Canon may maintain stable registries required by a project, but core Canon defines no mandatory literary/product ontology. Characters, motifs, reveals, objects, chapters, APIs, legal sections, stakeholders, or other domain entities are project/domain schemas or optional patterns. The universal Canon requirement is only that canonical identities are stable, scoped, provenance-bearing, and governed by explicit authority.

## Freeze semantics by maturity

### Foundation 0.x freeze

A 0.x freeze establishes a stable Research-entry authority boundary. It may include explicit assumptions, unknowns, contradictions awaiting Research, and protected ambiguity. It must not present those as fully researched truth.

Required minimum:

- Owner-authorized scope/protected values are explicit;
- known facts vs assumptions vs unknowns are distinguishable;
- known blocking ambiguity/contradiction is visible;
- stable identity/provenance exist;
- the freeze record states what remains unresolved and what Research is expected to reduce.

### Canon 1.0 freeze

A 1.0 freeze follows Research and explicit reconciliation. It requires current reconciliation state, authority disposition of accepted claims, and no unresolved blocker inside the production-authorizing scope unless the unresolved condition is explicitly accepted as protected ambiguity or expressly out of scope.

### Canon 2.0 freeze

A 2.0 freeze follows final production-era reconciliation. It records all accepted production-time Canon changes and remaining explicit decisions/ambiguities. Post-2.0 change cannot be an ordinary silent edit.

## Reopen rule

A frozen Canon scope may reopen only under explicit authority and a new state/version lineage. After Canon 2.0, the change must declare one of:

- `ADDENDUM`
- `EXPANSION`
- `NEW_EDITION`
- `REOPEN`

No mode authorizes retroactive mutation without provenance or impact handling.
