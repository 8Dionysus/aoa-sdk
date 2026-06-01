# AGENTS.md

## Applies to

`mechanics/codex-projection/parts/`.

## Role

Route functioning Codex Projection parts that own SDK-local Codex-facing
control-plane artifacts while keeping runtime and rollout authority outside the
SDK.

## Read before editing

- `mechanics/AGENTS.md`
- `mechanics/codex-projection/AGENTS.md`
- `mechanics/codex-projection/PARTS.md`
- the target part `README.md`, `CONTRACT.md`, and `VALIDATION.md`

## Boundaries

- Stay on the control plane.
- Do not make SDK readouts a Codex runtime or deploy authority.
- Keep external rollout artifact names as compatibility inputs, not active SDK
  route names.
- Do not add a functioning part without local contract and validation docs.

## Validation

```bash
python scripts/validate_mechanics_topology.py
python -m pytest -q mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py
```

## Closeout

Report which part moved root payload, which external owner tokens remain as
compatibility inputs, and which validation commands ran.
