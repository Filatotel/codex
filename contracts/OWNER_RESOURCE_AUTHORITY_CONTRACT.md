# Owner-Approved Resource Authority Contract

This contract is a bounded semantic extension of `contracts/RESOURCE_GOVERNANCE_CONTRACT.md`. It freezes how the existing `OWNER_DECISION_RECORD` artifact may act as the durable authority source for a `RESOURCE_GRANT` whose `authority_source.authority_type` is `OWNER_APPROVED_RESOURCE_AUTHORITY`.

It introduces no new artifact type, resource runtime, reservation mechanism, autonomy semantics, or Resolver behavior.

## Architectural law

```text
OWNER IDENTITY
!= OWNER RESOURCE AUTHORIZATION
```

```text
OWNER_DECISION_RECORD EXISTS
!= RESOURCE AUTHORITY
```

```text
RESOURCE_GRANT MAY REFERENCE AUTHORITY
BUT MAY NOT CREATE OR REINTERPRET AUTHORITY
```

A resource-authority decision must first be a fully schema-valid `OWNER_DECISION_RECORD` under `schemas/owner-decision-record.schema.json`. Structural validity is necessary but not sufficient. Resource authority exists only when the cross-artifact binding rules below are also proven.

## Canonical conditional vocabulary

The conditional Owner decision class is:

```text
decision_kind = OWNER_APPROVED_RESOURCE_AUTHORITY
```

This reuses the already-frozen Resource Governance authority-source vocabulary instead of inventing a second resource-authority decision family.

The only affirmative canonical Owner selection that grants authority within this decision class is:

```text
selected_option = AUTHORIZE_RESOURCE_AUTHORITY
```

`AUTHORIZE_RESOURCE_AUTHORITY` must be one of the exact `options_presented` on the record. A resource-authority decision may still be a valid durable Owner record when its selected option is rejection, deferment, or another non-affirmative presented choice. Such a record does not authorize resource consumption.

The resource-authority decision class conditionally requires:

```text
produced_by_role = owner-interface
status = RECORDED
authority_role = OWNER_K0
non_transitive = true
```

The `owner-interface` records the Owner's choice. It does not acquire Owner authority by producing the record.

## Structured finite authority binding

An affirmative resource-authority decision must bind the intended grant identity and every authority-bearing grant term needed to prevent Control from widening the Owner's choice after recording it.

The conditional `OWNER_DECISION_RECORD` fields are:

```text
authorized_resource_grant_ref : non-empty string
authorized_scope              : non-empty string
authorized_candidate_ref      : string | null
authorized_route_ref          : string | null
authorized_resource_classes   : non-empty unique RESOURCE_CLASS array
authorized_resource_limits    : non-empty RESOURCE_GRANT limit array
authorized_attempt_limit      : integer >= 1 | null
authorized_valid_until        : date-time string | null
authorized_finalization_policy: RESOURCE_GRANT finalization policy
```

Its common `assignment_id` and `input_state_ref` must be non-null, non-empty strings. Provenance and related-artifact lineage must be non-empty.

These fields freeze the finite resource authority itself. The Owner decision does not need an already-authorized `RESOURCE_GRANT` to exist first. Control may materialize the intended grant after the Owner decision, but only if the resulting grant matches the structured authority exactly. This avoids the invalid circular rule in which an already-authorized grant would be required to prove the authority needed to authorize itself.

`authorized_resource_grant_ref` binds the exact intended `RESOURCE_GRANT.artifact_id`; it is not, by itself, sufficient authority.

## Exact target and context equality

For a grant `G` and Owner decision `D`:

```text
D.authorized_resource_grant_ref == G.artifact_id
D.assignment_id                 == G.assignment_id
D.input_state_ref               == G.input_state_ref
D.authorized_scope              == G.scope.scope_ref
D.authorized_candidate_ref      == G.scope.candidate_ref
D.authorized_route_ref          == G.scope.route_ref
```

