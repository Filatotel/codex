# Common Project Resolver Contracts

These contracts define shared meanings. Engines may extend them but may not silently redefine them.

## STATE
**Definition:** durable accepted or candidate facts relevant to the project. **Authority:** the authority named for that state domain. **Required fields:** identity/version, status, provenance, authority, affected scope. **Invariants:** chat history is not state; state mutations are explicit. **Do not confuse with:** context, evidence, or an implementation observation.

## AUTHORITY
**Definition:** the right to accept, reject, or mutate a governed state/decision. **Owner:** the declared governing role or Owner/K0 boundary. **Required fields:** authority scope, holder/source, permitted actions, escalation path. **Invariants:** writing/carrying/observing information does not create authority. **Do not confuse with:** information access, verification ability, or implementation ownership.

## ENGINE
**Definition:** bounded owner of a class of transformations. **Authority:** system manifest + engine manifest. **Required fields:** `engine_id`, owns, does_not_own, inputs, outputs, entry/exit conditions, dependencies, workflows/capabilities. **Invariant:** conceptual separation does not require a separate repository. **Do not confuse with:** role or workflow.

## WORKFLOW
**Definition:** a declared transformation path inside an engine or shared control layer. **Authority:** owning engine/protocol. **Required fields:** workflow id, entry condition, roles, transitions, outputs, stop conditions. **Invariant:** workflow selects role/skills; it does not acquire new authority. **Do not confuse with:** lifecycle state graph as a whole.

## ROLE
**Definition:** durable responsibility and authority contract instantiated by disposable agents. **Authority:** shared/engine role registry. **Required fields:** purpose, authority, context contract, inputs, procedure, outputs, handoff, stop/escalation. **Invariant:** ROLE != AGENT INSTANCE. **Do not confuse with:** personality or a permanent worker.

## SKILL
**Definition:** bounded reusable procedure for how to perform one recurring decision/work method. **Authority:** owning namespace/library lifecycle. **Required fields:** id/name, trigger/use boundary, inputs, procedure, outputs, failure/stop rules; Solution Patterns also need assumptions/rejection conditions/alternatives/trade-offs. **Invariant:** a skill does not expand role or engine authority. **Do not confuse with:** engine, role, or universal architecture.

## ASSIGNMENT
**Definition:** exact instruction for what must happen now. **Authority:** issuer within declared scope. **Required fields:** id, objective, authority, input state ref, allowed/forbidden scope, acceptance, required outputs, stop conditions, result recipient. **Invariant:** assignment is bounded; missing authority is not inferred. **Do not confuse with:** role contract or project Canon.

## ARTIFACT
**Definition:** durable carrier of a result, claim, decision, or state proposal. **Authority:** source role produces it; downstream authority decides acceptance where required. **Required fields:** stable identity, type, producer role, assignment/state refs, status, provenance, related artifacts. **Invariant:** ARTIFACT != EVIDENCE. **Do not confuse with:** proof simply because it exists.

## EVIDENCE
**Definition:** observations/data that support a specific claim about an exact relevant state. **Authority:** evidence has information value; acceptance authority remains separate. **Required fields:** claim, exact target identity, method/source, result, freshness/trust boundary. **Invariants:** evidence cannot prove a stronger claim than it observes; stale affected evidence is not current proof. **Do not confuse with:** approval, authority, or artifact presence.

## GATE
**Definition:** explicit condition that controls an admissible state/workflow transition. **Authority:** declared by governing workflow/authority. **Required fields:** gate id, required conditions/evidence/authority, PASS/BLOCKED outcome, next transition. **Invariant:** gates fail closed when required proof/authority is absent. **Do not confuse with:** arbitrary ceremony or a permanent human bottleneck.

## HANDOFF
**Definition:** durable transfer of bounded continuation state between role instances. **Authority:** producing role owns accuracy of its handoff; receiving role revalidates affected assumptions. **Required fields:** source/recipient role, state/assignment refs, completed work, unresolved/blockers, evidence refs, exact next owner/action. **Invariant:** hidden chat memory is not a handoff. **Do not confuse with:** verification or acceptance.

## OWNER QUESTION
**Definition:** a human-readable request for a decision that only Owner/K0 may make. **Authority:** Owner/K0. **Required fields:** why decision is needed, options, consequences, recommendation, unresolved uncertainty, what follows. **Invariant:** do not manufacture Owner questions for decisions already delegated. **Do not confuse with:** an implementation clarification the active role can resolve within authority.

## STATE MUTATION
**Definition:** proposed or accepted change to governed durable state. **Authority:** mutation requires the authority of the affected state domain. **Required fields:** mutation id/proposal artifact, prior state ref, proposed change, reason/evidence, authority decision, resulting state ref. **Invariant:** no silent mutation. **Do not confuse with:** editing a carrier file when the edit has not been accepted as state.

## Mandatory distinctions

- `IMPLEMENTATION FACT != CANONICAL FACT`: software observations cannot silently become Canon truth.
- `ARTIFACT != EVIDENCE`: a report may point to proof but does not prove itself.
- `ROLE != AGENT INSTANCE`: agents are replaceable executions of durable contracts.
- `STATE != CHAT CONTEXT`: durable state survives independently of conversation history.
- `VERIFICATION AUTHORITY != INFORMATION AUTHORITY`: a verifier may establish whether claims are supported; it does not thereby own product/Canon/Owner decisions.
