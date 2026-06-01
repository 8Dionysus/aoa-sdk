# Skill Runtime Bridge Contract

## Allowed Outputs

- Skill detection and dispatch reports.
- Host availability labels: `host-executable`, `router-only`, and `unknown`.
- Runtime session file selection and compact active-skill packets.
- Manual equivalence notes when router-only risk gates remain semantically
  important.

## Stop-Lines

- Do not define canonical skill meaning in `aoa-sdk`.
- Do not claim router-only skills were directly executed.
- Do not turn manual equivalence into hidden approval.
- Do not let `aoa skills ...` become owner-layer surface dispatch, proof,
  memory, role, playbook, or runtime authority.

## Owner Split

The SDK keeps the bridge honest and typed. `aoa-skills` owns skill definition,
skill export posture, and stronger runtime availability law.
