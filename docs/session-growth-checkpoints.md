# Session Growth Checkpoints

`aoa-sdk` owns the control-plane seam for checkpoint-aware session growth.
It keeps checkpoint capture local-first and reviewable without turning the
existing session-harvest family into an automatic runtime authority.

## Boundary

- `aoa surfaces detect --phase checkpoint` stays additive and read-only
- `aoa checkpoint append` writes only local note state under `.aoa/`
- checkpoint capture does not emit `HARVEST_PACKET`
- checkpoint capture does not emit `CORE_SKILL_APPLICATION_RECEIPT`
- promotion remains explicit through `aoa checkpoint promote`
- full harvest still belongs to the existing reviewed closeout path

## Local storage

Checkpoint state lives under:

```text
aoa-sdk/.aoa/session-growth/current/<repo-label>/
  checkpoint-note.jsonl
  checkpoint-note.json
  checkpoint-note.md
  harvest-handoff.json
```

The JSONL file is append-only checkpoint history.
The JSON and Markdown files are rebuilt snapshots for current review.

## Commands

```bash
aoa surfaces detect /srv/aoa-sdk --phase checkpoint --checkpoint-kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa checkpoint append /srv/aoa-sdk --kind commit --intent-text "recurring owner follow-through after green verify" --root /srv/aoa-sdk --json
aoa checkpoint status /srv/aoa-sdk --root /srv/aoa-sdk --json
```

## Promotion read

`aoa checkpoint promote --target dionysus-note` writes one lightweight
reviewed snapshot into `Dionysus`.

`aoa checkpoint promote --target harvest-handoff` writes one local reviewed
handoff that can feed the explicit session-harvest family later.

Checkpoint notes stay below harvest verdict authority. They exist to preserve
good mid-session candidates until reviewed promotion is honest.
