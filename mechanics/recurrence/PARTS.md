# Recurrence Parts

## Candidate Parts

| Part | Current surfaces | Future payload condition |
| --- | --- | --- |
| manifest-compatibility | `manifests/recurrence/`, `src/aoa_sdk/recurrence/compat.py` | only if manifest packs move under mechanics |
| hook-pack | hook schemas, recurrence hook manifests | only if hook examples need package-local ownership |
| graph-closure | `src/aoa_sdk/recurrence/graph.py`, graph schemas | only if graph snapshots become mechanic artifacts |
| review-decision | `src/aoa_sdk/recurrence/decisions.py`, review schemas | only if review ledgers need local fixtures |
| downstream-projections | projection schemas and builder script | only if projections need package-local generated lanes |
| live-observations | live observation schemas and collector | only if observation runs become packaged examples |
| recursor-readiness | recursor readiness script and examples | only if readiness exports become a standalone pack |
