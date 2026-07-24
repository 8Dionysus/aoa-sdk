from __future__ import annotations

import io
import json
import os
import tarfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from routing_shadow_fixture_archive import validated_members

from aoa_sdk.control_plane.routing.core import RouterError
from aoa_sdk.control_plane.routing.shadow import (
    RoutingProducerInputs,
    build_shadow_bundle,
    validate_shadow_bundle,
)
from aoa_sdk.control_plane.routing.validator import (
    OUTPUT_SCHEMA_NAMES,
    SCHEMA_ROOT,
    get_schema_validator,
)


PART_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(os.environ["AOA_ROUTING_HYDRATED_FIXTURE_ROOT"])
EXPECTED_HASHES_PATH = (
    PART_ROOT / "fixtures" / "routing-shadow" / "expected-hashes.json"
)
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


def build_fixture_bundle(output_dir: Path):
    return build_shadow_bundle(
        fixture_inputs(),
        output_dir,
        predecessor_source_ref="f" * 64,
        sdk_source_ref="0" * 64,
        input_source_refs=SOURCE_REFS,
        observed_at=datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc),
    )


def test_shadow_bundle_builds_valid_non_publishing_dual_provenance(
    tmp_path: Path,
) -> None:
    bundle = build_fixture_bundle(tmp_path / "shadow")
    validate_shadow_bundle(bundle, fixture_inputs())

    provenance = json.loads(bundle.provenance_path.read_text(encoding="utf-8"))
    get_schema_validator("routing-shadow-provenance.schema.json").validate(provenance)

    assert len(bundle.artifact_sha256) == 14
    assert set(bundle.artifact_sha256) == set(OUTPUT_SCHEMA_NAMES)
    assert provenance["state"] == "sdk_shadow"
    assert provenance["publication_posture"] == "non_publishing"
    assert provenance["canonical_producer"]["owner_repo"] == "aoa-routing"
    assert provenance["shadow_producer"]["owner_repo"] == "aoa-sdk"
    assert provenance["input_source_refs"] == SOURCE_REFS
    expected_hashes = json.loads(EXPECTED_HASHES_PATH.read_text(encoding="utf-8"))
    assert bundle.artifact_sha256 == expected_hashes["output_sha256"]


def test_shadow_bundle_is_deterministic_at_a_fixed_observation_time(
    tmp_path: Path,
) -> None:
    first = build_fixture_bundle(tmp_path / "first")
    second = build_fixture_bundle(tmp_path / "second")

    assert first.artifact_sha256 == second.artifact_sha256
    assert first.provenance_path.read_bytes() == second.provenance_path.read_bytes()
    for filename in first.artifact_sha256:
        assert (first.output_dir / filename).read_bytes() == (
            second.output_dir / filename
        ).read_bytes()


def test_shadow_bundle_rejects_post_build_substitution(tmp_path: Path) -> None:
    bundle = build_fixture_bundle(tmp_path / "shadow")
    target = bundle.output_dir / "aoa_router.min.json"
    target.write_text("{}\n", encoding="utf-8")

    with pytest.raises(RouterError, match="does not match|schema violation"):
        validate_shadow_bundle(bundle, fixture_inputs())


@pytest.mark.parametrize(
    ("field", "replacement", "message"),
    [
        (
            "shadow_producer",
            {
                "owner_repo": "aoa-routing",
                "source_ref": "0" * 64,
                "implementation": "aoa_sdk.control_plane.routing",
            },
            "SDK producer drifted",
        ),
        (
            "input_source_refs",
            {**SOURCE_REFS, "aoa-kag": "a" * 64},
            "input source refs drifted",
        ),
    ],
)
def test_shadow_bundle_rejects_provenance_substitution(
    tmp_path: Path,
    field: str,
    replacement: object,
    message: str,
) -> None:
    bundle = build_fixture_bundle(tmp_path / "shadow")
    provenance = json.loads(bundle.provenance_path.read_text(encoding="utf-8"))
    provenance[field] = replacement
    bundle.provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RouterError, match=message):
        validate_shadow_bundle(bundle, fixture_inputs())


def test_shadow_bundle_requires_exact_owner_source_refs(tmp_path: Path) -> None:
    incomplete_refs = dict(SOURCE_REFS)
    incomplete_refs.pop("aoa-kag")

    with pytest.raises(RouterError, match="must match producer inputs"):
        build_shadow_bundle(
            fixture_inputs(),
            tmp_path / "shadow",
            predecessor_source_ref="f" * 64,
            sdk_source_ref="0" * 64,
            input_source_refs=incomplete_refs,
        )


