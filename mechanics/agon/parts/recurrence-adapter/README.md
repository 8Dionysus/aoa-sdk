# Agon Recurrence Adapter

## Role

This part owns the SDK-local Agon recurrence adapter and prebinding review
lanes.

## Input

- `config/agon_recurrence_adapter.seed.json`
- `config/agon_recurrence_prebinding_review_lanes.seed.json`
- public-safe recurrence review examples still owned by the recurrence example
  lane

## Output

- `generated/agon_recurrence_adapter_registry.min.json`
- `generated/agon_recurrence_prebinding_review_lanes.min.json`

## Owner

`aoa-sdk` owns the candidate-only adapter shape, local schemas, builders,
validators, and tests. Quest source records route through root `quests/`.
Agon owners retain doctrine, verdict,
rank, scar, retention, arena, and runtime authority.

## Start Here

- [CONTRACT](CONTRACT.md)
- [VALIDATION](VALIDATION.md)
- [docs](docs/)

## Artifact Homes

- `config/` - source inputs for the local generated companions
- `docs/` - active adapter and stop-line docs
- `generated/` - lower-authority compact registries
- `quests/agon/ready/` - source quest follow-through records for this part
- `schemas/` - adapter and lane contracts
- `scripts/` - builders and validators
- `tests/` - part-local regression checks

## Next Route

Use `../../PROVENANCE.md` for old root path accounting and
`../../../topology.json` for repo-wide route law.
