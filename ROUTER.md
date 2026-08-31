# Project Resolver Router

`ROUTER.md` chooses the smallest authoritative work surface. It does not discover the entire repository.

## Routing contract

```text
KERNEL
→ select ENGINE by semantic capability and authority boundary
→ ENGINE selects a declared WORKFLOW
→ WORKFLOW activates a durable ROLE
→ ROLE loads only required SKILLS and referenced artifacts
```

Selection is based on the transformation and authority required, not filename similarity.

## Research constitutional precedence

For every Research Engine route, apply this order before executing project-specific instructions:

```text
OWNER / K0 MACHINE-ONLY CONSTITUTIONAL DECISION
→ kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md
→ engines/research/MANIFEST.yaml + RESEARCH_CONTROL_CONTRACT.md
→ project-specific research architecture
→ work package
→ method / freeze
→ executor prompt
```

If a weaker layer requests prohibited non-owner human research, reject that method with `REJECT_METHOD / REQUIRE_MACHINE_REDESIGN`. Do not route to humans and do not block the whole research project merely because direct human measurement is unavailable.

## Current routes

| Capability | Engine | Next surface |
|---|---|---|
| `implement_software_change` | `production/software` | load `engines/production/software/MANIFEST.yaml`, then its implementation workflow |
| `diagnose_software_failure` | `production/software` | load `engines/production/software/MANIFEST.yaml`, then its diagnosis workflow |
| `plan_software_work` | `production/software` | load the Software Engine manifest and bounded planning skill set |
| `review_software_change` | `production/software` | load the Software Engine review workflow; use Verification Engine only for independent claim verification |
| `verify_completion_claim` | `verification` | load `engines/verification/MANIFEST.yaml`, then the completion-claim verification workflow |
| `verify_exact_candidate_claims` | `verification` | load Verification Engine plus shared exact-state/evidence skills |
| `admit_research_question` | `research` | load the machine-only constitution, then `engines/research/MANIFEST.yaml` and its default workflow |
| `plan_research_work` | `research` | validate question/work-package machine executability before activation |
| `execute_research_work` | `research` | run the declared machine-only research workflow |
| `run_research_experiment` | `research` | use the default computational experiment/freeze contracts |
| `verify_research_work` | `research` | run automated Research Engine verification and machine-only policy validation |
| `prepare_research_release` | `research` | freeze verified research and prepare the Canon reconciliation package without Canon mutation |

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

After an engine is selected, use only workflows and roles declared by that engine manifest. Shared roles live under `roles/`; shared reasoning skills are loaded only when the workflow names them or the assignment requires their owned decision process.

The active instance is:

```text
Relevant State Slice
+ Engine
+ Workflow
+ Role
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
- no silently continuing when required authority, evidence, or engine capability is absent;
- **PROHIBITED:** default Research Engine transitions to participant recruitment, survey deployment, interviews, external human review, or any other new non-owner human research.
