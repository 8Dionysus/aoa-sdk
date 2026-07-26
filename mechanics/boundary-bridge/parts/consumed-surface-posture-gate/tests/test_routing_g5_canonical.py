from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from aoa_sdk.control_plane.routing import candidate as candidate_module
from aoa_sdk.control_plane.routing import canonical as canonical_module
from aoa_sdk.control_plane.routing.candidate import CANDIDATE_ASSEMBLY_FILES
from aoa_sdk.control_plane.routing.canonical import (
    ARCHIVE_STOP_LINE,
    CANONICAL_PROFILE_ID,
    G5_CANONICAL_AUTHORITY,
    build_g5_canonical_bundle,
    load_g5_canonical_bundle,
    validate_g5_canonical_bundle,
    write_deterministic_canonical_archive,
)
from aoa_sdk.control_plane.routing.core import RouterError
from aoa_sdk.control_plane.routing.release_candidate import (
    build_g5_release_candidate_bundle,
    write_deterministic_release_archive,
)
from aoa_sdk.control_plane.routing.shadow import RoutingProducerInputs


FIXTURE_ROOT = Path(os.environ["AOA_ROUTING_HYDRATED_FIXTURE_ROOT"])
SOURCE_REFS = {
    "aoa-techniques": "1" * 64,
    "aoa-skills": "2" * 64,
    "aoa-evals": "3" * 64,
    "aoa-memo": "4" * 64,
    "aoa-stats": "5" * 64,
    "aoa-agents": "6" * 64,
    "Agents-of-Abyss": "7" * 64,
    "aoa-playbooks": "8" * 64,
    "aoa-kag": "9" * 64,
    "Tree-of-Sophia": "a" * 64,
    "aoa-sdk": "b" * 64,
    "Dionysus": "c" * 64,
    "8Dionysus": "d" * 64,
    "abyss-stack": "e" * 64,
}
PREDECESSOR_REF = "f" * 64
RUNTIME_CONSUMER_REF = "0" * 64
RELEASE_OBSERVED_AT = datetime(
    2026,
    7,
    25,
    18,
    0,
    tzinfo=timezone.utc,
)
CANONICAL_OBSERVED_AT = datetime(
    2026,
    7,
    26,
    2,
    30,
    tzinfo=timezone.utc,
)


def fixture_inputs() -> RoutingProducerInputs:
    return RoutingProducerInputs(
        techniques_root=FIXTURE_ROOT / "aoa-techniques",
        skills_root=FIXTURE_ROOT / "aoa-skills",
        evals_root=FIXTURE_ROOT / "aoa-evals",
        memo_root=FIXTURE_ROOT / "aoa-memo",
        stats_root=FIXTURE_ROOT / "aoa-stats",
        agents_root=FIXTURE_ROOT / "aoa-agents",
        aoa_root=FIXTURE_ROOT / "Agents-of-Abyss",
        playbooks_root=FIXTURE_ROOT / "aoa-playbooks",
        kag_root=FIXTURE_ROOT / "aoa-kag",
        tos_root=FIXTURE_ROOT / "Tree-of-Sophia",
        sdk_root=FIXTURE_ROOT / "aoa-sdk",
        source_route_root=FIXTURE_ROOT / "Dionysus",
        profile_root=FIXTURE_ROOT / "8Dionysus",
        abyss_stack_root=FIXTURE_ROOT / "abyss-stack",
    )


def _runtime_contract_root(tmp_path: Path) -> Path:
    root = tmp_path / "runtime-consumer"
    decision = (
        root
        / "docs"
        / "decisions"
        / "ABYSS-STACK-D-0086-receipt-bound-sdk-routing-cutover.md"
    )
    decision.parent.mkdir(parents=True)
    decision.write_text("# Receipt-bound SDK routing cutover\n", encoding="utf-8")
    return root


