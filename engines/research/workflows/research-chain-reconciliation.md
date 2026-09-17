# Workflow — Research Chain Reconciliation

executing_role: `roles/executor/ROLE.md`
consuming_role: `roles/control-director/ROLE.md`
required_skill: `engines/research/skills/reconcile-research-chain/SKILL.md`

## Entry

Load the Research machine-only constitution, Research manifest, Research control contract, and the required reconciliation skill. This workflow consumes already-existing durable Research outputs; it is not a Research execution workflow.

Exact upstream Research refs are mandatory. Caller prose such as "research is complete" is not evidence.

## Steps

1. Resolve the exact selected upstream Research artifacts and verify identity/provenance.
2. Establish the bounded downstream requirement set.
3. Normalize actual completed/not-completed Research state without changing raw result status.
4. Determine supersession and remove superseded items from active authority/frontier while preserving history.
5. Evaluate evidence sufficiency requirement-by-requirement.
6. Classify every material gap.
7. Detect and record evidence ceilings.
8. Compute satisfied, blocked, acceptable-unknown, deferred, Owner-required, superseded, and out-of-scope requirement states.
9. Derive a bounded next Research candidate frontier only where the skill's continuation law permits it.
10. Emit one durable `RESEARCH_CHAIN_RECONCILIATION` artifact using `engines/research/schemas/research-chain-reconciliation.schema.json`.

## Stop conditions

Fail closed on unresolved exact upstream refs or contradictory artifact identity.

Do not automatically repeat a gap. Do not execute Research. Do not dispatch or spawn a next candidate. Do not create accepted Canon state or call a Canon mutation gate. Owner preference/authority is surfaced to Control / Owner Interface, not converted into Research.

## Admission boundary

`tools.research_policy.admit_work_package()` remains mandatory for actual Research execution. This reconciliation workflow is read-only control interpretation over already-durable Research outputs, so it does not require a Research work-package admission artifact. Any candidate next frontier must return to Control for normal admission before Research execution.

## Durability boundary

The emitted artifact is structurally durable and preserves exact provenance. Independent fresh-agent system-of-record readback required by parent #60 remains deferred until #56 materializes that repository-wide readback boundary.
