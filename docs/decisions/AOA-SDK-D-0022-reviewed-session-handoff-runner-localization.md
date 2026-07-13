# Reviewed Session Handoff Runner Localization

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0022
- Original date: 2026-06-01
- Surface classes: topology, mechanics, artifact placement, validation guard
- SDK facets: mechanics topology, checkpoint, reviewed session handoff runner
- Mechanic parents: checkpoint
- Guard families: mechanics topology, part validation, active naming, owner boundary
- Posture: accepted

## Context

After the technique readiness reader slice, root `docs/` and `scripts/` still
held reviewed-session handoff runner payload:

- `docs/session-closeout.md`
- `scripts/install_closeout_units.py`
- `scripts/process_closeout_inbox.py`

These files are not repo-wide release or validation gates. They are Checkpoint
part payload: input is reviewed session material and owner-local receipts;
output is a closeout request/manifest/inbox/report path plus owner-publisher and
stats-refresh handoff.

## Decision

Move the docs and operator scripts into:

- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/`

Keep `src/aoa_sdk/closeout/` as importable SDK source. Keep deployment unit
filenames systemd-native, but place the unit templates under the part-local
runner route and point them at the part-local inbox processor path.

## Rationale

`reviewed-session-handoff-runner` names the operation explicitly: it builds,
queues, processes, and reports reviewed closeout manifests. The part still stays
below owner truth because it
only calls owner-owned publisher scripts and derived stats refreshes.

The `closeout-inbox-user-units/` templates are deployment wiring rather than the runner
implementation. They live under the part because they deploy only this runner.

## Consequences

- Root `docs/` and `scripts/` no longer carry the handoff runner implementation
  payload.
- The `closeout` former-parent legacy route now points to
  `checkpoint/reviewed-session-handoff-runner`.
- `aoa-closeout-inbox.service` now executes the part-local processor.
- Owner publishers, stats truth, proof, memory, and technique promotion remain
  outside SDK authority.

## Source Surfaces

- `mechanics/checkpoint/README.md`
- `mechanics/checkpoint/PARTS.md`
- `mechanics/checkpoint/PROVENANCE.md`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/`
- `src/aoa_sdk/closeout/`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/aoa-closeout-inbox.service`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/closeout-inbox-user-units/aoa-closeout-inbox.path`
- `mechanics/ARTIFACT_TOPOLOGY.md`
- `mechanics/topology.json`
- `README.md`
- `ROADMAP.md`

## Follow-Up Route

Continue root technical district audit for Checkpoint test placement, Questbook
payload, and cross-mechanic public contracts.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
