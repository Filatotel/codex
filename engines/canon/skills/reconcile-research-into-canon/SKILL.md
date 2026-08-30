---
name: reconcile-research-into-canon
description: Compare evidence-backed Research findings with exact current Canon and emit explicit proposed dispositions without automatically mutating Canon.
---

# Inputs

Exact current Canon, exact Research release/findings, provenance, reconciliation scope, authority boundary.

# Procedure

1. Verify Research outputs distinguish source/evidence/finding and identify claim scope.
2. For each relevant finding, compare it to current facts, assumptions, unknowns, ambiguities, contradictions and decisions.
3. Assign one explicit disposition: `ACCEPT_ADD_PROPOSAL`, `REJECT_PROPOSAL`, `RETAIN`, `SUPERSEDE_PROPOSAL`, `CLOSE_UNKNOWN_PROPOSAL`, `RETAIN_UNKNOWN`, `PRESERVE_AMBIGUITY`, `REGISTER_CONTRADICTION`, `REQUIRE_OWNER_DECISION`, or `DEFER_OUT_OF_SCOPE`.
4. State exactly what evidence supports the disposition and what it does not prove.
5. Emit `CANON_RECONCILIATION_RESULT` and bounded `CANON_CHANGE_PROPOSAL` artifacts.
6. Do not apply acceptance unless explicit Canon authority is present.

# Invariant

Research authority determines what evidence supports; Canon authority determines what the project accepts.