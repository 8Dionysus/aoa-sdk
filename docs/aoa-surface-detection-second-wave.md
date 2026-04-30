# AoA Surface Detection Second Wave

Second-wave surface detection stays additive to the first-wave seam in
`aoa-sdk`. It sharpens visibility; it does not create a new semantic owner.

## Purpose

The second wave adds three bounded enrichments around the existing
`sdk.surfaces` flow:

- advisory owner-layer shortlist hints from `aoa-routing.owner_layer_shortlist.min`
- richer `surface_detection_context` references preserved from
  `aoa-skills` core-skill receipts
- descriptive observability from `aoa-stats.surface_detection_summary.min`
- stats re-grounding hints derived from `aoa-stats` surface profiles and
  source coverage
- reviewed checkpoint-note preservation through local session-growth notes and
  closeout handoff references

## What Changes

`sdk.surfaces.detect(..., include_shortlist=True)` now keeps shortlist hints,
owner-layer ambiguity notes, stable family-entry refs, and receipt-backed
evidence links when sibling repos publish them.

`sdk.routing.owner_layer_shortlist()` exposes the router-owned shortlist as a
typed advisory read. It is not a verdict engine.

`sdk.stats.surface_detection()` exposes date-window summaries for:

- `activated` versus `manual-equivalent-adjacent`
- `candidate-now` versus `candidate-later`
- owner-layer ambiguity frequency
- closeout handoff target volume
- repeated-pattern and promotion-discussion signals

`sdk.stats.regrounding_signal()` reads `source_coverage_summary` and the target
surface profile as a policy input. In pre-mutation or public-share contexts,
thin coverage and high-risk profiles can require a re-grounding read before a
consumer relies on derived stats.

`sdk.routing.stats_regrounding_hints()` exposes router-owned advisory next-read
hints for those stats surfaces. It is not a verdict engine.

## Hard Invariants

- `aoa skills ...` stays skill-only
- checkpoint notes remain local reviewed notes until explicit promotion
- `manual-equivalent` never becomes `activated`
- non-skill items never enter `immediate_skill_dispatch`
- routing shortlist hints are advisory only
- routing stats re-grounding hints are advisory only
- `aoa-stats` remains descriptive only

## Example

```python
from aoa_sdk import AoASDK

sdk = AoASDK.from_workspace("/srv/AbyssOS/aoa-sdk")

report = sdk.surfaces.detect(
    repo_root="/srv/AbyssOS/aoa-sdk",
    phase="ingress",
    intent_text="prove and recall a recurring route",
    include_shortlist=True,
)
shortlist = sdk.routing.owner_layer_shortlist(signal="scenario-recurring")
surface_stats = sdk.stats.surface_detection(window_date="2026-04-05")
```
