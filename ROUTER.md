# Project Resolver Router

`ROUTER.md` chooses the smallest authoritative and executable work surface. It does not discover the entire repository.

## Routing contract

```text
KERNEL
→ select ENGINE by semantic capability and authority boundary
→ ENGINE selects a declared WORKFLOW
→ classify target authority/movability
→ classify execution-context fact authority
→ bind structured authorized claims and the exact supported execution envelope
→ compile structured assignment semantics under `contracts/ASSIGNMENT_COMPILATION_CONTRACT.md`
→ reject unauthorized identity/responsibility/evidence obligations
→ prove requested obligations are in the supported execution envelope
→ derive authorized mandatory actions + mandatory evidence gates from `COMPILED_ASSIGNMENT`
→ derive REQUIRED_CAPABILITIES only from compiled authority plus selected mandatory workflow/skill prerequisites
→ bind exact destination CAPABILITY_PROFILE
→ prove REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES
→ materialize ASSIGNMENT_ADMISSIBILITY
→ only if ADMISSIBLE: issue ASSIGNMENT
→ WORKFLOW activates a durable ROLE
→ ROLE loads only required SKILLS and referenced artifacts
```

Selection is based on the transformation and authority required, not filename similarity. Semantic engine capability is necessary but never sufficient for assignment.

Compilation is a mandatory upstream semantic gate. `REJECTED` compilation does not proceed to route, capability-profile selection, assignment admissibility, or executable assignment. The router consumes compiler output; it does not replace the deterministic compiler with prose judgment.

The universal executability contract is `contracts/EXECUTABILITY_CONTRACT.md`.

## Destination executability preflight

Before `ASSIGN`, the Control Director/router must compare the exact destination instance against every mandatory operation and evidence path required by the assignment, selected workflow, and selected mandatory skill steps.

Examples of concrete capability IDs include:

- `repository_remote_read`, `repository_remote_write`;
- `repository_local_checkout`, `git_local_worktree`, `shell`;
- `python_runtime`, `node_runtime`, `php_runtime`, `package_install`;
- `interactive_browser`, `playwright_runtime`;
- `database_access`, `deployment_access`, `outbound_network`;
- `ci_trigger`, `ci_read`, `connector:<name>`.

If any mandatory capability is not proven available, do not issue an executable assignment. Return:

```text
ASSIGNMENT_NOT_ADMISSIBLE
assignment_draft: <id>
destination: <destination_id>
required_capabilities: <set>
available_capabilities: <set>
missing_capabilities: <required - available>
mandatory_evidence_paths: <paths>
next: <select another already-authorized executable mode/destination | wait | escalate>
```

Do not intentionally route an impossible assignment to an Executor/Verifier merely so it can return `BLOCKED`. A later `BLOCKED_RUNTIME_DRIFT` remains valid when a capability disappears after a previously valid admissibility proof.

### Execution-mode substitution

A workflow/skill may expose multiple supported modes. The router may choose an alternate mode only when:

1. it remains within the same authority and semantic owner;
2. its declared capability prerequisites are satisfied by the destination;
3. it proves the same mandatory claims/evidence, or the assignment explicitly accepts a weaker claim;
4. the selected mode is recorded in `ASSIGNMENT_ADMISSIBILITY` and the assignment execution contract.

Remote repository state cannot silently substitute for local-worktree assertions. Playwright cannot silently substitute for a missing browser/runtime when Playwright itself requires checkout, Node/package execution, and browser binaries.

### Migration-preserved skills and patterns

An active skill/pattern migrated before the executability contract may not yet contain a dedicated execution-prerequisite section. Missing metadata means **UNKNOWN prerequisites, not zero prerequisites**. When such a legacy item is actually selected, inspect only that selected item's mandatory procedure/evidence steps and derive concrete required capabilities before assignment. If any mandatory prerequisite cannot be derived confidently, return `ASSIGNMENT_NOT_ADMISSIBLE` pending bounded clarification/annotation. Do not perform a repository-wide compatibility scan during ordinary routing.

## Canon progressive disclosure

Canon is an active engine only after `SYSTEM_MANIFEST.yaml` identifies `engine_id: canon` as `available`. For a Canon route:

1. load `engines/canon/MANIFEST.yaml`;
2. select the exact workflow named by the capability mapping;
3. load every item in `workflow_contracts.<workflow>.required_skills` plus only optional skills actually required by the assignment;
4. bind the workflow's explicit executing/consuming roles and upstream requirements;
5. feed those mandatory prerequisites into the normal compiler/capability/admissibility chain.

Do not reduce a multi-skill Canon workflow to one guessed skill. Do not recursively discover `engines/canon/skills/`. Engine availability does not confer Canon mutation authority.

The Canon authority chain remains:

```text
RESEARCH
→ EVIDENCE / FINDINGS
→ CANON RECONCILIATION
→ explicit Canon authority where mutation is requested
→ ACCEPTED CANON
```

Research findings, Software observations, and Verification results may be inputs or evidence; none automatically mutate Canon.

## Research constitutional precedence

For every Research Engine route, apply this order before executing project-specific instructions:

```text
OWNER / K0 MACHINE-ONLY CONSTITUTIONAL DECISION
→ kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md
→ contracts/EXECUTABILITY_CONTRACT.md
→ engines/research/MANIFEST.yaml + RESEARCH_CONTROL_CONTRACT.md
→ project-specific research architecture
→ work package
→ method / freeze
→ executor prompt
```

