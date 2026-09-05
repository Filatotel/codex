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
5. Emit envelope-compatible `CANON_RECONCILIATION_RESULT` and bounded `CANON_CHANGE_PROPOSAL` artifacts.
6. Do not apply acceptance unless explicit Canon authority is present.

# Invariant

Research authority determines what evidence supports; Canon authority determines what the project accepts. Research output never mutates Canon automatically.

## Execution contract

**Required execution capabilities for mandatory steps:**
- `durable_artifact_write`

**Supported execution modes:** assignment-bound reconciliation over exact supplied/current Canon and Research artifacts.

**Conditional / optional capabilities:** none by default. Research execution, source collection, network, repository, browser, or shell access are not implied by this skill.

**Mandatory evidence path:** emit common-envelope reconciliation and any change-proposal artifacts with exact Canon/Research refs and mutation-authority state.

If required upstream artifacts are unresolved, the workflow is not executable. If the destination lacks mandatory output capability, return `ASSIGNMENT_NOT_ADMISSIBLE`.
