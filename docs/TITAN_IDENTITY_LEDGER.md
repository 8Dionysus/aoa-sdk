# Titan Identity Ledger

The SDK identity ledger commands operate over Titan bearer state and lineage events.

## Objects

```text
role_key       class of agent work
bearer_id      named remembered agent entity
incarnation_id runtime appearance
event_id       append-only lineage event
```

## Example

```bash
python scripts/titan_lineage.py list \
  --bearers /srv/aoa-agents/config/titan_bearers.v0.json

python scripts/titan_lineage.py fall \
  --bearers /srv/aoa-agents/config/titan_bearers.v0.json \
  --ledger /srv/aoa-agents/config/titan_lineage_ledger.v0.json \
  --bearer-id titan:forge:founder \
  --summary "Forge exceeded mutation scope during pilot." \
  --lesson "Require expected_files before mutation gate." \
  --source-ref receipts/session-042.json
```

A fall does not delete the bearer.
It marks status and appends a fall event.
