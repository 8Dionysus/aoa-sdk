# Recurrence Hardening & Compatibility

The recurrence registry must be generous in what it can observe and strict in what it loads.

## Law

`RecurrenceRegistry` loads only owner-authored `recurrence_component` manifests. Everything else in `manifests/recurrence` is one of three things:

1. known foreign recurrence-adjacent manifest, such as a hook binding set;
2. adapter-required manifest, currently most important for Agon-shaped observation-only files;
3. invalid or unknown manifest that belongs in quarantine diagnostics.

No mixed manifest should abort registry loading.

## Manifest kind ladder

- `recurrence_component`: component law loaded into the registry.
- `hook_binding_set`: known foreign manifest handled by hook registry.
- `wiring_plan`, `rollout_bundle`, `review_surface`: known foreign report/review shapes.
- `agon_recurrence_adapter`: observation-only compatibility shape, not live Agon runtime.
- `unknown`: quarantined until an owner makes the shape explicit.

## Doctor gaps

Manifest diagnostics become doctor gaps only when they matter operationally:

- `manifest_json_error`
- `invalid_manifest_shape`
- `unknown_manifest_kind`
- `foreign_manifest_requires_adapter`
- `owner_repo_mismatch`

Known hook binding sets should be visible in scan reports but not treated as connectivity failures.

## Agon boundary

Agon-shaped manifests may be detected, but they remain adapter-required and observation-only. Recurrence must not create arena sessions, write scars, emit verdicts, assign ranks, promote ToS, or spawn agents from this seed.
