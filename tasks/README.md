# Temporary manual task packets

## Purpose

This directory is a temporary manual control-plane staging area for bounded implementation assignments used while the Project Resolver is not yet able to materialize its own executable task packets.

```text
MANUAL TASK FILE
!=
MATERIALIZED RESOLVER FEATURE
```

These files are operational planning artifacts only. They do not create authority, do not replace GitHub issues, and do not become project Canon merely by existing in the repository.

## Lifecycle

Use this directory for upcoming bounded tasks that are already designed but are not yet ready to execute against an exact frozen repository state.

Recommended states:

- `STAGED` — scope is designed, but predecessor gates are not yet satisfied.
- `READY_TO_FREEZE` — predecessor gates are satisfied and the task can be materialized on a work branch.
- `FROZEN` — copied/materialized on the execution branch at an exact task commit; the executor must not edit it.
- `EXECUTED` — implementation exists and awaits or has passed independent verification.
- `OBSOLETE` — superseded before execution; do not reuse silently.

A staged task must not pretend that its current repository SHA is the future execution basis.

Before execution:

1. verify the predecessor gate;
2. verify current authoritative `main`;
3. create the bounded work branch from that exact `main`;
4. materialize/freeze the task file on that branch;
5. record the exact task commit;
6. execute without editing the frozen task packet.

## #56 sequence

The already-frozen first packet remains at:

`docs/tasks/TASK-56-A1.md`

Do not move, rewrite, or duplicate it merely for directory consistency. Its existing path and blob are part of its execution provenance.

The staged follow-up sequence is:

```text
56-A1
required durable-output declaration + reference completeness
        ↓
56-B
provider-neutral durable system-of-record port + independent readback primitive
        ↓
56-C
materialization/readback enforcement in result, verification, and transition flow
        ↓
56-D
fresh independent consumer / predecessor-local-state elimination conformance
        ↓
#56 closure candidate
```

Each task is conditional on the previous task being independently verified and merged.

## Scope discipline

Do not pre-implement future tasks from an earlier task.

If a later task reveals an upstream contract gap:

```text
STOP
→ report exact gap
→ repair upstream separately
→ refreeze downstream task
```

Do not silently broaden a task file after observing implementation difficulty.

## Cleanup

This directory is intentionally temporary.

After the PAC-readiness closing program has durable repository-native task materialization or another authoritative replacement, remove these manual staging files in one explicit cleanup change.

Deletion of this directory must not delete or rewrite historical Git commits that contain the frozen packets used for executed workstreams.
