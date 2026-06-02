# RPG Mechanic

Status: active topology with part-local payload.

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
- typed consumer API boundary and path documentation
- regression tests for the consumer slice

### Stronger owner split

RPG gameplay semantics, frontend behavior, state authority, and runtime
decisions remain outside SDK ownership.

### Current source surfaces

- `mechanics/rpg/parts/typed-consumer-api/`
- `mechanics/rpg/parts/surface-path-transport/`
- `src/aoa_sdk/rpg/`

### Candidate parts

- typed-consumer-api
- surface-path-transport

### Must not claim

This mechanic must not present typed reads as RPG gameplay execution or state
truth.

### Validation

Use the touched part `VALIDATION.md` for executable checks. For package-wide
route changes, use `mechanics/topology.json` for the active validation list
and then run the mechanics topology gate from the root route card.

### Next route

Runtime or gameplay changes route to the RPG owner; SDK keeps typed reads and
path helpers.
