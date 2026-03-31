from datetime import timezone
from pathlib import Path

from aoa_sdk import AoASDK


def test_new_artifact_uses_utc_timestamp(tmp_path: Path) -> None:
    sdk = AoASDK.from_workspace(tmp_path)

    artifact = sdk.agents.new_artifact(phase="verify", payload={"ok": True})

    assert artifact.phase == "verify"
    assert artifact.artifact_type == "verify_artifact"
    assert artifact.payload == {"ok": True}
    assert artifact.produced_at.tzinfo == timezone.utc
