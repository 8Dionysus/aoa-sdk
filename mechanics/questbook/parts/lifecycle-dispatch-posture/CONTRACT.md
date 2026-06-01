# Lifecycle Dispatch Posture Contract

## Contract

Quest lifecycle states describe obligation posture and return route. Dispatch
readers, when added, must be generated from source records.

## Must

- keep lifecycle state meaning visible in `quests/README.md`;
- keep future generated readers lower authority than source records;
- require builder and validator routes before adding generated quest outputs.

## Must Not

- infer completion from file movement alone;
- publish generated quest readers by hand;
- use dispatch readers as proof or owner verdict authority.
