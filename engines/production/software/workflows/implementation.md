# Software Workflow — Implementation

**Entry:** an exact software assignment with authority, relevant state, and destination executability proof. `execution_contract.proof_status` must be `PROVEN` for the exact destination/execution mode before the Executor is activated.

**Primary role:** `roles/executor/ROLE.md`.

Load by need, not all at once:
- planning: `skills/implementation-planning`;
- bounded execution control: shared `kernel/skills/anti-loop-execution`;
- authority/dependency/exact-state Core only when the assignment needs those decisions;
- technology/QA skills only for the affected surface and only when their mandatory execution prerequisites are satisfied;
- optional patterns only after both their semantic assumptions and execution prerequisites match.

**Pre-assignment capability derivation:** mandatory actions and evidence gates from this workflow and selected skills contribute concrete capabilities to `REQUIRED_CAPABILITIES`. Examples include repository write access for mutation, `repository_local_checkout` + `shell` + language/package runtime for mandatory local commands, and `interactive_browser` or a fully provisioned `playwright_runtime` when browser evidence is mandatory.

**Transform:** assignment → bounded plan where needed → implementation → declared technical validation through proven execution surfaces → `EXECUTOR_RESULT`.

`local/technical validation` is not an unconditional assumption that every destination has a local machine. The exact validation mode is assignment-specific:

- if acceptance requires local-worktree/runtime evidence, the assignment is admissible only on a destination that proves those local capabilities;
- if remote repository/API evidence fully satisfies the stated claim, a declared remote mode may be used;
- remote evidence must not be used to assert local branch/worktree/runtime facts;
- missing mandatory validation capability before assignment is `ASSIGNMENT_NOT_ADMISSIBLE`, not a planned downstream `BLOCKED`;
- loss of a previously proven capability during execution is `BLOCKED_RUNTIME_DRIFT`.

**Exit:** work product and Executor Result exist, exact resulting state is known, evidence refs/limitations/deferred findings are recorded. Final acceptance is not self-certified; route to independent verification when required, and preflight the verifier destination against its own mandatory evidence paths before assigning verification.
