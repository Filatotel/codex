# PR-MIG-02 Canon Source Rewrite Notes

Source: `Filatotel/new-book-skills@ed29f77cf94b7ce3f6e12a66ab8a60268adca660`.

Substantive rewrites were intentionally bounded to Canon-owned knowledge:

- `ENGINE.md` / `MANIFEST.yaml`: extract Canon truth lifecycle from the historical all-in-one literary library and state explicit non-ownership boundaries.
- `docs/CANON_AUTHORITY.md`: rewrite `protocols/CANON_PROTOCOL.md` to project-neutral Canon while preserving explicit-over-inferred authority, implementation/translation not law, unknown ≠ ambiguity, scoped freeze and no implicit conflict winner.
- `docs/CANON_FOUNDATION_MODEL.md`: rewrite `docs/SEED_CANON_MODEL.md`; retain protected values, provenance, stable identity, assumptions/unknowns/ambiguities/contradictions while removing mandatory literary registries.
- `skills/establish-canon-foundation`: consolidate source `seed-extraction` + `canon-initialization`; remove synopsis/story assumptions and make Owner authority explicit.
- `skills/register-canon-fact`: adapt `fact-registry` to project-neutral factual Canon.
- `skills/register-unknown` + `skills/register-ambiguity`: split source `ambiguity-ledger` so undecided state cannot be promoted to protected ambiguity.
- `skills/register-contradiction` + `skills/validate-canon`: adapt source `contradiction-audit`, `canon-acceptance-tests`, and `canon-validator`; internal validation explicitly does not grant independent Verification authority.
- `skills/freeze-canon`: adapt source `canon-freeze` to maturity-specific semantics. Foundation 0.x may freeze explicit unknowns as unknowns; Canon 1.0 requires Research reconciliation; Canon 2.0 requires final reconciliation.
- `skills/classify-canon-change`: uses the frozen Project Resolver Canon A/B/C/D production-time model. The source generic A–E `CHANGE_PROTOCOL` is preserved for future common-protocol extraction but is not Canon law.
- `skills/reconcile-research-into-canon`: materializes the Project Resolver Research boundary absent from the historical direct Seed→frozen-Canon orchestrator.
- `skills/reopen-canon`: materializes explicit post-freeze/post-2.0 lineage control required by the accepted lifecycle.
- `schemas/canon-foundation.schema.json`, `schemas/canon-state.schema.json`, and templates: preserve source state-bearing artifact practice but remove literary-only universal ontology.

No narrative, translation, interactive-runtime, proof/release, generic toolchain, or future engine is implemented by these rewrites. Their exact disposition remains in `CANON_ENGINE_MIGRATION_MAP.md`.