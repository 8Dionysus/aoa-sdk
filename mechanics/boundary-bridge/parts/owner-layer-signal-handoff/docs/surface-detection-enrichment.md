# AoA Surface Detection Enrichment

Enrichment adds advisory context without changing candidate truth.

## Inputs

- current `aoa-routing.owner_layer_shortlist.min` hints;
- descriptive stats re-grounding signals from owner-published stats surfaces;
- local checkpoint candidates created during the current repository session.

Shortlist refs to retired `aoa-skills` surfaces are removed from consideration
and reported in `inspection_gaps`. The SDK does not silently translate them to
new surfaces.

Session-local skill receipts and activation logs are intentionally not
enrichment inputs. They remain session evidence and cannot make an owner
candidate current, executable, or accepted.

## Invariants

- shortlist and stats hints remain advisory;
- all surface items remain non-executable;
- checkpoint carry stays local until reviewed handoff;
- owner records remain stronger than SDK reports;
- stale or malformed optional context produces an honest gap or no hint, not a
  fabricated fallback.
