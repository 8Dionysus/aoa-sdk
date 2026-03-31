from pathlib import Path

from aoa_sdk import AoASDK


def test_pick_skill_uses_registry_search(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    matches = sdk.routing.pick(kind="skill", query="plan verify")

    assert [entry.name for entry in matches] == ["aoa-change-protocol"]


def test_inspect_and_expand_skill_use_routing_hints(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    capsule = sdk.routing.inspect(kind="skill", id_or_name="aoa-change-protocol")
    expanded = sdk.routing.expand(kind="skill", id_or_name="aoa-change-protocol")
    verification_only = sdk.routing.expand(
        kind="skill",
        id_or_name="aoa-change-protocol",
        sections=["verification"],
    )

    assert capsule["name"] == "aoa-change-protocol"
    assert [section["key"] for section in expanded["sections"]] == [
        "intent",
        "procedure",
        "verification",
    ]
    assert [section["key"] for section in verification_only["sections"]] == ["verification"]
