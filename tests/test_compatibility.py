from pathlib import Path

import pytest

from aoa_sdk import AoASDK
from aoa_sdk.errors import IncompatibleSurfaceVersion


def test_compatibility_report_includes_versioned_and_unversioned_surfaces(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = {entry.surface_id: entry for entry in sdk.compatibility.check_all()}

    assert report["aoa-playbooks.playbook_activation_surfaces.min"].compatibility_mode == "unversioned"
    assert report["aoa-playbooks.playbook_activation_surfaces.min"].compatible is True
    assert report["aoa-evals.eval_catalog.min"].detected_version == 1
    assert report["aoa-evals.eval_catalog.min"].compatible is True


def test_assert_compatible_raises_on_version_mismatch(workspace_root: Path) -> None:
    target = workspace_root / "aoa-skills" / "generated" / "runtime_discovery_index.json"
    target.write_text(
        target.read_text(encoding="utf-8").replace('"schema_version": 1', '"schema_version": 99'),
        encoding="utf-8",
    )
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    with pytest.raises(IncompatibleSurfaceVersion):
        sdk.compatibility.assert_compatible("aoa-skills.runtime_discovery_index")
