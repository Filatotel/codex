# Software Engine Skill Index

This index is **engine-local**. Load only the smallest skill set for the selected Software workflow. Shared cross-engine skills are referenced from `kernel/skills/`; they are not duplicated here.

## Software procedural skills
- `implementation-planning`
- `systematic-debugging`
- `git-branch-integrity`
- `merge-preview-check`
- `pre-merge-review`
- `design-system-authoring`
- `webapp-dogfood-qa`
- `playwright-dogfood-harness`
- `operational-auditing`
- `docs-assembly`
- `spike-prototyping`
- `laravel-contract-first`
- `security-property-calibration`
- `async-lifetime-ownership`

## Optional Solution Patterns
These are not root rules. Read the selected pattern's assumptions, `Use when`, `Do not use when`, alternatives, trade-offs, and verification before adoption.

- `versioned-signed-state-envelope`
- `immutable-deployment-data-pinning`
- `single-writer-session-reconciliation`
- `stable-semantic-identifiers`
- `legacy-schema-adoption`
- `transactional-semantic-state`
- `server-authoritative-event-journal`
- `post-commit-recovery-cursor`
- `immutable-retry-snapshot`
- `capture-on-get-consume-on-post`
- `plan-revalidate-apply-fence`
- `publication-frontier`
- `read-only-observer-facade`
- `provider-late-binding`
- `presentation-completion-barrier`
- `accessibility-commit-announcement`
- `architectural-dependency-fence`

## Shared Core referenced by Software
`anti-loop-execution`, `authority-mapping`, `dependency-ownership`, `exact-state-verification`, `evidence-and-authority`, and `irreversible-boundary-reasoning` live under `kernel/skills/` and are loaded only when their owned decision process is required.
