# Surface Detection Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Detect non-skill owner-layer candidates and route reviewed handoffs while
preserving skill-only activation boundaries.

### Trigger

Use this mechanic when additive surface heuristics, second-wave shortlist
behavior, owner-layer handoff, or CLI detection behavior changes.

### SDK owns

- additive first-wave and second-wave candidate detection
- heuristic implementation
- reviewed closeout handoff formatting
- local reports under SDK runtime surfaces

### Stronger owner split

Eval, memo, playbook, agent, technique, routing, and owner-layer semantics
remain with their owning repositories.

### Current source surfaces

- `docs/aoa-surface-detection-first-wave.md`
- `docs/aoa-surface-detection-second-wave.md`
- `docs/aoa-surface-detection-heuristics.md`
- `docs/aoa-surface-detection-closeout-handoff.md`
- `src/aoa_sdk/surfaces/`
- `tests/test_surfaces.py`
- `tests/test_surfaces_cli.py`

### Candidate parts

- first-wave-heuristics
- second-wave-shortlist
- reviewed-handoff

### Must not claim

This mechanic must not turn surface hints into routing authority, proof,
memory, role, or skill activation.

### Validation

```bash
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase ingress
python -m pytest -q tests/test_surfaces.py tests/test_surfaces_cli.py
```

### Next route

Durable detected pressure routes to the stronger owner or reviewed closeout
handoff, not to hidden SDK ownership.
