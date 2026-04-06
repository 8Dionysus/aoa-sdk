from pathlib import Path

from aoa_sdk import AoASDK


def test_discover_and_disclose_skills(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    discovered = sdk.skills.discover(query="plan verify", mutation_surface="repo")
    disclosure = sdk.skills.disclose("aoa-change-protocol")

    assert [skill.name for skill in discovered] == ["aoa-change-protocol"]
    assert disclosure.skill_dir == ".agents/skills/aoa-change-protocol"
    assert "Verification" in disclosure.headings_available


def test_project_core_outer_ring_reads(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    ring = sdk.skills.project_core_outer_ring()
    readiness = sdk.skills.project_core_outer_ring_readiness()

    assert ring.ring_id == "project-core-engineering-ring-v1"
    assert ring.skills == [
        "aoa-adr-write",
        "aoa-source-of-truth-check",
        "aoa-bounded-context-map",
        "aoa-core-logic-boundary",
        "aoa-port-adapter-refactor",
        "aoa-change-protocol",
        "aoa-tdd-slice",
        "aoa-contract-test",
        "aoa-property-invariants",
        "aoa-invariant-coverage-audit",
    ]
    assert [entry.skill_name for entry in readiness] == ring.skills
    assert all(entry.readiness_passed for entry in readiness)


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
