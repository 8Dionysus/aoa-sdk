# Route Resolution Control-Plane Contract

## SDK owns

- the versioned deterministic resolver and score law;
- strict snapshot/source-lock validation;
- intersection of SDK-canonical routing entries with pinned
  `aoa-skills` owner projections;
- typed `resolved`, `degraded`, and `blocked` decisions;
- complete candidate explanations with no fallback;
- public Python and CLI resolution, explanation, and validation contours.

## Stronger owner split

- `aoa-skills` owns capability meaning, lifecycle, applicability, retrieval
  fields, effect declarations, bindings, and approval posture;
- `abyss-machine` owns artifact trust admission;
- `abyss-stack` owns the deployed routing mirror and runtime lifecycle;
- the requesting agent or scenario owner owns the intent and constraints;
- a candidate provider agent remains absent unless an exact stronger-owner
  projection supplies it; the caller is never substituted as that provider;
- the runtime owner retains activation, model/tool execution, and receipts.

## Determinism

The decision identity binds the canonical intent digest, exact input snapshot
digest, resolver version, and resolver artifact provenance. Repeated
resolution over those same inputs must produce the same decision bytes.

An exact top-score tie is ambiguity and therefore `blocked`. Sorting stabilizes
serialization only; it cannot select a winner.

## Fail-closed gates

- No implicit routing bundle discovery.
- No predecessor `aoa-routing` checkout dependency.
- No non-G5, untrusted, stale, or mixed-owner runtime snapshot.
- No unpinned capability graph.
- No missing, duplicate, or inconsistent owner projection.
- No unsupported capability kind or policy constraint.
- No deferred/candidate-only capability without an exact explicit constraint.
- No capability with invalid binding, effect, lifecycle, or approval posture.

## Stop lines

- A selected route is a candidate reference, not invocation.
- `RouteIntent.requested_by` is the caller, not a selected capability
  provider or scenario participant.
- `approval_required` is not approval.
- Explanation never reruns or changes resolution.
- Validation proves shape and parent binding, not execution.
- C1 does not compile `RunPlan`, instantiate `AoARunner`, select a runtime
  adapter, mutate a repository, or emit an external effect.
- Route resolution does not import skill, eval, memo, agent, playbook, proof,
  or runtime meaning into `aoa-sdk`.
