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

## Current routes

| Capability | Engine | Next surface |
|---|---|---|
| `implement_software_change` | `production/software` | load `engines/production/software/MANIFEST.yaml`, then its implementation workflow |
| `diagnose_software_failure` | `production/software` | load `engines/production/software/MANIFEST.yaml`, then its diagnosis workflow |
| `plan_software_work` | `production/software` | load the Software Engine manifest and bounded planning skill set |
| `review_software_change` | `production/software` | load the Software Engine review workflow; use Verification Engine only for independent claim verification |
| `verify_completion_claim` | `verification` | load `engines/verification/MANIFEST.yaml`, then the completion-claim verification workflow |
| `verify_exact_candidate_claims` | `verification` | load Verification Engine plus shared exact-state/evidence skills |

## Non-materialized engine gate

If the required semantic capability belongs to Canon, Research, Foundation, or another engine whose status is `not_materialized`, return:

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
- no silently continuing when required authority, evidence, or engine capability is absent.