`null` candidate or route is an exact binding. It never means "any future candidate/route".

Resource-class equality is set equality because order carries no authority meaning:

```text
set(D.authorized_resource_classes)
==
set(G.scope.resource_classes)
```

Resource-limit equality is semantic equality keyed by:

```text
(resource_class, dimension)
```

Each side must contain at most one limit for a key. For every key, `limit_mode`, `ordinary_limit`, and `finalization_reserve` must be equal. Reordering the array does not change authority; duplicate or competing keys fail closed.

Before Owner binding is considered, the grant itself must satisfy the frozen Resource Governance authority-shape semantics. In particular, every limit resource_class belongs to scope.resource_classes:

```text
{limit.resource_class for limit in G.limits}
⊆
set(G.scope.resource_classes)
```

A declared scope class does not need its own limit entry. The inverse is forbidden: a limit may not introduce a resource class that the grant scope did not declare. A structurally schema-valid grant that violates this invariant cannot establish Owner resource authority, even if the Owner record mirrors the same invalid limit.

The remaining finite terms must match exactly:

```text
D.authorized_attempt_limit       == G.attempt_limit
D.authorized_valid_until         == G.valid_until
D.authorized_finalization_policy == G.finalization_policy
```

For `authorized_finalization_policy.allowed_purposes`, equality is set equality. `protected` must remain `true` as required by the grant schema.

The authority decision therefore binds the grant's finite amount, enforcement modes, protected finalization reserve, allowed finalization purposes, resource classes, attempts, lifetime, assignment, input state, scope, candidate, and route. `RESOURCE_GRANT` envelope fields already fixed by its schema (`produced_by_role`, `issued_by`, and `status`) are not duplicated into the Owner record.

## Cross-artifact authority predicate

For a `RESOURCE_GRANT` `G` to derive authority from an Owner decision `D`, every statement below must be true:

1. `G` is structurally valid under `schemas/resource-grant.schema.json` and satisfies the complete frozen Resource Governance semantic invariants relevant to its authority shape, including unambiguous `(resource_class, dimension)` limit keys and the rule that every `G.limits[*].resource_class` belongs to `G.scope.resource_classes`.
2. `G.authority_source.authority_type == OWNER_APPROVED_RESOURCE_AUTHORITY`.
3. `G.parent_grant_ref == null`; delegated child authority belongs to `PARENT_RESOURCE_GRANT`.
4. `G.authority_source.authority_ref` resolves to exactly one durable artifact `D`.
5. `D` is structurally valid under the current `schemas/owner-decision-record.schema.json`; reduced fixtures or prose-only substitutes are not authority.
6. `D.artifact_type == OWNER_DECISION_RECORD`.
7. `D.produced_by_role == owner-interface`.
8. `D.status == RECORDED`.
9. `D.authority_role == OWNER_K0`.
10. `D.decision_kind == OWNER_APPROVED_RESOURCE_AUTHORITY`.
11. `D.selected_option == AUTHORIZE_RESOURCE_AUTHORITY`, and that exact option is present in `D.options_presented`.
12. `D.non_transitive == true`.
13. `D.authorized_resource_grant_ref == G.artifact_id`.
14. `D.assignment_id == G.assignment_id`.
15. `D.input_state_ref == G.input_state_ref`.
16. `D.authorized_scope == G.scope.scope_ref`.
17. `D.authorized_candidate_ref == G.scope.candidate_ref`.
18. `D.authorized_route_ref == G.scope.route_ref`.
19. `D.authorized_resource_classes` equals `G.scope.resource_classes` under the set-equality rule above.
20. `D.authorized_resource_limits` equals `G.limits` under the keyed semantic-equality rule above.
21. `D.authorized_attempt_limit == G.attempt_limit`.
22. `D.authorized_valid_until == G.valid_until`.
23. `D.authorized_finalization_policy` equals `G.finalization_policy` under the rule above.
24. `D.related_artifacts` contains `G.artifact_id`.
25. `G.authority_source.authority_ref == D.artifact_id`.
26. `D.owner_constraints` is empty and `D.qualifications` is absent or empty.

