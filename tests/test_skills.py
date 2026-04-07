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


def test_project_foundation_reads(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    foundation = sdk.skills.project_foundation()

    assert foundation.foundation_id == "project-foundation-v1"
    assert foundation.canonical_install_profile == "repo-project-foundation"
    assert foundation.skill_count == 22
    assert foundation.skills[:3] == [
        "aoa-session-donor-harvest",
        "aoa-automation-opportunity-scan",
        "aoa-session-route-forks",
    ]
    assert foundation.skills[-3:] == [
        "aoa-local-stack-bringup",
        "aoa-safe-infra-change",
        "aoa-sanitized-share",
    ]


def test_project_risk_guard_ring_reads(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    ring = sdk.skills.project_risk_guard_ring()
    governance = sdk.skills.project_risk_guard_ring_governance()

    assert ring.ring_id == "project-risk-guard-ring-v1"
    assert ring.skills == [
        "aoa-approval-gate-check",
        "aoa-dry-run-first",
        "aoa-local-stack-bringup",
        "aoa-safe-infra-change",
        "aoa-sanitized-share",
    ]
    assert [entry.skill_name for entry in governance] == ring.skills
    assert all(entry.governance_passed for entry in governance)


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


def test_detect_and_dispatch_ingress(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    session_file = workspace_root / "aoa-sdk" / ".aoa" / "skill-runtime-session.json"

    report = sdk.skills.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="plan verify a bounded change",
    )
    dispatch_report = sdk.skills.dispatch(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="ingress",
        intent_text="plan verify a bounded change",
        session_file=str(session_file),
    )
    session = sdk.skills.session_status(str(session_file))

    assert [item.skill_name for item in report.activate_now] == ["aoa-change-protocol"]
    assert report.must_confirm == []
    assert dispatch_report.activate_now[0].skill_name == "aoa-change-protocol"
    assert session.active_skills[0].name == "aoa-change-protocol"


def test_detect_pre_mutation_raises_risk_gates_without_auto_running_them(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.skills.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="pre-mutation",
        intent_text="plan verify a bounded change",
        mutation_surface="runtime",
    )

    assert [item.skill_name for item in report.activate_now] == ["aoa-change-protocol"]
    assert [item.skill_name for item in report.must_confirm] == [
        "aoa-approval-gate-check",
        "aoa-dry-run-first",
        "aoa-local-stack-bringup",
        "aoa-safe-infra-change",
    ]
    assert "mutation_without_explicit_risk_confirmation" in report.blocked_actions


def test_detect_closeout_reuses_kernel_brief(workspace_root: Path) -> None:
    from tests.test_closeout import install_closeout_fixture

    fixture = install_closeout_fixture(workspace_root)
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    report = sdk.skills.detect(
        repo_root=str(workspace_root / "aoa-sdk"),
        phase="closeout",
        closeout_path=str(fixture["manifest_path"]),
    )

    assert report.closeout_chain is not None
    assert report.closeout_chain.suggested_skill_name == "aoa-automation-opportunity-scan"
    assert [item.skill_name for item in report.must_confirm] == ["aoa-automation-opportunity-scan"]
