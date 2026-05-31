# Agon Provenance

## Source Surfaces

- `config/`
- `docs/AGON_WAVE1_EXPERIENCE_CAPTURE_PIPELINE.md`
- `generated/agon_recurrence_adapter_registry.min.json`
- `schemas/agon-recurrence-adapter-registry.schema.json`
- `scripts/build_agon_recurrence_adapter_registry.py`
- `scripts/validate_agon_recurrence_adapter.py`
- `tests/test_agon_recurrence_adapter.py`

## Stronger Owners

Agon owners decide helper acceptance and domain truth. SDK Agon surfaces are
candidate helper contracts and generated control-plane readers.

## Notes

This shared mechanic name is kept because the same Agon package pressure is
visible across the refactored AoA repos.

Agon quest records route through `mechanics/questbook/` as quest-source parts,
then back to Agon only when helper-candidate meaning is in scope.
