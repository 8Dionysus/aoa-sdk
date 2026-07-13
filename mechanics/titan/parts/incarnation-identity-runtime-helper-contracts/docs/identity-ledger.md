# Titan Identity Ledger

The SDK identity ledger commands operate over Titan bearer state and lineage events.

## Objects

```text
role_key       class of agent work
bearer_id      named remembered agent entity
incarnation_id runtime appearance
event_id       append-only lineage event
```

## Executable route

Bearer listing and lineage-event append behavior are owned by the part-local
`scripts/titan_lineage.py`; canonical operator and regression routes are in
`../VALIDATION.md`.

A fall does not delete the bearer.
It marks status and appends a fall event.
