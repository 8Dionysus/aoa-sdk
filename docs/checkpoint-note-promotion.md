# Checkpoint Note Promotion

Checkpoint promotion is the bridge from local `.aoa/session-growth/` capture
into reviewed durable lineage.

## Targets

- `dionysus-note`
  writes one lightweight snapshot into `Dionysus/reports/ecosystem-audits/`
- `harvest-handoff`
  writes one local reviewed handoff for later explicit session-harvest use

## Guardrails

- if `Dionysus` is missing, stay local and do not silently fall back
- if `Dionysus` is a dirty git checkout, block the promotion and keep the local
  reviewed note authoritative for now
- promotion does not replay raw append history into `Dionysus`
- full `session-harvest.*` surfaces remain end-of-session or
  sufficient-density artifacts, not checkpoint scratchpads

## Closeout link

When a local checkpoint note exists, `sdk.surfaces.build_closeout_handoff(...)`
may preserve:

- `checkpoint_note_ref`
- `surviving_checkpoint_clusters`

This keeps the closeout seam aware of reviewed checkpoint survivors without
pretending those survivors already became a harvest verdict.
