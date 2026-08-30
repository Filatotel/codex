# Software Workflow — Implementation

**Entry:** an exact software assignment with authority and relevant state.

**Primary role:** `roles/executor/ROLE.md`.

Load by need, not all at once:
- planning: `skills/implementation-planning`;
- bounded execution control: shared `kernel/skills/anti-loop-execution`;
- authority/dependency/exact-state Core only when the assignment needs those decisions;
- technology/QA skills only for the affected surface;
- optional patterns only after their assumptions match.

**Transform:** assignment → bounded plan where needed → implementation → local/technical validation → `EXECUTOR_RESULT`.

**Exit:** work product and Executor Result exist, exact resulting state is known, evidence refs/limitations/deferred findings are recorded. Final acceptance is not self-certified; route to independent verification when required.
