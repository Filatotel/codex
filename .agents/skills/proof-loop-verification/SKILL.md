# Proof Loop Verification

## Purpose

Use this skill when work is close to complete and you need to decide whether the task is actually done.

## Principle

Completion is not a statement. Completion is a claim backed by durable evidence.

## Inputs

- task goal
- acceptance criteria
- current branch or commit
- changed files
- available test or verification commands
- known risks and assumptions

## Required outputs

Produce or update a task evidence artifact that includes:

- summary of intended outcome
- exact scope checked
- commands or checks performed
- observed results
- unresolved issues
- final verdict: pass, partial, or fail

## Procedure

1. Restate the acceptance criteria in concrete terms.
2. Check the actual changed files against the claimed scope.
3. Run or inspect the strongest available verification, not the easiest one.
4. Record evidence, not just conclusions.
5. If evidence is incomplete, downgrade the verdict.
6. Do not use optimistic language when the outcome is partial.

## Anti-patterns

Avoid:

- done in theory
- probably works
- tested locally without details
- omitting known risks from the verdict

## Minimal verdict format

- Status
- Scope checked
- Evidence
- Risks
- Next action
