# Project Resolver Agent Rules

This repository is the **Project Resolver / Agent Project Operating System**. It is a modular monorepo of bounded engines, shared contracts, durable roles, protocols, skills, and evidence rules.

## Ordinary runtime intake

For ordinary execution, read only:

1. `AGENTS.md`
2. `SYSTEM_MANIFEST.yaml`
3. `ROUTER.md`

Then load only the selected engine manifest, selected workflow/role contract, assignment, and required bounded skill namespace.

**NO GLOBAL SKILL DISCOVERY DURING ORDINARY EXECUTION.** Do not recursively scan the repository, load every skill, or use a global catalog as the runtime router.

### Research constitutional preload

When the selected capability belongs to the Research Engine, `kernel/RESEARCH_MACHINE_ONLY_CONSTITUTION.md` is a mandatory upstream kernel contract and MUST be loaded before project-specific research architecture, work packages, methods, or executor prompts.

A downstream research instruction cannot weaken that constitution. If a method requests prohibited non-owner human participation, stop and reject the method, then redesign it for machine execution or return an explicit evidence limitation. Do not convert the research project into `BLOCKED_PENDING_HUMANS`.

## Control rules

- **State is durable. Chat is not authoritative state.** Use explicit artifacts and exact state references.
- **Agents are disposable; roles are durable.** An active agent instance is assembled from relevant state + engine + workflow + role + assignment + required skills.
- **Context is assembled, not inherited.** Do not rely on hidden or prior chat history as authority.
- **Engine authority is bounded.** An engine owns its declared work class only. Software does not own K0/Owner authority, Canon truth, Research truth, or universal contracts.
- **Default Research is machine-only.** Owner/K0 is the only default human actor and supplies project authority, not routine research labor. New third-party human research is invalid unless Owner/K0 explicitly creates a separate bounded `human-research/` workstream.
- Load only the selected engine manifest and its declared dependencies. Do not cross an engine boundary by convenience.
- Follow the exact assignment and its authority. No silent scope expansion, no silent Owner-intent redefinition, and no silent state mutation.
- Claims that depend on a candidate/revision/environment must cite exact-state evidence. `ARTIFACT != EVIDENCE`; evidence must actually support the claim.
- Missing capability, missing authority, unresolved contradiction, or unavailable required engine is an explicit stop/escalation condition, not permission to improvise governance.
- **Solution Patterns are optional.** Select them only when their assumptions and rejection conditions match; production success never promotes a pattern into universal law.
- Relevant shared-state change invalidates affected evidence/preconditions until fresh verification, equivalence proof, rebuild/rebase, or explicit stop. A universal exclusive lease is not required.
- Architecture is not reconsidered merely because implementation is difficult. Distinguish implementation failure, local architecture defect, and invalidated architecture assumption; open an Architecture Reconsideration Gate only on evidence or before an explicitly planned hard-to-reverse commitment.

## Durable control

State changes require explicit authority and a durable mutation/decision record. Role-native outputs remain distinct: in particular, `EXECUTOR_RESULT` and `VERIFICATION_RESULT` are separate artifacts, and a Control Director consumes both where verification is required.
