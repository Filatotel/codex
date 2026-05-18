# Operational Auditing

## Purpose

Use this skill to audit a repository, deployment, workflow, or application for operational risk.

## Goal

Find hidden breakage, unsafe assumptions, missing verification, workflow drift, security leaks, deployment mistakes, or incomplete integrations before they become production failures.

## When to use

Use this skill when:

- onboarding into a repository
- reviewing an AI-generated codebase
- preparing deployment
- inheriting a project
- validating a contractor or agent contribution
- checking workflow maturity
- auditing Cloudflare or GitHub setup

## Audit categories

| Category | Questions |
|---|---|
| Repository hygiene | Are secrets ignored? Are binaries committed? Is structure understandable? |
| Build integrity | Does build actually pass? Are scripts deterministic? |
| Deployment | Are Pages/Workers assumptions documented and reproducible? |
| Config/env | Are env vars and bindings named consistently? |
| UI/UX | Is mobile usable? Are CTA and flows visible? |
| Forms/integrations | Do forms validate? Do CRM payloads still match expected shape? |
| Analytics | Are important events captured consistently? |
| QA | Is there any browser/testing harness? |
| Docs | Can a new contributor understand the system? |
| Git workflow | Are PR/review/handoff workflows operational? |

## Audit scoring

| Score | Meaning |
|---|---|
| Critical | Immediate production or security risk |
| High | Serious operational weakness |
| Medium | Important but survivable issue |
| Low | Cleanup or polish item |

## Procedure

1. Inspect repository structure.
2. Identify frameworks, deployment targets, and workflows.
3. Check scripts, config, and env assumptions.
4. Review documentation and onboarding clarity.
5. Verify QA/testing coverage.
6. Review operational risks.
7. Produce actionable findings.

## Required outputs

- Executive summary
- Audit categories reviewed
- Findings by severity
- Evidence
- Recommended fixes
- Operational maturity verdict

## Anti-patterns

Avoid:

- generic security theater
- pretending coverage exists when it does not
- praising style while ignoring operational risk
- massive architecture rewrites without justification
- auditing only code and ignoring workflows
