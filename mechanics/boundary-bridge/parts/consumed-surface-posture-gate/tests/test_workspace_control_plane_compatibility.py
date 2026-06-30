from __future__ import annotations

import json
from pathlib import Path

from aoa_sdk.compatibility import CompatibilityAPI
from aoa_sdk.workspace.discovery import Workspace


def test_workspace_control_plane_rejects_malformed_artifact_identity(workspace_root: Path) -> None:
    surface_path = workspace_root / "aoa-sdk" / "generated" / "workspace_control_plane.min.json"
    payload = json.loads(surface_path.read_text(encoding="utf-8"))
    payload["artifact_identity"] = None
    surface_path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")

    check = CompatibilityAPI(Workspace.discover(workspace_root)).check("aoa-sdk.workspace_control_plane.min")

    assert check.compatible is False
    assert "artifact_identity" in check.reason
    assert "JSON objects" in check.reason


def test_workspace_control_plane_accepts_artifact_identity_object(workspace_root: Path) -> None:
    check = CompatibilityAPI(Workspace.discover(workspace_root)).check("aoa-sdk.workspace_control_plane.min")

    assert check.compatible is True
