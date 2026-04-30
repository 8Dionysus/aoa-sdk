# Stats Re-Grounding Policy

## Purpose

`aoa-sdk` reads `aoa-stats` surface profiles and source coverage as policy
inputs for consumer-side re-grounding.

This is a control-plane decision helper. It is not an eval verdict, not routing
authority, and not owner truth.

## Inputs

The SDK consumes:

- `aoa-stats.summary_surface_catalog.min`
- `aoa-stats.source_coverage_summary.min`
- `aoa-routing.stats_regrounding_hints.min`

The stats catalog entry is treated as a `surface_profile`: input posture,
owner-truth inputs, authority ceiling, consumer risk, and live-state capability.

The source coverage summary is treated as an intake audit: missing owners,
unexpected owners, dominant owner/event-family skew, and registry absence can
raise a re-grounding recommendation or requirement.

The routing surface is advisory only. It helps consumers find the next owner
read; it does not decide policy.

## API

```python
from aoa_sdk import AoASDK

sdk = AoASDK.from_workspace("/srv/AbyssOS/aoa-sdk")

coverage = sdk.stats.source_coverage()
profile = sdk.stats.surface_profile("surface_detection_summary")
signal = sdk.stats.regrounding_signal(
    "surface_detection_summary",
    phase="pre-mutation",
    mutation_surface="code",
)
routing_hints = sdk.routing.stats_regrounding_hints(
    surface_name="surface_detection_summary",
)
```

`sdk.surfaces.detect(...)` also includes `regrounding_hints`,
`regrounding_required`, and `regrounding_reason_codes` when the intent names a
stats-sensitive path.

## Boundary

Stats says what is derived and where its feed is thin.
SDK says whether the consumer should re-ground before acting.
Routing says where to look next.
Evals can check that this split stayed bounded.
Owner repos still decide source truth.
