# RPG Parts

Active SDK RPG parts live here. They make RPG surfaces readable to callers
without moving gameplay, runtime, proof, quest, progression, or frontend truth
into the SDK.

## Part Map

| Part | Role | Active surfaces |
| --- | --- | --- |
| [`typed-consumer-api`](typed-consumer-api/README.md) | Loads upstream RPG surfaces into stable Python objects and helper methods. | API boundary doc, part tests |
| [`surface-path-transport`](surface-path-transport/README.md) | Names expected upstream generated transport paths and fragment refs. | transport path doc, route test |

## Active Part Contract

Every active part keeps:

- `README.md`: role, input, output, owner split, next route
- `CONTRACT.md`: allowed outputs and stop-lines
- `VALIDATION.md`: narrow validation route

Old root paths and former doc titles route through parent provenance and
artifact topology, not active compatibility aliases.
