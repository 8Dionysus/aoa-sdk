from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from aoa_sdk.control_plane.routing import candidate as candidate_module
from aoa_sdk.control_plane.routing.candidate import CANDIDATE_ASSEMBLY_FILES
from aoa_sdk.control_plane.routing.core import RouterError
from aoa_sdk.control_plane.routing.release_candidate import (
    G5_FALSE_AUTHORITY,
    RELEASE_CANDIDATE_PROFILE_ID,
    build_g5_release_candidate_bundle,
    load_g5_release_candidate_bundle,
    validate_g5_release_candidate_bundle,
    write_deterministic_release_archive,
)
from aoa_sdk.control_plane.routing.shadow import RoutingProducerInputs
from aoa_sdk.control_plane.routing.validator import get_schema_validator


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
OBSERVED_AT = datetime(2026, 7, 25, 16, 0, tzinfo=timezone.utc)


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


def build_fixture_release_candidate(
    monkeypatch: pytest.MonkeyPatch,
    output_root: Path,
):
    monkeypatch.setattr(
        candidate_module,
        "_require_exact_git_source_refs",
        lambda *_args, **_kwargs: None,
    )
    return build_g5_release_candidate_bundle(
        fixture_inputs(),
        output_root,
        predecessor_source_ref="f" * 64,
        sdk_source_ref=SOURCE_REFS["aoa-sdk"],
        input_source_refs=SOURCE_REFS,
        observed_at=OBSERVED_AT,
    )


def test_release_candidate_wraps_exact_nonpublishing_candidate_without_g5(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_release_candidate(
        monkeypatch,
        tmp_path / "release-candidate",
    )
    validate_g5_release_candidate_bundle(bundle, fixture_inputs())

    release_provenance = json.loads(
        bundle.provenance_path.read_text(encoding="utf-8")
    )
    release_manifest = json.loads(
        bundle.manifest_path.read_text(encoding="utf-8")
    )
    candidate_provenance = json.loads(
        bundle.candidate.provenance_path.read_text(encoding="utf-8")
    )
    candidate_manifest = json.loads(
        bundle.candidate.manifest_path.read_text(encoding="utf-8")
    )

    get_schema_validator(
        "routing-g5-release-candidate-provenance.schema.json"
    ).validate(release_provenance)
    assert candidate_provenance["publication_posture"] == "non_publishing_canary"
    assert candidate_manifest["mode"] == "os_abyss_local"
    assert release_provenance["publication_posture"] == "public_release_candidate"
    assert release_provenance["g5_authority"] == G5_FALSE_AUTHORITY
    assert release_manifest["mode"] == "github_release"
    assert (
        release_manifest["producer_admission_profile_id"]
        == RELEASE_CANDIDATE_PROFILE_ID
    )
    assert release_manifest["lifecycle"]["initial_state"] == "release-ready"
    assert len(release_manifest["artifact_subjects"]) == (
        len(CANDIDATE_ASSEMBLY_FILES) + 2
    )
    assert release_provenance["candidate_bundle"]["candidate_provenance_sha256"]
    assert release_provenance["candidate_bundle"]["candidate_manifest_sha256"]


def test_release_candidate_requests_public_release_but_denies_runtime_before_g5(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_release_candidate(
        monkeypatch,
        tmp_path / "release-candidate",
    )
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    commands = "\n".join(manifest["consumer_command"])

    assert "--trust-root-mode public_release" in commands
    assert "--consumer-intent release_consumer" in commands
    assert "--consumer-intent runtime " in commands
    assert "must deny before G5" in commands
    assert "canonical_producer_switch_authorized" not in commands


def test_release_candidate_archive_is_path_independent_and_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = build_fixture_release_candidate(monkeypatch, tmp_path / "first")
    second = build_fixture_release_candidate(monkeypatch, tmp_path / "second")
    first_archive = tmp_path / "one" / "first.tar.gz"
    second_archive = tmp_path / "two" / "second.tar.gz"

    first_digest = write_deterministic_release_archive(first, first_archive)
    second_digest = write_deterministic_release_archive(second, second_archive)

    assert first_digest == second_digest
    assert first_archive.read_bytes() == second_archive.read_bytes()


def test_release_candidate_rejects_release_envelope_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_release_candidate(
        monkeypatch,
        tmp_path / "release-candidate",
    )
    provenance = json.loads(bundle.provenance_path.read_text(encoding="utf-8"))
    provenance["g5_authority"]["sdk_canonical"] = True
    bundle.provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        RouterError,
        match="schema violations|authority stop line|content drifted",
    ):
        validate_g5_release_candidate_bundle(
            load_g5_release_candidate_bundle(bundle.output_root),
            fixture_inputs(),
        )


def test_release_candidate_rejects_extra_empty_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_release_candidate(
        monkeypatch,
        tmp_path / "release-candidate",
    )
    (bundle.output_root / "unexpected-empty").mkdir()

    with pytest.raises(RouterError, match="directory set drifted"):
        validate_g5_release_candidate_bundle(
            load_g5_release_candidate_bundle(bundle.output_root),
            fixture_inputs(),
        )


def test_release_candidate_output_must_stay_outside_producer_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        candidate_module,
        "_require_exact_git_source_refs",
        lambda *_args, **_kwargs: None,
    )
    inputs = fixture_inputs()

    with pytest.raises(RouterError, match="outside producer inputs"):
        build_g5_release_candidate_bundle(
            inputs,
            inputs.sdk_root / "release-candidate",
            predecessor_source_ref="f" * 64,
            sdk_source_ref=SOURCE_REFS["aoa-sdk"],
            input_source_refs=SOURCE_REFS,
            observed_at=OBSERVED_AT,
        )
