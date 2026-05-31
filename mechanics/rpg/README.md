# RPG Mechanic

Status: skeleton.

## Mechanic Card

### Operation

Provide the RPG typed consumer slice and surface-path helpers without becoming
gameplay, frontend, or runtime authority.

### Trigger

Use this mechanic when RPG SDK docs, surface paths, registry models, or RPG API
tests change.

### SDK owns

- typed RPG registry models
- surface-path helper behavior
- SDK addendum and path documentation
- regression tests for the consumer slice

### Stronger owner split

RPG gameplay semantics, frontend behavior, state authority, and runtime
decisions remain outside SDK ownership.

### Current source surfaces

- `docs/RPG_SDK_ADDENDUM.md`
- `docs/RPG_SURFACE_PATHS.md`
- `src/aoa_sdk/rpg/`
- `tests/test_rpg_api.py`

### Candidate parts

- typed-registry
- surface-paths
- consumer-api

### Must not claim

This mechanic must not present typed reads as RPG gameplay execution or state
truth.

### Validation

```bash
python -m pytest -q tests/test_rpg_api.py
```

### Next route

Runtime or gameplay changes route to the RPG owner; SDK keeps typed reads and
path helpers.
