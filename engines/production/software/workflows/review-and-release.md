# Software Workflow — Review and Release Support

**Entry:** exact software candidate/result that needs integration review, technical QA, or release preparation, plus destination executability proof for the mandatory review/release actions and evidence paths selected for this assignment.

Software-owned review skills may include `pre-merge-review`, `merge-preview-check`, `git-branch-integrity`, `operational-auditing`, browser QA, and deployment/data engineering support as applicable.

Before assignment, derive concrete capabilities from the selected mandatory review surface. Examples:

- local branch/worktree assertions require `repository_local_checkout` / `git_local_worktree` and any required shell/git execution surface;
- build/install/test minima require the matching checkout, package/runtime, and command execution capabilities;
- browser QA requires `interactive_browser` or a fully provisioned declared browser-automation mode such as `playwright_runtime` plus its own checkout/runtime/package/browser prerequisites;
- deployed/runtime/database assertions require the exact deployed/network/database access needed by the claim;
- remote PR/branch state may use a declared repository connector/API mode, but cannot prove local-only state.

Known missing mandatory capability before dispatch is `ASSIGNMENT_NOT_ADMISSIBLE`. Do not reinterpret a mandatory full review as `PASS` merely because only static/remote evidence is available. A supported partial review is valid only when the assignment explicitly scopes/accepts partial evidence.

Shared exact-state/evidence rules bind all claims to the actual candidate/environment. A production mutation is an explicit authority boundary, not an incidental worker feedback loop.

Software review/support does not replace independent Verification Engine authority. When the acceptance contract requires verification, hand exact assignment + Executor Result + candidate/evidence refs to `engines/verification/` and preflight the verifier destination separately; preserve both role-native results for Control Director.