If a weaker layer requests prohibited non-owner human research, reject that method with `REJECT_METHOD / REQUIRE_MACHINE_REDESIGN`. Do not route to humans and do not block the whole research project merely because direct human measurement is unavailable.

Research fields such as `MACHINE_EXECUTABLE=true` and `CAN_EXECUTE_WITH_AVAILABLE_MACHINE_METHODS=true` are method-level machine-only admission claims. They do not replace destination executability preflight. The destination must separately prove the capabilities required by `EXECUTION_SURFACE`, `SOURCE_ACCESS_METHOD`, `COMPUTATION_METHOD`, verification method, and mandatory validators.

## Current routes

| Capability | Engine | Next surface |
|---|---|---|
| `establish_canon_foundation` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + all declared required skills; then generic executability preflight |
| `register_canon_fact` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the fact-registration skill as the selected semantic operation |
| `register_canon_assumption` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the assumption-registration skill as the selected semantic operation |
| `register_unknown` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the unknown-registration skill as the selected semantic operation |
| `register_ambiguity` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the ambiguity-registration skill as the selected semantic operation |
| `register_contradiction` | `canon` | load Canon manifest + `establish_canon_foundation` workflow + required skills; add the contradiction-registration skill as the selected semantic operation |
| `reconcile_research_into_canon` | `canon` | load Canon manifest + reconciliation workflow + all declared required skills; require exact Research/Canon refs and mutation authority for accepted changes |
| `classify_canon_change` | `canon` | load Canon manifest + production Canon-change workflow + all declared required skills |
| `validate_canon` | `canon` | load Canon manifest + validation-only `validate_canon` workflow + `validate-canon` skill; no freeze authority or freeze mutation is implied |
| `freeze_canon` | `canon` | load Canon manifest + validate/freeze workflow + all declared required skills and explicit freeze authority |
| `final_canon_reconciliation` | `canon` | load Canon manifest + final reconciliation workflow + all declared required skills and final Canon authority |
| `reopen_canon` | `canon` | load Canon manifest + reopen workflow + all declared required skills and explicit reopen authority |
| `implement_software_change` | `production/software` | load `engines/production/software/MANIFEST.yaml`, implementation workflow, then executability preflight |
| `diagnose_software_failure` | `production/software` | load Software manifest/diagnosis workflow, then executability preflight for required observations/tools |
| `plan_software_work` | `production/software` | load the Software Engine manifest and bounded planning skill set; require only the capabilities actually mandatory for planning/evidence |
| `review_software_change` | `production/software` | load the Software Engine review workflow; preflight the exact build/runtime/browser/repository evidence required; use Verification Engine only for independent claim verification |
| `verify_completion_claim` | `verification` | load `engines/verification/MANIFEST.yaml`; preflight every mandatory evidence path before assignment |
| `verify_exact_candidate_claims` | `verification` | load Verification Engine plus shared exact-state/evidence skills; distinguish remote-repository claims from local-worktree claims before assignment |
| `admit_research_question` | `research` | load the machine-only constitution, then Research manifest; method admission does not waive destination preflight for later execution |
| `plan_research_work` | `research` | validate machine-only method admission, then prove destination executability before activating an execution assignment |
| `execute_research_work` | `research` | run the declared machine-only research workflow only on an admissible destination/mode |
| `run_research_experiment` | `research` | use the default computational experiment/freeze contracts plus destination executability proof |
| `verify_research_work` | `research` | preflight automated Research validators and evidence access before assigning verification |
| `prepare_research_release` | `research` | freeze verified research and prepare the Canon reconciliation package without Canon mutation; preflight any mandatory validators/output surfaces |

## Non-materialized engine gate

If the required semantic capability belongs to Foundation or another engine whose status is `not_materialized`, return:

```text
ENGINE_NOT_MATERIALIZED / OWNER_OR_SYSTEM_GATE
required_capability: <capability>
required_engine: <engine>
reason: <why this engine owns the task>
```

Do not simulate a missing engine by borrowing Software skills or inventing new authority.

## Role activation

After an engine is selected and destination admissibility is proven, use only workflows and roles declared by that engine manifest. Shared roles live under `roles/`; shared reasoning skills are loaded only when the workflow names them or the assignment requires their owned decision process.

The active instance is:

```text
Relevant State Slice
+ Engine
+ Workflow
+ Role
+ Destination Capability Profile
+ Assignment Admissibility Proof
+ Assignment
+ Required Skills
= Active Agent Instance
```

## Forbidden routing behavior

- no recursive repository-wide skill search during ordinary execution;
- no loading every skill "for context";
- no selection by fuzzy title similarity alone;
- no use of the archived legacy global skill index as a runtime router;
- no crossing engine authority boundaries because a nearby skill looks applicable;
- no treating missing legacy execution metadata as proof of zero prerequisites;
- no treating semantic engine capability as proof of destination runtime capability;
- no issuing an assignment with an unproven or non-empty missing capability set;
- no silently weakening a mandatory evidence claim because the destination lacks its execution surface;
- no silently continuing when required authority, evidence, engine capability, or destination execution capability is absent;
- **PROHIBITED:** default Research Engine transitions to participant recruitment, survey deployment, interviews, external human review, or any other new non-owner human research.
