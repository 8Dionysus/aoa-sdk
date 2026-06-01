# Facade Boundary

`sdk/facade-boundary/` owns SDK route posture for sibling readers,
compatibility policy, and truth-label boundaries.

## Families

| Family | Role | Next route |
| --- | --- | --- |
| `sibling-surface-readers/` | typed readers over sibling-owned surfaces | facade registries and Boundary Bridge tests |
| `compatibility-policy/` | drift checks and supported source refs | `src/aoa_sdk/compatibility/`, `docs/versioning.md` |
| `truth-label-posture/` | explicit authority and review labels | `src/aoa_sdk/models.py`, `docs/boundaries.md` |

## Stop Lines

- The SDK owns handles, not sibling meaning.
- Compatibility should expose drift, not smooth it away.
- Truth labels are not owner acceptance by themselves.
