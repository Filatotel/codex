---
name: classify-canon-change
description: Classify a production-time Canon change as A Enrichment, B Closure, C Production-required Canonical Change, or D Core Change/Retcon and emit the required gate.
---

# Classes

- `A_ENRICHMENT`: compatible detail; no protected semantic change and no closure of an explicit open decision.
- `B_CLOSURE`: resolves an explicit unknown/open decision within already authorized scope.
- `C_PRODUCTION_REQUIRED_CANONICAL_CHANGE`: coherent production requires changing accepted Canon.
- `D_CORE_CHANGE_RETCON`: changes/contradicts protected/core Canon or project identity.

# Procedure

1. Lock exact Canon state and production observation.
2. Identify affected Canon IDs/protected values and downstream dependencies.
3. Determine the weakest class that fully describes semantic impact; never downgrade to avoid a gate.
4. Emit class, rationale, evidence/observation refs, affected scope, required authority and revalidation obligations.
5. C pauses affected production pending explicit Canon resolution. D triggers controlled stop and explicit Owner/Canon authority.

# Boundary

This Canon-specific A-D model supersedes the source repository's generic change A-E taxonomy for this engine.