from __future__ import annotations

from pathlib import Path

from aoa_sdk import AoASDK


def test_rpg_compatibility_report_marks_expected_surfaces_present(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")
    report = {entry.surface_id: entry for entry in sdk.rpg.compatibility.check_all()}

    assert report["Agents-of-Abyss.dual_vocabulary_overlay"].compatible is True
    assert report["Agents-of-Abyss.dual_vocabulary_overlay"].detected_version == "dual_vocabulary_overlay_v1"
    assert report["abyss-stack.rpg_build_snapshots"].compatible is True
    assert report["abyss-stack.rpg_reputation_ledgers"].compatible is True
    assert report["abyss-stack.rpg_quest_run_results"].compatible is True
    assert report["abyss-stack.rpg_frontend_projection_bundles"].compatible is True


def test_rpg_vocabulary_and_label_lookup_are_available(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    overlay = sdk.rpg.vocabulary()
    assert overlay.overlay_id == "aoa_default_rpg_en"
    assert sdk.rpg.label_for("proof_trust") == "Proof Trust"
    assert sdk.rpg.label_for("missing-key", default="Fallback") == "Fallback"


def test_rpg_latest_build_is_available(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    build = sdk.rpg.latest_build("AOA-A-0002")
    assert build.rank == "specialist"
    assert build.class_archetype == "coder"
    assert build.loadout.equipped_ability_ids == [
        "ability.aoa-change-protocol",
        "ability.aoa-safe-infra-change",
    ]


def test_rpg_runs_filter_by_agent_and_quest(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    runs = sdk.rpg.runs(agent_id="AOA-A-0002", quest_ref="AOA-Q-0006")
    assert len(runs) == 1
    assert runs[0].outcome.run_status == "completed"
    assert runs[0].execution.party == ["AOA-A-0002", "AOA-A-0004"]


def test_rpg_frontend_helpers_expose_bundle_views(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    bundle = sdk.rpg.latest_bundle()
    assert bundle.bundle_id == "frontend.bundle.2026-04-01T18:30:00Z"

    card = sdk.rpg.agent_sheet("AOA-A-0002")
    assert card.display_name == "Coder"
    assert card.rank == "specialist"

    board = sdk.rpg.quest_board(state="triaged")
    assert len(board) == 1
    assert board[0].quest_ref == "AOA-Q-0006"

    panel = sdk.rpg.reputation_panel("AOA-A-0002")
    assert panel.highlighted_slices[0].axis == "proof_trust"
