# Closeout Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Assemble reviewed closeout requests, manifests, inbox processing, next-step
briefs, and owner followthrough handoffs.

### Trigger

Use this mechanic when `aoa closeout ...` behavior, closeout schemas,
followthrough maps, inbox automation, or systemd units change.

### SDK owns

- mechanical closeout request assembly
- reviewed manifest assembly from available artifacts
- local inbox processing helper behavior
- owner followthrough handoff bundle shape
- optional local unit installation helpers

### Stronger owner split

Owner receipts, durable memory, proof, harvest, progression, and skill
application remain stronger than SDK closeout artifacts.

### Current source surfaces

- `docs/session-closeout.md`
- `docs/closeout-followthrough-map.md`
- `scripts/install_closeout_units.py`
- `scripts/process_closeout_inbox.py`
- `src/aoa_sdk/closeout/`
- `systemd/`
- `tests/test_closeout.py`

### Candidate parts

- request-assembly
- manifest-assembly
- inbox-processing
- owner-followthrough

### Must not claim

This mechanic must not claim that mechanical bridge artifacts prove skill
application or owner acceptance.

### Validation

```bash
python -m pytest -q tests/test_closeout.py
```

### Next route

After closeout produces owner pressure, route it to the owning repository or
reviewed memory/proof/progression surface.
