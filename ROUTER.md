# Project Resolver Router

`ROUTER.md` chooses the smallest authoritative and executable work surface. It does not discover the entire repository.

## Routing contract

```text
KERNEL
→ select ENGINE by semantic capability and authority boundary
→ ENGINE selects a declared WORKFLOW
→ derive mandatory actions + mandatory evidence gates
→ derive REQUIRED_CAPABILITIES
→ bind exact destination CAPABILITY_PROFILE
→ prove REQUIRED_CAPABILITIES ⊆ AVAILABLE_CAPABILITIES
→ materialize ASSIGNMENT_ADMISSIBILITY
→ only if ADMISSIBLE: issue ASSIGNMENT
→ WORKFLOW activates a durable ROLE
→ ROLE loads only required SKILLS and referenced artifacts
```

Selection is based on the transformation and authority required, not filename similarity. Semantic engine capability is necessary but never sufficient for assignment.

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

If the required semantic capability belongs to Canon, Foundation, or another engine whose status is `not_materialized`, return:

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
- no treating semantic engine capability as proof of destination runtime capability;
- no issuing an assignment with an unproven or non-empty missing capability set;
- no silently weakening a mandatory evidence claim because the destination lacks its execution surface;
- no silently continuing when required authority, evidence, engine capability, or destination execution capability is absent;
- **PROHIBITED:** default Research Engine transitions to participant recruitment, survey deployment, interviews, external human review, or any other new non-owner human research.