Failure or inability to prove any one of these statements means the Owner-approved resource authority is not established.

## Owner constraints and qualifications

`owner_constraints` and `qualifications` remain faithful records of the Owner's words, not an implementation language for hidden resource authority.

For direct use as `OWNER_APPROVED_RESOURCE_AUTHORITY`, `owner_constraints` MUST be empty and `qualifications` MUST be absent or empty. This is intentionally strict and mechanically checkable. A qualified or conditional Owner answer remains a valid durable `OWNER_DECISION_RECORD`, but it is not sufficient direct resource authority because RG-04 must not parse free-form prose to decide whether a condition has been satisfied.

If the Owner wants a bounded condition to affect authority, the condition must first resolve into an unqualified current decision whose structured resource-authority fields express the resulting finite authority. If that cannot be represented faithfully, the authority remains unresolved and the bounded contract-gap path applies.

Provenance text, consequence prose, question wording, or generic strings must never be parsed to manufacture missing resource authority.

## Fail-closed semantics

The following never constitute Owner-approved resource authority:

- an unresolved, fake, ambiguous, or non-unique `authority_ref`;
- a schema-invalid or partial Owner decision object;
- an Owner record produced by another role;
- a non-`RECORDED` Owner record;
- a record without `OWNER_K0` authority role;
- an unrelated Owner decision, including Canon, deployment, architecture, human-research, or another resource grant;
- a resource decision whose selected option is not `AUTHORIZE_RESOURCE_AUTHORITY`;
- a decision targeting another resource grant;
- assignment or input-state mismatch;
- scope, candidate, or route mismatch, including `null` versus non-`null` mismatch;
- a grant limit whose `resource_class` is not declared by `scope.resource_classes`;
- resource-class, finite-limit, attempt-limit, validity, or finalization-policy mismatch;
- duplicate/ambiguous limit keys;
- missing structured resource-authority binding;
- any non-empty `owner_constraints` or `qualifications` on the direct authority record;
- provenance/question/consequence text that merely claims Owner approval;
- a `RESOURCE_GRANT` referring to itself as authority.

`RESOURCE_GRANT` is never permitted to satisfy the `OWNER_DECISION_RECORD` side of this predicate. A grant may cite authority but may not bootstrap that authority from its own existence, status, provenance, or fields.

## Non-transitivity and parent grants

An Owner decision of this class authorizes only its exact `authorized_resource_grant_ref` with exactly the structured finite authority recorded above. It is non-transitive.

Delegated child resource authority must continue to use the already-frozen `PARENT_RESOURCE_GRANT` authority-source family and satisfy the Resource Governance parent/child monotonicity laws. A child grant must not reuse the root Owner decision as if the Owner had independently authorized the child.

## Compatibility

This is a conditional specialization of the existing `OWNER_DECISION_RECORD` schema. It does not make every Owner decision a resource decision.

Existing non-resource Owner decision records remain valid under their existing rules. Canon, human-research, deployment, architecture, and other Owner decision flows do not gain resource authority merely because they are valid Owner records.

No prose field, provenance string, generic `question_ref`, generic `authorized_scope`, or artifact existence by itself may be reinterpreted as resource authority.

## Downstream ownership

RG-04 and later Resource Admission work may consume and validate this frozen predicate. They do not own it and must not weaken, rename, or reinterpret it.

This contract does not implement:

- `tools/resource_admission.py`;
- `tools/resolver_spawn.py`;
- resource reservation or spending;
- estimator or ledger behavior;
- provider execution;
- PAC, TICKET, or autonomy envelopes.

If a downstream validator cannot prove the predicate from exact durable artifacts, it must return a non-admissible/fail-closed result under the Resource Governance contract rather than infer Owner authorization.
