# A2A Return Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Assemble A2A summon, checkpoint bridge, reviewed closeout, and return
transition packets for bounded cross-agent return.

### Trigger

Use this mechanic when A2A rebase modules, return examples, checkpoint-return
tests, reviewed closeout packet shape, or return seam docs change.

### SDK owns

- typed packet assembly helpers
- public-safe A2A return fixtures
- local return seam docs
- SDK API tests for packet consistency

### Stronger owner split

Role handoff, durable memory, proof, progression, stress verdict, and agent
authority remain outside SDK packet assembly.

### Current source surfaces

- `docs/A2A_WAVE5_CODEX_RETURN_CHECKPOINT.md`
- `docs/RETURN_REENTRY_SEAM.md`
- `examples/a2a/`
- `src/aoa_sdk/a2a/`
- `tests/test_a2a_sdk_api.py`
- `tests/test_a2a_wave5_checkpoint_and_return.py`
- `tests/test_a2a_wave5_e2e_fixture.py`

### Candidate parts

- summon-target
- checkpoint-bridge
- reviewed-closeout
- return-transition

### Must not claim

This mechanic must not treat a return packet as proof that the receiving role
accepted the handoff.

### Validation

```bash
python -m pytest -q tests/test_a2a_sdk_api.py tests/test_a2a_wave5_checkpoint_and_return.py tests/test_a2a_wave5_e2e_fixture.py
```

### Next route

Accepted return meaning routes to the receiving role, memo, proof, or
progression owner.
