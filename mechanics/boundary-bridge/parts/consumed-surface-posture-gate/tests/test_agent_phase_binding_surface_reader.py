from datetime import timezone
from pathlib import Path

from aoa_sdk import AoASDK


def test_new_artifact_uses_bound_phase_binding(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    artifact = sdk.agents.new_artifact(phase="verify", payload={"ok": True})

    assert artifact.phase == "verify"
    assert artifact.artifact_type == "verification_result"
    assert artifact.payload == {"ok": True}
    assert artifact.produced_at.tzinfo == timezone.utc


def test_bindings_load_from_runtime_surface(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    bindings = sdk.agents.bindings()

    assert [binding.phase for binding in bindings] == ["route", "verify"]
    assert sdk.agents.binding_for_phase("verify").role_names == ["reviewer"]
