# Session Growth Checkpoints

`aoa-sdk` owns the control-plane seam for checkpoint-aware session growth.
It keeps checkpoint capture local-first and reviewable without turning the
existing session-harvest family into an automatic runtime authority.

## Boundary

- `aoa surfaces detect --phase checkpoint` stays additive and read-only
- `aoa skills enter` and `aoa skills guard` stay skill-first; by default they auto-append one local checkpoint note only when checkpoint-phase surface detection finds a real growth signal
- explicit `commit` or `verify-green` intents on a non-`none` mutation surface also count as local growth signals, even when recurring-route heuristics stay quiet
- use `--no-auto-checkpoint` to keep `aoa skills enter` or `aoa skills guard` read-only apart from the persisted skill report
- use `--checkpoint-kind` to override the inferred checkpoint kind when one explicit checkpoint event matters
- `aoa checkpoint append` writes only local note state under `.aoa/`
- checkpoint capture does not emit `HARVEST_PACKET`
- checkpoint capture does not emit `CORE_SKILL_APPLICATION_RECEIPT`
- promotion remains explicit through `aoa checkpoint promote`
- full harvest still belongs to the existing reviewed closeout path
- checkpoint notes carry harvest, progression, and upgrade candidates through the end of the session
- checkpoint notes keep provisional multi-axis movement for `boundary_integrity`, `execution_reliability`, `change_legibility`, `review_sharpness`, `proof_discipline`, `provenance_hygiene`, and `deep_readiness`
- candidate movement and stats refresh stay end-of-session decisions, not mid-session auto-promotion

## Local storage

Checkpoint state lives under:

```text
aoa-sdk/.aoa/session-growth/current/<repo-label>/
  checkpoint-note.jsonl
  checkpoint-note.json
  checkpoint-note.md
  harvest-handoff.json
  closeout-context.json
  closeout-execution-report.json
```

The JSONL file is append-only checkpoint history.
The JSON and Markdown files are rebuilt snapshots for current review.
Those rebuilt snapshots now act as the session-local ledger for:

- harvest candidates that should be bundled at reviewed closeout
- progression candidates and provisional axis movement that should feed `aoa-session-progression-lift` only at reviewed closeout
- upgrade candidates that should be reviewed once at closeout before any owner-layer promotion
- the final stats-refresh hint that belongs to the same reviewed closeout moment

`aoa skills enter` and `aoa skills guard` also surface that ledger directly in
their runtime JSON under `checkpoint_capture.session_end_skill_targets`,
`checkpoint_capture.progression_axis_signals`,
`checkpoint_capture.session_end_next_honest_move`, and
`checkpoint_capture.stats_refresh_recommended`.
At reviewed closeout the explicit bridge skill is
`aoa-checkpoint-closeout-bridge`: it builds `closeout-context.json`, rereads
the reviewed artifact, and then executes donor harvest, progression lift, and
quest harvest in order without refreshing stats inside the bridge itself.

## Commands

```bash
aoa skills detect /srv/aoa-sdk --phase checkpoint --intent-text "plan verify a bounded change" --root /srv/aoa-sdk --json
aoa skills enter /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "recurring workflow needs better handoff proof and recall" --mutation-surface code --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "commit bounded patch" --mutation-surface code --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "refresh generated contracts" --mutation-surface code --no-auto-checkpoint --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --append-note --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa skills guard /srv/aoa-sdk --intent-text "recurring owner follow-through after green verify" --mutation-surface code --checkpoint-kind verify_green --root /srv/aoa-sdk --json
aoa checkpoint append /srv/aoa-sdk --kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa checkpoint build-closeout-context /srv/aoa-sdk --reviewed-artifact /srv/path/to/reviewed_session_artifact.md --root /srv/aoa-sdk --json
aoa checkpoint execute-closeout-chain /srv/aoa-sdk --reviewed-artifact /srv/path/to/reviewed_session_artifact.md --root /srv/aoa-sdk --json
aoa checkpoint status /srv/aoa-sdk --root /srv/aoa-sdk --json
```

## Promotion read

`aoa checkpoint promote --target dionysus-note` writes one lightweight
reviewed snapshot into `Dionysus`.

`aoa checkpoint promote --target harvest-handoff` writes one local reviewed
handoff that can feed the explicit session-harvest family later.

Checkpoint notes stay below harvest verdict authority. They exist to preserve
good mid-session candidates until reviewed promotion is honest.
They should be carried through the session and only moved, harvested, or paired
with stats refresh from the final reviewed closeout path.
When progression evidence exists, reviewed closeout should raise
`aoa-session-progression-lift` before `aoa-quest-harvest`, so the final
multi-axis verdict is gathered once from the carried checkpoint evidence instead
of being guessed mid-session.
That reviewed closeout path should be driven through
`aoa-checkpoint-closeout-bridge`, not by silently widening `aoa closeout run`.
