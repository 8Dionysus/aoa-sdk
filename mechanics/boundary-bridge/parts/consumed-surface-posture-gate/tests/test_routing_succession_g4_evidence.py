from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from aoa_sdk.contracts.routing import RoutingOwnerLayerShortlistHint


PART_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = PART_ROOT / "evidence" / "routing-succession-g4-evidence.json"
VERIFIER_PATH = PART_ROOT / "scripts" / "verify_routing_succession_g4.py"
CANONICAL_GENERATED_ROOT = Path(
    os.environ["AOA_ROUTING_CANONICAL_GENERATED_ROOT"]
)


def load_evidence() -> dict[str, object]:
    return json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_g4_proves_shadow_without_switching_authority() -> None:
    evidence = load_evidence()
    scope = evidence["scope"]
    gate = evidence["gate_g4"]

    assert evidence["schema_version"] == "aoa_sdk_routing_succession_g4_evidence_v1"
    assert evidence["status"] == "g4_passed_shadow_only"
    assert scope["repository_state"] == "sdk_shadow"
    assert scope["canonical_producer"] == "aoa-routing"
    assert scope["publication_posture"] == "non_publishing"
    assert gate["verdict"] == "pass"
    assert gate["canonical_producer_switch_authorized"] is False
    assert gate["runtime_publication_authorized"] is False
    assert gate["g5_owner_switch"] is False
    assert gate["repository_archive_authorized"] is False


def test_g4_pins_full_corpus_and_all_canonical_artifact_hashes() -> None:
    evidence = load_evidence()
    full_corpus = evidence["pins"]["full_corpus"]
    hashes = full_corpus["output_sha256"]

    assert len(full_corpus["input_source_refs"]) == 14
    assert full_corpus["input_source_refs"]["aoa-sdk"] == (
        "29de1b1f893c683e0923cbf0cf0ee13beaa86d0e"
    )
    assert len(hashes) == 14
    assert all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in hashes.values())
    assert hashes["aoa_router.min.json"] == (
        "f01e3722d675c1776f20ad09e1ac43e5e646de8bdad2858a30d39ba7b7534cb7"
    )
    assert {
        path.name: sha256(path)
        for path in CANONICAL_GENERATED_ROOT.iterdir()
        if path.is_file()
    } == hashes
    assert evidence["verification_matrix"]["route_count"] == 170


def test_g4_requires_full_corpus_replay_before_runtime_dry_run() -> None:
    source = VERIFIER_PATH.read_text(encoding="utf-8")

    assert "--input-workspace-root" in source
    assert "--abyss-stack-input-root" in source
    assert "_materialize_full_corpus" in source
    assert "_verify_full_corpus" in source
    assert "sdk_output=full_output" in source
    assert "full_corpus_rollback_byte_parity" in source
    assert "SDK_CANONICAL_ARCHIVE_REL" in source


def test_g4_runtime_content_passes_while_provenance_stays_fail_closed() -> None:
    gate = load_evidence()["gate_g4"]

    assert gate["runtime_mirror_content_dry_run"] is True
    assert gate["runtime_mirror_consumer_ready"] is True
    assert gate["runtime_mirror_provenance_ready"] is False
    assert gate["runtime_mirror_closure_ready"] is False
    assert gate["runtime_mirror_expected_provenance_debt"] == [
        "routing mirror provenance source Git ref is unavailable",
        "routing mirror trust verdict is unavailable",
    ]
    assert gate["runtime_native_sdk_identity"] is False
    assert gate["live_runtime_verified_current"] is False


def test_owner_shortlist_contract_accepts_current_guard_kind() -> None:
    payload = json.loads(
        (CANONICAL_GENERATED_ROOT / "owner_layer_shortlist.min.json").read_text(
            encoding="utf-8"
        )
    )
    guard_hint = next(
        hint
        for hint in payload["hints"]
        if hint["shortlist_id"] == "risk-gate.capability-guard.primary"
    )

    parsed = RoutingOwnerLayerShortlistHint.model_validate(guard_hint)

    assert parsed.object_kind == "guard"
    assert parsed.owner_repo == "aoa-skills"
