# Skill Authoring

## Purpose

Use this skill when creating or editing reusable Project Resolver skills inside their owning namespace.

## Goal

Keep the reusable skill corpus useful, small, operational, and safely routable across heterogeneous destination runtimes. A skill should teach an agent how to do one recurring workflow with evidence, not dump generic advice or assume execution surfaces that may not exist.

## When to use

Use this skill when:

- adding a new skill
- editing an existing skill
- deciding whether a workflow should become a skill
- creating templates or references that support a skill

Do not use this skill for one-off project notes, task evidence, or product-specific docs that do not belong in the reusable system.

## Skill or template

| Need | Best artifact |
|---|---|
| Reusable procedure | `SKILL.md` |
| Reusable output shape | owning namespace template or shared library template |
| Current task state | copied template in product repo |
| Long-term project decision | project chronicle |
| Temporary experiment result | spike report |

## Required shape

Every new or substantively edited skill should include:

- Purpose
- Goal
- When to use
- Inputs
- **Execution contract**
- Required outputs
- Procedure
- Anti-patterns
- Verification checklist or minimal verdict format

The **Execution contract** must declare:

- required execution capabilities for mandatory steps;
- supported execution modes (for example remote-repository, local-worktree, interactive-browser, deployed-runtime);
- conditional/optional capabilities;
- mandatory evidence paths and any equivalent fallbacks;
- unsupported-environment behavior.

If a skill is pure reasoning and requires no external execution surface, state that explicitly rather than omitting the section.

Optional sections:

- Decision table
- Quick reference
- Escalation rules
- Pair with other skills
- Output template

## Executability law

A skill declaration does not prove that the current destination has its prerequisites. `contracts/EXECUTABILITY_CONTRACT.md` remains authoritative:

```text
REQUIRED_CAPABILITIES(skill/workflow/assignment mandatory steps)
⊆ AVAILABLE_CAPABILITIES(exact destination)
```

The Control Director/router performs that comparison before assignment. Skill authors must make prerequisites explicit enough to derive the required set without guessing.

For multiple execution modes, state the claim boundary of each mode. Do not label a fallback equivalent when it produces weaker evidence. Examples:

- remote GitHub state cannot prove an unpushed local worktree;
- Playwright still requires checkout + Node/package runtime + browser binaries;
- static inspection cannot silently replace mandatory deployed/browser/runtime observation.

## Naming rules

- Use lowercase directory names.
- Use hyphens between words.
- Prefer workflow names over tool names.
- Avoid broad names like `frontend`, `backend`, or `misc`.
- Do not create a new skill if an existing skill can be tightened.

Good:

- `systematic-debugging`
- `pre-merge-review`
- `webapp-dogfood-qa`

Bad:

- `coding`
- `do-better-ui`
- `everything-about-react`

## Ownership and discovery

Before creating or editing a skill:

1. Determine the owning engine, kernel, protocol, or library namespace and the capability owner.
2. Inspect that namespace's manifest and its skill index or registry when one exists.
3. Inspect only neighboring relevant skills needed to detect overlap or an existing owner under another name.
4. Do not scan the whole repository or rely on a root-wide skill catalog by default.

Current active skill locations include:

- `kernel/skills/`
- `protocols/skills/`
- `engines/verification/skills/`
- `engines/production/software/skills/`
- `library/skills/`

Use the selected owning namespace rather than creating a separate global skill location.

## Procedure

1. Establish ownership and bounded discovery using the rules above.
2. Confirm the workflow does not already have an owner that can be tightened instead of duplicated.
3. Decide whether the workflow is reusable enough to become a skill.
4. Start from `library/templates/SKILL_TEMPLATE.md` when creating a new skill.
5. Derive every mandatory external action/evidence step and declare its concrete execution prerequisites; separate supported modes and conditional capabilities.
6. Create or edit the skill under the selected owning namespace's existing or explicitly authorized skill location.
7. Keep the skill focused on procedure, decisions, evidence, failure modes, and execution prerequisites.
8. Add supporting templates only when they will actually be reused.
9. Update only the owning namespace manifest, skill index, or registry required for bounded discovery.
10. Verify the new or edited skill does not encourage unrelated rewrites, global discovery, vague completion claims, or assignment into unsupported environments.

## Good skill properties

| Property | Meaning |
|---|---|
| Triggered | The agent knows when to load it |
| Actionable | It tells the agent what to do, not just what to value |
| Bounded | It does one workflow, not every workflow |
| Evidence-based | It requires observable output or verification |
| Executability-explicit | Mandatory steps declare concrete destination prerequisites and evidence modes |
| Portable | It can be reused across projects/runtimes with explicit mode boundaries |
| Short | It avoids becoming a giant prompt dump |

## Anti-patterns

Avoid:

- copying large external skills verbatim
- hiding runtime/tool assumptions in procedure prose
- declaring `machine executable` or `AI can do this` without concrete execution surfaces
- treating a tool fallback as free of that tool's own runtime prerequisites
- adding tool-specific instructions without supported-mode/failure boundaries
- mixing product strategy, implementation, and QA in one skill
- creating overlapping skills with different names
- adding scripts or templates that no one will maintain
- recreating root-level global skill discovery or a parallel global skill directory
- saying a skill is complete without updating the required owning namespace registration

## Verification checklist

- [ ] The skill has a clear trigger.
- [ ] Its owning namespace and capability owner are identified.
- [ ] It does not duplicate an existing skill or owner.
- [ ] It has an Execution contract.
- [ ] Every mandatory external action/evidence step has concrete required capabilities.
- [ ] Supported execution modes and their claim/evidence boundaries are explicit.
- [ ] Unsupported environments fail before assignment or return an explicit non-admissible mode; they do not rely on planned downstream blockage.
- [ ] It has required outputs.
- [ ] It has anti-patterns or failure modes.
- [ ] It is concise enough for on-demand loading.
- [ ] Required owning namespace templates or registration entries were updated if needed.
- [ ] No root-level global discovery surface was introduced.

## Minimal verdict format

- Status
- Skill created or edited
- Owning namespace
- Required execution capabilities
- Supported execution modes
- Why it belongs in the reusable system
- Files changed
- Discovery updates
- Risks
