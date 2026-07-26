# Plan Compilation Control-Plane Contract

## SDK owns

- the versioned `aoa_control_plane_plan_compiler_v1`;
- strict typed scenario artifact and reviewed-condition bindings;
- exact validation of the admitted owner projection and schema pin;
- deterministic guard pruning, dependency repair, provenance binding,
  snapshot identity, and plan identity;
- public Python and CLI compilation contours;
- rejection of incomplete, extra, stale, positional, or owner-conflicting
  inputs.

## Stronger owner split

- `aoa-playbooks` owns scenario meaning, abstract steps, conditions, policies,
  artifact roles, eval anchors, retention references, and closeout contour;
- routing owns route eligibility and route approval requirements;
- `aoa-agents` and `aoa-skills` own bound identities and capability meaning;
- the scenario reviewer owns each supplied boolean condition value;
- `aoa-evals` owns eval contracts and verdicts;
- `aoa-memo` owns retention meaning and receipts;
- the runtime owner supplies compatibility and later executes effects.

## Determinism

The plan identity binds the exact decision, scenario binding, runtime profile,
owner contour/schema/trust pin, compiler projection, and plan snapshot. Equal
inputs produce equal bytes. A false reviewed condition removes only its
guarded steps and guarded requirements; references to removed steps are
removed while retained relative order and retained dependencies stay intact.

## Fail-closed gates

- No blocked or unselected decision.
- No decision-reference or correlation mismatch.
- No scenario owner, playbook path, or Git-ref mismatch from the admitted
  contour snapshot.
- No missing, extra, reordered, or substituted agent/capability binding.
- No agent or capability moved outside its stronger owner repository.
- No generic input for a typed contour and no positional artifact matching.
- No empty generic input where `all_scenario_inputs` is required.
- No missing or extra reviewed conditions or requirement-owner references.
- No unsupported effect in the runtime profile.
- No stale digest, non-latest trust record, denied admission, missing subject
  store, missing required trust control, or schema drift.
- No route approval rewritten or dropped by the compiler.

## Stop lines

- A `RuntimeProfile` compatibility declaration is not adapter selection or
  execution authorization.
- A compiled `RunPlan` is an immutable candidate plan, not a session.
- C2 emits no command, prompt, tool argument, model choice, MCP binding,
  mutable lifecycle state, proof verdict, or memory truth.
- The SDK does not parse `PLAYBOOK.md` and does not hardcode substitute
  scenario meaning.
- Runtime dispatch and every effect remain outside C2.
