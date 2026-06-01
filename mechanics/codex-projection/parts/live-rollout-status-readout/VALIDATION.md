# Live Rollout Status Readout Validation

Run:

```bash
python -m pytest -q mechanics/codex-projection/parts/live-rollout-status-readout/tests/test_live_rollout_status_readout.py
python scripts/validate_mechanics_topology.py
```

For broader Codex Projection routing, also run:

```bash
python -m pytest -q mechanics/codex-projection/parts/workspace-mcp-server/tests/test_workspace_mcp_server.py tests/test_docs_routes.py mechanics/release-support/parts/public-support-ci-posture/tests/test_public_support_ci_posture.py
```
