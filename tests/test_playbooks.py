from pathlib import Path

from aoa_sdk import AoASDK


def test_playbooks_local_read_path(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    listed = sdk.playbooks.list(status="active")
    registry_entry = sdk.playbooks.get("AOA-P-0011")
    activation = sdk.playbooks.activation_surface("bounded-change-safe")
    handoff = sdk.playbooks.handoff_contracts("bounded-change-safe")
    failure = sdk.playbooks.failure_catalog(code="APPROVAL_REQUIRED")
    recipe = sdk.playbooks.subagent_recipe(playbook="bounded-change-safe")

    assert [item.name for item in listed] == ["bounded-change-safe", "restartable-inquiry-loop"]
    assert registry_entry.name == "bounded-change-safe"
    assert activation.memo_source_route_policy == "required"
    assert handoff.name == "bounded-change-safe"
    assert failure.summary.startswith("The requested action crosses an approval boundary")
    assert recipe[0].name == "safety-split"