def test_shadow_bundle_accepts_full_sha1_git_object_ids(tmp_path: Path) -> None:
    sha1_refs = {name: f"{index:x}" * 40 for index, name in enumerate(SOURCE_REFS, 1)}
    bundle = build_shadow_bundle(
        fixture_inputs(),
        tmp_path / "shadow",
        predecessor_source_ref="f" * 40,
        sdk_source_ref="0" * 40,
        input_source_refs=sha1_refs,
    )

    validate_shadow_bundle(bundle, fixture_inputs())


def test_shadow_bundle_rejects_abbreviated_git_object_id(tmp_path: Path) -> None:
    with pytest.raises(RouterError, match="full lowercase Git object ID"):
        build_shadow_bundle(
            fixture_inputs(),
            tmp_path / "shadow",
            predecessor_source_ref="f" * 12,
            sdk_source_ref="0" * 40,
            input_source_refs=SOURCE_REFS,
        )


@pytest.mark.parametrize("invalid_ref", ["F" * 40, f"{'f' * 40} "])
def test_shadow_bundle_rejects_normalized_but_noncanonical_git_object_ids(
    tmp_path: Path,
    invalid_ref: str,
) -> None:
    with pytest.raises(RouterError, match="full lowercase Git object ID"):
        build_shadow_bundle(
            fixture_inputs(),
            tmp_path / "shadow",
            predecessor_source_ref=invalid_ref,
            sdk_source_ref="0" * 40,
            input_source_refs=SOURCE_REFS,
        )


def test_shadow_bundle_refuses_any_canonical_looking_generated_directory(
    tmp_path: Path,
) -> None:
    from aoa_sdk.control_plane.routing.core import REPO_ROOT

    for target in (REPO_ROOT / "generated", tmp_path / "generated"):
        with pytest.raises(RouterError, match="must not be named 'generated'"):
            build_shadow_bundle(
                fixture_inputs(),
                target,
                predecessor_source_ref="f" * 64,
                sdk_source_ref="0" * 64,
                input_source_refs=SOURCE_REFS,
            )


def test_shadow_bundle_requires_a_fresh_empty_output_directory(
    tmp_path: Path,
) -> None:
    target = tmp_path / "shadow"
    target.mkdir()
    (target / "stale.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(RouterError, match="absent or empty"):
        build_fixture_bundle(target)


def test_shadow_bundle_rejects_extra_files_after_construction(
    tmp_path: Path,
) -> None:
    bundle = build_fixture_bundle(tmp_path / "shadow")
    (bundle.output_dir / "unexpected.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(RouterError, match="file set drifted"):
        validate_shadow_bundle(bundle, fixture_inputs())


def test_shadow_bundle_enforces_provenance_date_time_format(
    tmp_path: Path,
) -> None:
    bundle = build_fixture_bundle(tmp_path / "shadow")
    provenance = json.loads(bundle.provenance_path.read_text(encoding="utf-8"))
    provenance["observed_at"] = "not-a-date-time"
    bundle.provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RouterError, match="RFC 3339"):
        validate_shadow_bundle(bundle, fixture_inputs())


def test_packaged_schema_family_covers_every_output_and_sidecar() -> None:
    packaged = {path.name for path in SCHEMA_ROOT.glob("*.json")}

    assert set(Path(schema_ref).name for schema_ref in OUTPUT_SCHEMA_NAMES.values()) <= packaged
    assert "router-entry.schema.json" in packaged
    assert "quest_dispatch_hint.schema.json" in packaged
    assert "routing-shadow-provenance.schema.json" in packaged


@pytest.mark.parametrize("unsafe_kind", ["parent_traversal", "symlink"])
def test_fixture_archive_materializer_rejects_unsafe_members(
    tmp_path: Path,
    unsafe_kind: str,
) -> None:
    archive_path = tmp_path / f"{unsafe_kind}.tar.gz"
    with tarfile.open(archive_path, mode="w:gz") as archive:
        if unsafe_kind == "parent_traversal":
            payload = b"escape"
            member = tarfile.TarInfo("../escape")
            member.size = len(payload)
            archive.addfile(member, io.BytesIO(payload))
        else:
            member = tarfile.TarInfo("fixture-link")
            member.type = tarfile.SYMTYPE
            member.linkname = "target"
            archive.addfile(member)

    target = tmp_path / "target"
    target.mkdir()
    with tarfile.open(archive_path, mode="r:gz") as archive:
        with pytest.raises(RuntimeError, match="unsafe|unsupported"):
            validated_members(archive, target)
