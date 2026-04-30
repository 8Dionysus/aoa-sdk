# AoA Surface Detection First Wave

First-wave surface detection adds one read-only control-plane seam to
`aoa-sdk`. It does not extend the meaning of `aoa skills ...`, and it does not
move source ownership away from sibling repositories.

## Boundary

- `aoa skills detect`, `aoa skills dispatch`, `aoa skills enter`, and
  `aoa skills guard` stay skill-only
- `aoa surfaces detect` is additive and read-only
- `phase=checkpoint` may recommend local note capture, but it does not emit
  harvest verdicts or receipts
- only `skills` may appear in `immediate_skill_dispatch`
- `eval`, `memo`, `playbook`, `agent`, and `technique` surfaces stay hints,
  candidates, or reviewed closeout handoffs in wave one

## Report shape

`sdk.surfaces.detect(...)` and `aoa surfaces detect` emit
`SurfaceDetectionReport` with:

- repo and workspace context
- the requested surface phase, including `in-flight`
- optional checkpoint metadata and checkpoint candidate clusters when the phase
  is `checkpoint`
- the referenced skill prelude path when one was supplied
- current active skill names from the runtime session file when present
- `immediate_skill_dispatch` copied from the skill prelude only
- additive `items`, `closeout_followups`, `owner_layer_notes`, and
  `actionability_gaps`

Reports persist under:

```text
aoa-sdk/.aoa/surface-detection/{label}.{phase}.latest.json
```

## Skill prelude contract

`surfaces.detect` reuses the existing skill detector as a prelude.

- `ingress`, `pre-mutation`, and `closeout` call the matching skill phase
- `in-flight` reuses ingress scoring without changing the skill detector's
  public phase enum
- `checkpoint` also reuses ingress scoring and then adds local note-oriented
  checkpoint clustering
- the surface layer never calls `skills.dispatch`

## Truth rules

- `activated` is reserved for real skill activations from the skill prelude
- `manual-equivalent` records router-only skill discipline with honest fallback
  labeling
- non-skill surfaces never become `executable_now`
- `manual-equivalent` never mutates into `activated` during reporting or
  handoff

## Commands

```bash
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase ingress --intent-text "verify recurring handoff proof" --root /srv/AbyssOS/aoa-sdk --json
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase in-flight --intent-text "recall prior proof" --root /srv/AbyssOS/aoa-sdk --json
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase pre-mutation --intent-text "prove and recall a recurring route" --mutation-surface code --root /srv/AbyssOS/aoa-sdk --json
aoa surfaces detect /srv/AbyssOS/aoa-sdk --phase checkpoint --checkpoint-kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/AbyssOS/aoa-sdk --json
```

Use `docs/aoa-surface-detection-heuristics.md` for the deterministic ruleset and
`docs/aoa-surface-detection-closeout-handoff.md` for the reviewed-only handoff
contract.
