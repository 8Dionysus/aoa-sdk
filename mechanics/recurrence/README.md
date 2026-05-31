# Recurrence Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Manage recurrence manifests, hook packs, graph closure, review decisions,
downstream projections, live observations, and recursor readiness.

### Trigger

Use this mechanic when recurrence manifests, recurrence CLI behavior, graph
snapshots, owner review decisions, projections, live observation producers, or
recursor readiness changes.

### SDK owns

- recurrence control-plane helpers
- manifest compatibility scanning
- graph snapshot and closure readers
- owner-review decision templates and closure reports
- downstream projection builders
- live observation collection helpers

### Stronger owner split

Component owners own recurrence truth. `aoa-evals` owns proof of recurrence
control-plane integrity.

### Current source surfaces

- `docs/RECURRENCE_CONTROL_PLANE.md`
- `docs/RECURRENCE_HARDENING_COMPATIBILITY.md`
- `examples/recurrence/`
- `manifests/recurrence/`
- recurrence schemas under `schemas/`
- `scripts/validate_recurrence_manifests.py`
- `src/aoa_sdk/recurrence/`
- recurrence tests under `tests/`

### Candidate parts

- manifest-compatibility
- hook-pack
- graph-closure
- review-decision
- downstream-projections
- live-observations
- recursor-readiness

### Must not claim

This mechanic must not make recurrence projections source truth for routing,
stats, KAG, or owner components.

### Validation

```bash
python scripts/validate_recurrence_manifests.py --workspace-root /srv/AbyssOS
python -m pytest -q tests/test_recurrence_registry.py tests/test_recurrence_seed.py
```

### Next route

Projection or proof changes route to the owning downstream repository or
`aoa-evals` eval-suite handoff.
