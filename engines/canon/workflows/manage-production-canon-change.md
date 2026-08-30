# Workflow: Manage Production-Time Canon Change

**Workflow ID:** `manage_production_canon_change`

Production observations can expose a Canon gap or conflict. They cannot silently become Canon facts.

## Procedure

1. Lock current Canon version, affected production state and observed signal.
2. Run `classify-canon-change`.
3. Record a `CANON_CHANGE_PROPOSAL` with exact impacted Canon IDs/scopes, production dependencies, evidence/observation refs and requested authority.
4. Apply class behavior:
   - **A — ENRICHMENT:** may proceed only when it is demonstrably compatible with protected meaning and within delegated mutation authority; otherwise propose it.
   - **B — CLOSURE:** explicit Canon authority must accept the closure of the known open space.
   - **C — PRODUCTION-REQUIRED CANONICAL CHANGE:** pause affected production, resolve the Canon proposal explicitly, then revalidate dependent production assumptions.
   - **D — CORE CHANGE / RETCON:** controlled stop; require explicit Owner/Canon authority and full downstream impact handling before any mutation.
5. Validate any authorized resulting Canon state.
6. Return the exact changed/unchanged state and downstream revalidation obligations.

## Stop

No class permits mutating Canon merely to match a bug, draft, translation, test, or convenient implementation.