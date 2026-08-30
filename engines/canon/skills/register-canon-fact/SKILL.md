---
name: register-canon-fact
description: Register atomic scoped Canon fact proposals or authorized facts with stable identity, provenance and explicit authority.
---

Adapted from source `fact-registry`.

## Procedure

1. Split compound statements into propositions that can change independently.
2. Classify support: supplied fact, explicit accepted decision, reconciled finding proposal, or inference.
3. Reuse existing semantic identity when the proposition already exists.
4. Record stable ID, statement, scope, provenance, dependencies and authority ref.
5. Default unsupported/inferential additions to `PROPOSED`.
6. Set `ACCEPTED`/`FROZEN` only when the active workflow has explicit authority for that transition.
7. Surface overlaps/conflicts; never choose a winner silently.

## Failure rules

Do not accept a Research finding, implementation observation, translation choice or test behavior merely because it exists. Do not globalize local/temporal facts.