def _public_release_asset(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, str]:
    monkeypatch.setattr(
        candidate_module,
        "_require_exact_git_source_refs",
        lambda *_args, **_kwargs: None,
    )
    release = build_g5_release_candidate_bundle(
        fixture_inputs(),
        tmp_path / "release-candidate",
        predecessor_source_ref=PREDECESSOR_REF,
        sdk_source_ref=SOURCE_REFS["aoa-sdk"],
        input_source_refs=SOURCE_REFS,
        observed_at=RELEASE_OBSERVED_AT,
    )
    archive = (
        tmp_path / "aoa-sdk-routing-g5-release-candidate-v0.7.0.tar.gz"
    )
    digest = write_deterministic_release_archive(release, archive)
    return archive, f"sha256:{digest}"


def _build_canonical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    archive, digest = _public_release_asset(tmp_path, monkeypatch)
    runtime_root = _runtime_contract_root(tmp_path)
    monkeypatch.setattr(
        canonical_module,
        "_require_exact_checkout",
        lambda *_args, **_kwargs: None,
    )
    bundle = build_g5_canonical_bundle(
        fixture_inputs(),
        tmp_path / "canonical",
        predecessor_source_ref=PREDECESSOR_REF,
        sdk_source_ref=SOURCE_REFS["aoa-sdk"],
        sdk_version="0.8.0",
        input_source_refs=SOURCE_REFS,
        public_release_archive=archive,
        public_release_ref=(
            "https://github.com/8Dionysus/aoa-sdk/releases/tag/v0.7.0"
        ),
        public_release_source_ref=SOURCE_REFS["aoa-sdk"],
        public_release_asset_digest=digest,
        runtime_consumer_root=runtime_root,
        runtime_consumer_source_ref=RUNTIME_CONSUMER_REF,
        compatibility_started_on="2026-07-26",
        observed_at=CANONICAL_OBSERVED_AT,
    )
    return bundle, archive, runtime_root


