# Software Workflow — Diagnosis

**Entry:** a software failure or unexplained red signal with bounded target state.

**Primary role:** Executor.

Load `skills/systematic-debugging` and shared `kernel/skills/anti-loop-execution`. Add `exact-state-verification`, authority/dependency skills, or technical QA skills only when their owned question is present.

Preserve failure taxonomy. Provider/environment/not-executed evidence is not automatically a code defect. After repeated same-class correction failure, stop point-fixing and enter causal audit rather than expanding scope.

**Exit:** demonstrated root cause and bounded correction path, or explicit BLOCKED/PARTIAL with unresolved causal evidence. Emit Executor Result; independent verifier checks completion claims separately.
