# Questbook Mechanic

Status: active package.

## Mechanic Card

### Operation

Keep SDK obligations visible, lane-routed, and returnable through root
`quests/`, root `QUESTBOOK.md`, and future generated quest readers.

### Trigger

Open this mechanic when a helper follow-through, owner handoff, checkpoint
return, or reviewed closeout pressure needs a durable source record instead of
being hidden in a part-local payload directory or roadmap prose.

### SDK owns

The SDK owns quest source placement for SDK obligations, human index posture,
lifecycle vocabulary, dispatch-reader posture, and validation that source
quest records do not become runtime or owner authority.

### Stronger owner split

Agon doctrine, verdicts, rank, retention, KAG promotion, Tree of Sophia canon,
proof verdicts, memory truth, release publication, and sibling owner acceptance
remain outside this mechanic.

### Current source surfaces

- `QUESTBOOK.md`
- `quests/README.md`
- `quests/AGENTS.md`
- `quests/agon/README.md`
- `quests/agon/ready/`
- `mechanics/questbook/PARTS.md`
- `mechanics/questbook/parts/quest-source-store/`
- `mechanics/questbook/parts/public-obligation-index/`
- `mechanics/questbook/parts/lifecycle-dispatch-posture/`

### Candidate parts

- `quest-source-store`
- `public-obligation-index`
- `lifecycle-dispatch-posture`

### Must not claim

- Do not use quest records as proof verdicts, owner acceptance, or release
  readiness.
- Do not hide source quest records under helper part payload homes.
- Do not add generated quest readers without a source-derived builder and
  validator.
- Do not mint top-level quest aliases outside lane/state directories.

### Validation

```bash
python scripts/validate_mechanics_topology.py
python scripts/validate_nested_agents.py --strict-advisory --fail-on-untracked
python -m pytest -q tests/test_mechanics_topology.py tests/test_design_surfaces.py
```

### Next route

Use `quests/<lane>/<state>/` for source records, `QUESTBOOK.md` for human
visibility, and the owning mechanic part for helper contracts or runtime
validation.
