# Agon Gate Routing Owner Boundary

The SDK bridge answers only the routing question: where should a pressure
pattern go next?

It may emit:

- `no_gate_service_route`;
- `agon_gate_candidate`;
- `agon_gate_candidate_missing_context`;
- `owner_review_required`;
- `quarantine_hint`.

These are advisory control-plane states, not arena states.

`Agents-of-Abyss` owns Agon law and lawful move vocabulary. `aoa-agents` owns
actor form and eligibility. `aoa-evals` owns proof and verdict meaning.
`aoa-memo` owns durable memory. `aoa-playbooks` owns trial choreography.
`aoa-stats` owns derived summaries, and `Tree-of-Sophia` owns slow canon.

The SDK may preserve owner-qualified refs and produce a handoff. It may not
decide the stronger owner's result or execute the handoff.
