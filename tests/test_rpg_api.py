from __future__ import annotations

import json
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


def test_rpg_models_tolerate_additive_upstream_fields(workspace_root: Path) -> None:
    overlay_path = workspace_root / "Agents-of-Abyss" / "generated" / "dual_vocabulary_overlay.json"
    overlay = json.loads(overlay_path.read_text(encoding="utf-8"))
    overlay["future_overlay_tag"] = "wave-2"
    overlay["entries"][0]["ui_badge"] = "proof"
    overlay_path.write_text(json.dumps(overlay, indent=2) + "\n", encoding="utf-8")

    builds_path = workspace_root / "src" / "abyss-stack" / "generated" / "rpg" / "agent_build_snapshots.json"
    builds = json.loads(builds_path.read_text(encoding="utf-8"))
    builds["projection_epoch"] = "2026-04-02"
    builds["builds"][0]["future_rank_tier"] = "wave-2"
    builds["builds"][0]["loadout"]["recommended_toolset"] = "portable"
    builds_path.write_text(json.dumps(builds, indent=2) + "\n", encoding="utf-8")

    ledgers_path = workspace_root / "src" / "abyss-stack" / "generated" / "rpg" / "reputation_ledgers.json"
    ledgers = json.loads(ledgers_path.read_text(encoding="utf-8"))
    ledgers["window"] = "daily"
    ledgers["ledgers"][0]["projection_mode"] = "bounded"
    ledgers["ledgers"][0]["slices"][0]["display_delta"] = "+1"
    ledgers_path.write_text(json.dumps(ledgers, indent=2) + "\n", encoding="utf-8")

    runs_path = workspace_root / "src" / "abyss-stack" / "generated" / "rpg" / "quest_run_results.json"
    runs = json.loads(runs_path.read_text(encoding="utf-8"))
    runs["transport_generation"] = 2
    runs["runs"][0]["outcome"]["confidence_band"] = "high"
    runs["runs"][0]["execution"]["route_lane"] = "party_router"
    runs_path.write_text(json.dumps(runs, indent=2) + "\n", encoding="utf-8")

    bundles_path = workspace_root / "src" / "abyss-stack" / "generated" / "rpg" / "frontend_projection_bundles.json"
    bundles = json.loads(bundles_path.read_text(encoding="utf-8"))
    bundles["projection_family"] = "rpg-ui"
    bundles["bundles"][0]["views"]["agent_sheet_cards"][0]["accent_color"] = "amber"
    bundles["bundles"][0]["source_refs"]["quest_run_results"].append(
        "abyss-stack/generated/rpg/quest_run_results.json#QRR-2026-04-01-0001"
    )
    bundles_path.write_text(json.dumps(bundles, indent=2) + "\n", encoding="utf-8")

    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    assert sdk.rpg.vocabulary().label_for("proof_trust") == "Proof Trust"
    assert sdk.rpg.latest_build("AOA-A-0002").class_archetype == "coder"
    assert sdk.rpg.ledger("AOA-A-0002").subject_kind == "agent"
    assert sdk.rpg.run("QRR-2026-04-01-0001").outcome.run_status == "completed"
    assert sdk.rpg.latest_bundle().bundle_id == "frontend.bundle.2026-04-01T18:30:00Z"
