from pathlib import Path

from aoa_sdk import AoASDK


def test_discover_and_disclose_skills(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    discovered = sdk.skills.discover(query="plan verify", mutation_surface="repo")
    disclosure = sdk.skills.disclose("aoa-change-protocol")

    assert [skill.name for skill in discovered] == ["aoa-change-protocol"]
    assert disclosure.skill_dir == ".agents/skills/aoa-change-protocol"
    assert "Verification" in disclosure.headings_available


def test_activate_and_manage_session(workspace_root: Path, tmp_path: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = tmp_path / ".aoa" / "skill-runtime-session.json"

    activation = sdk.skills.activate(
        "$aoa-change-protocol",
        session_file=str(session_file),
        explicit_handle="$aoa-change-protocol",
        include_frontmatter=True,
    )
    second_activation = sdk.skills.activate(
        "aoa-change-protocol",
        session_file=str(session_file),
    )
    session = sdk.skills.session_status(str(session_file))
    packet = sdk.skills.compact(str(session_file))
    cleared = sdk.skills.deactivate("aoa-change-protocol", str(session_file))

    assert activation["skill"].name == "aoa-change-protocol"
    assert activation["frontmatter"]["name"] == "aoa-change-protocol"
    assert activation["content"]["instructions_markdown"].startswith("# aoa-change-protocol")
    assert second_activation["session"].active_skills[0].activation_count == 2
    assert session.active_skills[0].activation_count == 2
    assert packet["active_skill_packets"][0]["name"] == "aoa-change-protocol"
    assert cleared.active_skills == []
