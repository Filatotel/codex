# Git Branch Integrity

## Purpose

Use this skill before major edits, before handoff, and before declaring a branch ready for review.

## Goal

Prevent branch-local success from hiding merge or provenance problems.

## Capture at start

Record the following in branch state:

- repository
- current branch
- target branch
- base SHA
- merge base SHA
- task scope
- files expected to change

## Capture during work

Keep branch state updated with:

- newly touched files
- scope expansions
- blockers
- assumptions
- dependency on upstream changes

## Verify before sign-off

1. Confirm the branch still matches the intended scope.
2. Confirm no unrelated files were changed.
3. Check whether target branch moved since the work started.
4. Check whether rebase or merge is likely to change behavior.
5. Note whether verification was run only on the feature branch or also after sync with target branch.

## Required caution

Do not say ready to merge unless merge drift risk has been assessed.

## Recommended artifact

Update `templates/BRANCH_STATE.md` derived file with:

- base SHA
- current HEAD SHA
- target branch SHA when checked
- merge risk notes
- verification status
