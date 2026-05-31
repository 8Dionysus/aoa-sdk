# Agon Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Build and validate Agon SDK helper candidates, registries, recurrence adapters,
state-packet bridges, generated companions, and helper quest seeds.

### Trigger

Use this mechanic when an Agon helper seed, generated registry, schema,
example, quest, or SDK helper test changes.

### SDK owns

- SDK helper candidate schemas and examples
- generated helper registries from local seeds
- candidate-only quest surfaces
- SDK stop-line documentation for Agon helper bridges

### Stronger owner split

Agon owners retain doctrine, verdict, duel-kernel, Sophian, KAG, SLC, VDS,
mechanical-trial, and state-packet meaning.

### Current source surfaces

- `config/`
- `docs/AGON_*.md`
- `generated/agon_*.min.json`
- `quests/`
- Agon schemas under `schemas/`
- `scripts/build_agon_*.py`
- `scripts/validate_agon_*.py`
- `tests/test_agon_*.py`

### Candidate parts

- helper-candidates
- registries
- recurrence-adapter
- state-packet-bindings
- quest-seeds

### Must not claim

This mechanic must not make candidate helper packs accepted Agon truth or
replace stronger Agon owner review.

### Validation

```bash
python -m pytest -q tests/test_agon_recurrence_adapter.py tests/test_agon_wave7_recurrence_lanes.py
```

### Next route

Accepted helper meaning routes to the Agon owner surface; SDK keeps only
candidate helper contracts and generated read models.
