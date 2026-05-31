# Questbook Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Route SDK quest source records and durable followthrough obligations while
keeping owner acceptance outside the quest record itself.

### Trigger

Use this mechanic when root `quests/` records, quest source-store posture,
Agon helper quest candidates, or owner-followthrough quest pressure changes.

### SDK owns

- SDK quest source records under `quests/`
- quest source-store route posture
- candidate helper quest routing back to owning mechanics

### Stronger owner split

Agon, release, checkpoint, memory, proof, and other owner repositories decide
acceptance, completion, and durable meaning.

### Current source surfaces

- `quests/`
- `mechanics/agon/README.md`
- `mechanics/agon/PARTS.md`
- `ROADMAP.md`

### Candidate parts

- quest-source-store
- agon-helper-quests
- owner-followthrough

### Must not claim

This mechanic must not treat a quest record as owner acceptance, proof,
release readiness, or completed followthrough.

### Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q tests/test_mechanics_topology.py
```

### Next route

Agon helper quest pressure routes to `mechanics/agon/`; release pressure routes
to `mechanics/release-support/`; checkpoint residues route to
`mechanics/checkpoint/`.