def test_canonical_bundle_authorizes_g5_without_archive_or_live_cutover(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, archive, runtime_root = _build_canonical(tmp_path, monkeypatch)
    validate_g5_canonical_bundle(
        load_g5_canonical_bundle(bundle.output_root),
        fixture_inputs(),
        public_release_archive=archive,
        runtime_consumer_root=runtime_root,
    )

    receipt = json.loads(bundle.receipt_path.read_text(encoding="utf-8"))
    provenance = json.loads(bundle.provenance_path.read_text(encoding="utf-8"))
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    commands = "\n".join(manifest["consumer_command"])

    assert receipt["schema"] == "aoa_sdk_routing_g5_owner_switch_receipt_v1"
    assert receipt["status"] == "g5_switch_authorized"
    assert receipt["g5_authority"] == G5_CANONICAL_AUTHORITY
    assert receipt["archive_stop_line"] == ARCHIVE_STOP_LINE
    assert receipt["predecessor"]["rollback_posture"] == "retained"
    assert provenance["state"] == "sdk_canonical"
    assert provenance["runtime_consumer_contract"]["live_cutover_executed"] is False
    assert manifest["producer_admission_profile_id"] == CANONICAL_PROFILE_ID
    assert manifest["lifecycle"]["initial_state"] == "release-ready"
    assert "--consumer-intent runtime" in commands
    assert "--trust-root-mode public_release" in commands
    assert len(manifest["artifact_subjects"]) == (
        len(CANDIDATE_ASSEMBLY_FILES) + 2
    )


def test_canonical_bundle_preserves_every_public_release_assembly_byte(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, archive, _runtime_root = _build_canonical(tmp_path, monkeypatch)
    public_members = canonical_module._public_release_members(
        archive,
        expected_digest=f"sha256:{hashlib.sha256(archive.read_bytes()).hexdigest()}",
        release_source_ref=SOURCE_REFS["aoa-sdk"],
        predecessor_source_ref=PREDECESSOR_REF,
    )

    for relative in CANDIDATE_ASSEMBLY_FILES:
        assert (bundle.output_root / relative).read_bytes() == public_members[relative]


def test_canonical_archive_is_path_independent_and_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, _archive, _runtime_root = _build_canonical(tmp_path, monkeypatch)
    first = tmp_path / "one" / "canonical.tar.gz"
    second = tmp_path / "two" / "canonical.tar.gz"

    first_digest = write_deterministic_canonical_archive(bundle, first)
    second_digest = write_deterministic_canonical_archive(bundle, second)

    assert first_digest == second_digest
    assert first.read_bytes() == second.read_bytes()


def test_canonical_bundle_rejects_public_release_digest_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive, _digest = _public_release_asset(tmp_path, monkeypatch)
    runtime_root = _runtime_contract_root(tmp_path)
    monkeypatch.setattr(
        canonical_module,
        "_require_exact_checkout",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(RouterError, match="digest drifted"):
        build_g5_canonical_bundle(
            fixture_inputs(),
            tmp_path / "canonical",
            predecessor_source_ref=PREDECESSOR_REF,
            sdk_source_ref=SOURCE_REFS["aoa-sdk"],
            sdk_version="0.8.0",
            input_source_refs=SOURCE_REFS,
            public_release_archive=archive,
            public_release_ref="release:v0.7.0",
            public_release_source_ref=SOURCE_REFS["aoa-sdk"],
            public_release_asset_digest=f"sha256:{'0' * 64}",
            runtime_consumer_root=runtime_root,
            runtime_consumer_source_ref=RUNTIME_CONSUMER_REF,
            compatibility_started_on="2026-07-26",
            observed_at=CANONICAL_OBSERVED_AT,
        )


def test_canonical_bundle_rejects_archive_authority_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, archive, runtime_root = _build_canonical(tmp_path, monkeypatch)
    receipt = json.loads(bundle.receipt_path.read_text(encoding="utf-8"))
    receipt["g5_authority"]["archive_authorized"] = True
    bundle.receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RouterError,
        match="schema violations|authority drifted",
    ):
        validate_g5_canonical_bundle(
            load_g5_canonical_bundle(bundle.output_root),
            fixture_inputs(),
            public_release_archive=archive,
            runtime_consumer_root=runtime_root,
        )


def test_canonical_bundle_rejects_cross_owner_provenance_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, archive, runtime_root = _build_canonical(tmp_path, monkeypatch)
    provenance = json.loads(
        bundle.provenance_path.read_text(encoding="utf-8")
    )
    provenance["public_release_trust_root"]["release_ref"] = "release:other"
    bundle.provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RouterError, match="cross-owner binding drifted"):
        validate_g5_canonical_bundle(
            load_g5_canonical_bundle(bundle.output_root),
            fixture_inputs(),
            public_release_archive=archive,
            runtime_consumer_root=runtime_root,
        )


def test_canonical_bundle_rejects_extra_empty_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle, archive, runtime_root = _build_canonical(tmp_path, monkeypatch)
    (bundle.output_root / "unexpected-empty").mkdir()

    with pytest.raises(RouterError, match="directory set drifted"):
        validate_g5_canonical_bundle(
            load_g5_canonical_bundle(bundle.output_root),
            fixture_inputs(),
            public_release_archive=archive,
            runtime_consumer_root=runtime_root,
        )


def test_canonical_output_must_stay_outside_producer_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    archive, digest = _public_release_asset(tmp_path, monkeypatch)
    runtime_root = _runtime_contract_root(tmp_path)
    inputs = fixture_inputs()
    monkeypatch.setattr(
        canonical_module,
        "_require_exact_checkout",
        lambda *_args, **_kwargs: None,
    )

    with pytest.raises(RouterError, match="outside producer inputs"):
        build_g5_canonical_bundle(
            inputs,
            inputs.sdk_root / "canonical",
            predecessor_source_ref=PREDECESSOR_REF,
            sdk_source_ref=SOURCE_REFS["aoa-sdk"],
            sdk_version="0.8.0",
            input_source_refs=SOURCE_REFS,
            public_release_archive=archive,
            public_release_ref="release:v0.7.0",
            public_release_source_ref=SOURCE_REFS["aoa-sdk"],
            public_release_asset_digest=digest,
            runtime_consumer_root=runtime_root,
            runtime_consumer_source_ref=RUNTIME_CONSUMER_REF,
            compatibility_started_on="2026-07-26",
            observed_at=CANONICAL_OBSERVED_AT,
        )
