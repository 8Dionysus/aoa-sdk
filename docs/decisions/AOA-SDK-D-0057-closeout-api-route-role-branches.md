# Closeout API Route-Role Branches

## Status

Accepted.

## Index Metadata

- Decision ID: AOA-SDK-D-0057
- Original date: 2026-06-03
- Surface classes: source-topology, closeout, implementation, validation
- SDK facets: importable implementation, reviewed closeout runner, route-role branches
- Mechanic parents: checkpoint, release-support
- Guard families: source topology, reviewed closeout runner, owner follow-through
- Posture: accepted

## Context

`src/aoa_sdk/closeout/api.py` had the right public owner: `CloseoutAPI` is the
reviewed closeout runner facade. But the file also owned build-request loading,
manifest assembly, submit-reviewed request writing, queue and inbox movement,
publisher subprocess execution, stats refresh parsing, kernel next-step
analysis, owner/workflow follow-through, receipt evidence resolution, and
filesystem naming helpers.

That mixture made the closeout route hard to extend cleanly. A publisher,
queue, or follow-through change could land in the facade without passing
through the route-role that actually owns the behavior.

## Options Considered

- Keep `closeout/api.py` as the single closeout implementation module.
- Split only the largest helper region.
- Move closeout behavior into checkpoint closeout branches.
- Keep `CloseoutAPI` stable and split implementation helpers by closeout
  route role.

## Decision

Keep `src/aoa_sdk/closeout/api.py` as the public `CloseoutAPI` facade.

Move closeout implementation into named branches:

- `closeout/manifests.py` owns build-request loading, submit-reviewed request
  writing, manifest validation, and manifest assembly.
- `closeout/queue.py` owns enqueue, process-inbox, queue status, and
  manifest archival orchestration.
- `closeout/runner.py` owns one reviewed manifest run and report emission.
- `closeout/publishers.py` owns publisher specs, receipt-kind publisher
  mapping, publisher subprocess execution, stats refresh execution, and
  stdout parsing.
- `closeout/followthrough.py` owns kernel next-step, owner follow-through,
  workflow follow-through, owner handoff writing, and kernel receipt
  interpretation.
- `closeout/receipts.py` owns receipt collection, receipt-file loading,
  publisher detection, and evidence-ref resolution.
- `closeout/filesystem.py` owns queue path defaults, path resolution,
  safe closeout filenames, manifest archival, and small uniqueness helpers.

`CloseoutAPI` binds those route functions as methods so existing public and
private entrypoints remain available. This preserves the current
`skills/detector.py` use of `_build_kernel_next_step_brief`.

## Rationale

The reviewed closeout runner is a control-plane helper. It may coordinate
publisher scripts and report follow-through, but it does not own sibling
receipt semantics, stats truth, owner acceptance, or release publication.

Named branches let future changes enter through the pressure they actually
serve: queue mechanics, manifest construction, publisher execution, receipt
evidence, or follow-through briefs.

## Consequences

- Public `CloseoutAPI` behavior remains stable.
- Existing private method access remains available where current SDK code
  already uses it.
- `api.py` should remain facade-only.
- New publisher or stats behavior belongs in `publishers.py`.
- New owner/workflow follow-through behavior belongs in `followthrough.py`.
- New queue/inbox behavior belongs in `queue.py`.
- New path or naming helpers belong in `filesystem.py`.

## Source Surfaces

- `src/aoa_sdk/closeout/api.py`
- `src/aoa_sdk/closeout/manifests.py`
- `src/aoa_sdk/closeout/queue.py`
- `src/aoa_sdk/closeout/runner.py`
- `src/aoa_sdk/closeout/publishers.py`
- `src/aoa_sdk/closeout/followthrough.py`
- `src/aoa_sdk/closeout/receipts.py`
- `src/aoa_sdk/closeout/filesystem.py`
- `src/aoa_sdk/skills/detector.py`
- `mechanics/checkpoint/parts/reviewed-session-handoff-runner/tests/`
- `generated/source_topology.min.json`
- `tests/test_source_topology_index.py`

## Follow-Up Route

Do not add implementation behavior to `closeout/api.py`. Add behavior to the
owning closeout route branch, and route stronger owner meaning back to the
sibling repo or reviewed checkpoint closeout context that owns it.

## Verification

The executable decision-index and owning-surface checks are routed through
`docs/decisions/AGENTS.md` and the nearest source-owner validation surface.
