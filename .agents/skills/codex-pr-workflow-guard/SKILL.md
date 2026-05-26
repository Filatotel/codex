# Codex PR Workflow Guard

## Purpose

Use this skill when an agent opens, updates, reviews, or prepares to merge a GitHub pull request.

## Goal

Catch process failures that make code review unreliable: stale PR bodies, wrong branch scope, duplicate PRs, missing checks, unresolved current review threads, outdated comments treated as current blockers, and claims of QA that did not happen.

## When to use

Use this skill when:

- a PR is created or updated by an agent
- a PR is declared ready to merge
- review comments or bot comments appear
- the branch needs a follow-up fix
- a task should continue in the same PR instead of a new PR
- mergeability, deploy status, or checks are unclear

## Inputs

Collect:

- repository and PR number
- target branch and head branch
- latest head SHA
- changed files
- PR body
- review threads and comments
- check and deploy status
- commands the agent claims it ran
- whether the task is new scope or a fix to current scope

## Procedure

1. Verify the PR head branch and target branch match the requested work.
2. Verify the latest head SHA is the one being reviewed.
3. Check whether the PR body describes the actual latest scope and checks.
4. Check mergeable state, required checks, and deploy status.
5. Separate current review threads from outdated comments tied to old commits.
6. If a bug is in the current PR scope, continue in the same branch.
7. If starting from main with new scope, do not mention stopping an unrelated old PR in the task text.
8. Verify claimed commands are plausible and listed with exact names.
9. Do not accept manual QA claims unless evidence or steps are provided.
10. Produce a merge-readiness verdict with blockers and non-blocking warnings.

## Common failures

- agent says PR body was updated but it still contains stale text
- branch is mergeable false but the PR is called ready
- deploy is still in progress when code is approved
- a review comment is outdated but treated as current
- a current P1 is ignored because checks pass
- new PR is created for a bug that belongs in the current PR
- task prompt tells Codex to stop work on a PR it cannot see
- agent claims manual QA without evidence

## Blockers

Treat these as blocking:

- mergeable false or unknown when merge readiness is requested
- latest required check or deploy is failing or still in progress
- unresolved current P1/P2 review thread
- PR body materially misrepresents scope or test status
- follow-up fix was made on a different branch without reason
- claimed verification is missing and no equivalent evidence exists

## Required output

```md
## Codex PR workflow guard

- Status: pass / partial / fail
- PR and head SHA:
- Scope match:
- PR body accuracy:
- Checks and deploy status:
- Current review threads:
- Outdated comments:
- Same-branch vs new-branch decision:
- Blockers:
- Recommended next action:
```

## Pair with

- `pre-merge-review`
- `merge-preview-check`
- `proof-loop-verification`
- `git-branch-integrity`
