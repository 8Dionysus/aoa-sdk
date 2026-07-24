from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from aoa_sdk.control_plane.routing import candidate as candidate_module
from aoa_sdk.control_plane.routing.candidate import (
    CANDIDATE_ASSEMBLY_FILES,
    CANDIDATE_MANIFEST_REL,
    CANDIDATE_PROVENANCE_REL,
    RUNTIME_REQUIRED_FILES,
    build_g5_candidate_bundle,
    load_g5_candidate_bundle,
    validate_g5_candidate_bundle,
)
from aoa_sdk.control_plane.routing.core import RouterError
from aoa_sdk.control_plane.routing.identity import (
    SDK_G5_CANDIDATE,
    apply_routing_producer_posture,
)
from aoa_sdk.control_plane.routing.shadow import (
    RoutingProducerInputs,
    build_shadow_bundle,
)
from aoa_sdk.control_plane.routing.validator import (
    OUTPUT_SCHEMA_NAMES,
    get_schema_validator,
)


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
OBSERVED_AT = datetime(2026, 7, 24, 12, 0, tzinfo=timezone.utc)


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


def build_fixture_candidate(
    monkeypatch: pytest.MonkeyPatch,
    output_root: Path,
):
    monkeypatch.setattr(
        candidate_module,
        "_require_exact_git_source_refs",
        lambda *_args, **_kwargs: None,
    )
    return build_g5_candidate_bundle(
        fixture_inputs(),
        output_root,
        predecessor_source_ref="f" * 64,
        sdk_source_ref=SOURCE_REFS["aoa-sdk"],
        input_source_refs=SOURCE_REFS,
        observed_at=OBSERVED_AT,
    )


def changed_leaves(
    predecessor: object,
    candidate: object,
    path: tuple[str, ...] = (),
):
    if isinstance(predecessor, dict) and isinstance(candidate, dict):
        assert set(predecessor) == set(candidate)
        for key in sorted(predecessor):
            yield from changed_leaves(
                predecessor[key],
                candidate[key],
                (*path, key),
            )
        return
    if isinstance(predecessor, list) and isinstance(candidate, list):
        assert len(predecessor) == len(candidate)
        for index, (old_item, new_item) in enumerate(
            zip(predecessor, candidate, strict=True)
        ):
            yield from changed_leaves(
                old_item,
                new_item,
                (*path, str(index)),
            )
        return
    if predecessor != candidate:
        yield path, predecessor, candidate


def test_g5_candidate_builds_sdk_identity_without_switch_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_candidate(monkeypatch, tmp_path / "candidate")
    validate_g5_candidate_bundle(bundle, fixture_inputs())

    provenance = json.loads(bundle.provenance_path.read_text(encoding="utf-8"))
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    router = json.loads(
        (bundle.generated_root / "aoa_router.min.json").read_text(encoding="utf-8")
    )

    get_schema_validator(
        "routing-g5-candidate-provenance.schema.json"
    ).validate(provenance)
    assert set(bundle.artifact_sha256) == set(OUTPUT_SCHEMA_NAMES)
    assert len(CANDIDATE_ASSEMBLY_FILES) == 27
    assert set(RUNTIME_REQUIRED_FILES) <= set(CANDIDATE_ASSEMBLY_FILES)
    assert len(RUNTIME_REQUIRED_FILES) == 23
    assert router["artifact_identity"]["owner_repo"] == "aoa-sdk"
    assert router["artifact_identity"]["abi_epoch"] == (
        "aoa_routing_thin_router_v1"
    )
    assert provenance["current_canonical_producer"] == {
        "owner_repo": "aoa-routing",
        "source_ref": "f" * 64,
    }
    assert provenance["candidate_producer"]["owner_repo"] == "aoa-sdk"
    assert provenance["publication_posture"] == "non_publishing_canary"
    assert set(provenance["g5_authority"].values()) == {False}
    assert manifest["owner_repo"] == "aoa-sdk"
    assert manifest["artifact_class"] == "thin_routing_readmodel_bundle"
    assert manifest["lifecycle"]["initial_state"] == "candidate"
    assert (
        manifest["artifact_source"]["producer_source_ref"]
        == SOURCE_REFS["aoa-sdk"]
    )


def test_g5_candidate_changes_only_declared_producer_route_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate = build_fixture_candidate(monkeypatch, tmp_path / "candidate")
    shadow = build_shadow_bundle(
        fixture_inputs(),
        tmp_path / "shadow",
        predecessor_source_ref="f" * 64,
        sdk_source_ref=SOURCE_REFS["aoa-sdk"],
        input_source_refs=SOURCE_REFS,
        observed_at=OBSERVED_AT,
    )
    shadow_payloads = {
        filename: json.loads(
            (shadow.output_dir / filename).read_text(encoding="utf-8")
        )
        for filename in shadow.artifact_sha256
    }
    expected_candidate = apply_routing_producer_posture(
        shadow_payloads,
        SDK_G5_CANDIDATE,
    )
    actual_candidate = {
        filename: json.loads(
            (candidate.generated_root / filename).read_text(encoding="utf-8")
        )
        for filename in candidate.artifact_sha256
    }

    assert actual_candidate == expected_candidate
    assert len(
        actual_candidate["aoa_router.min.json"]["entries"]
    ) == len(shadow_payloads["aoa_router.min.json"]["entries"])


def test_g5_candidate_preserves_payload_except_producer_and_return_routes(
    tmp_path: Path,
) -> None:
    shadow = build_shadow_bundle(
        fixture_inputs(),
        tmp_path / "shadow",
        predecessor_source_ref="f" * 64,
        sdk_source_ref=SOURCE_REFS["aoa-sdk"],
        input_source_refs=SOURCE_REFS,
        observed_at=OBSERVED_AT,
    )
    predecessor = {
        filename: json.loads(
            (shadow.output_dir / filename).read_text(encoding="utf-8")
        )
        for filename in shadow.artifact_sha256
    }
    candidate = apply_routing_producer_posture(
        predecessor,
        SDK_G5_CANDIDATE,
    )
    changes = list(changed_leaves(predecessor, candidate))

    assert changes
    for path, old_value, new_value in changes:
        in_identity = (
            len(path) >= 2
            and path[0]
            in {
                "aoa_router.min.json",
                "federation_entrypoints.min.json",
            }
            and path[1] == "artifact_identity"
        )
        if in_identity:
            continue
        assert path[-1] in {
            "owner_repo",
            "source_repo",
            "surface_repo",
            "target_repo",
        }
        assert old_value == "aoa-routing"
        assert new_value == "aoa-sdk"


def test_g5_candidate_is_deterministic_at_a_fixed_observation_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = build_fixture_candidate(monkeypatch, tmp_path / "first")
    second = build_fixture_candidate(monkeypatch, tmp_path / "second")

    assert first.artifact_sha256 == second.artifact_sha256
    assert first.assembly_file_sha256 == second.assembly_file_sha256
    assert first.provenance_path.read_bytes() == second.provenance_path.read_bytes()
    assert first.manifest_path.read_bytes() == second.manifest_path.read_bytes()


def test_g5_candidate_rejects_post_build_substitution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_candidate(monkeypatch, tmp_path / "candidate")
    (bundle.generated_root / "aoa_router.min.json").write_text(
        "{}\n",
        encoding="utf-8",
    )

    with pytest.raises(RouterError, match="schema violation|does not match"):
        validate_g5_candidate_bundle(bundle, fixture_inputs())


def test_g5_candidate_rejects_unexpected_empty_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_candidate(monkeypatch, tmp_path / "candidate")
    (bundle.output_root / "unexpected-empty-directory").mkdir()

    with pytest.raises(RouterError, match="directory set drifted"):
        validate_g5_candidate_bundle(bundle, fixture_inputs())


def test_g5_candidate_requires_fresh_noncanonical_output_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "candidate"
    target.mkdir()
    (target / "stale").write_text("stale", encoding="utf-8")

    with pytest.raises(RouterError, match="absent or empty"):
        build_fixture_candidate(monkeypatch, target)

    with pytest.raises(RouterError, match="must not be named 'generated'"):
        build_fixture_candidate(monkeypatch, tmp_path / "generated")

    symlink_target = tmp_path / "symlink-target"
    symlink_target.mkdir()
    output_symlink = tmp_path / "candidate-link"
    output_symlink.symlink_to(symlink_target, target_is_directory=True)
    with pytest.raises(RouterError, match="must not be a symlink"):
        build_fixture_candidate(monkeypatch, output_symlink)


def test_g5_candidate_output_must_stay_outside_every_producer_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        candidate_module,
        "_require_exact_git_source_refs",
        lambda *_args, **_kwargs: None,
    )
    inputs = fixture_inputs()
    with pytest.raises(RouterError, match="outside producer inputs"):
        build_g5_candidate_bundle(
            inputs,
            inputs.sdk_root / "candidate-output",
            predecessor_source_ref="f" * 64,
            sdk_source_ref=SOURCE_REFS["aoa-sdk"],
            input_source_refs=SOURCE_REFS,
            observed_at=OBSERVED_AT,
        )


def test_g5_candidate_requires_sdk_source_ref_to_match_sdk_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        candidate_module,
        "_require_exact_git_source_refs",
        lambda *_args, **_kwargs: None,
    )
    with pytest.raises(RouterError, match="must match input_source_refs"):
        build_g5_candidate_bundle(
            fixture_inputs(),
            tmp_path / "candidate",
            predecessor_source_ref="f" * 64,
            sdk_source_ref="0" * 64,
            input_source_refs=SOURCE_REFS,
            observed_at=OBSERVED_AT,
        )


def test_g5_candidate_manifest_and_provenance_are_artifact_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_candidate(monkeypatch, tmp_path / "candidate")
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    subjects = {
        item["path"]
        for item in manifest["artifact_subjects"]
    }

    assert subjects == set(CANDIDATE_ASSEMBLY_FILES) | {
        CANDIDATE_PROVENANCE_REL.as_posix()
    }
    assert CANDIDATE_MANIFEST_REL.as_posix() not in subjects
    assert manifest["abi_subject"] == {
        "path": "generated/aoa_router.min.json",
        "artifact_identity_pointer": "/artifact_identity",
    }
    joined_commands = "\n".join(manifest["consumer_command"])
    assert "--source-repo aoa-sdk" in joined_commands
    assert "--consumer-intent runtime" in joined_commands
    assert "--trust-root-mode host_managed" in joined_commands
    assert "materialize-subjects" in joined_commands
    assert "trust-gate" in joined_commands
    assert "registry-latest" in joined_commands


def test_g5_candidate_rejects_manifest_command_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_candidate(monkeypatch, tmp_path / "candidate")
    manifest = json.loads(bundle.manifest_path.read_text(encoding="utf-8"))
    manifest["consumer_command"] = ["true"]
    bundle.manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RouterError, match="manifest content drifted"):
        validate_g5_candidate_bundle(bundle, fixture_inputs())


def test_g5_candidate_rejects_non_string_source_refs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = build_fixture_candidate(monkeypatch, tmp_path / "candidate")
    provenance = json.loads(bundle.provenance_path.read_text(encoding="utf-8"))
    provenance["input_source_refs"]["aoa-sdk"] = 7
    bundle.provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(RouterError, match="full lowercase Git object ID"):
        validate_g5_candidate_bundle(
            load_g5_candidate_bundle(bundle.output_root),
            fixture_inputs(),
        )


def test_exact_git_source_ref_gate_rejects_dirty_or_mismatched_input(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "AoA Test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "aoa@example.invalid"],
        check=True,
    )
    (repo / "input.txt").write_text("input\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "input.txt"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "fixture"],
        check=True,
    )
    source_ref = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    inputs = RoutingProducerInputs(
        techniques_root=repo,
        skills_root=repo,
        evals_root=repo,
        memo_root=repo,
        stats_root=repo,
        agents_root=repo,
        aoa_root=repo,
        playbooks_root=repo,
        kag_root=repo,
        tos_root=repo,
        sdk_root=repo,
        source_route_root=repo,
        profile_root=repo,
        abyss_stack_root=repo,
    )
    refs = {name: source_ref for name in inputs.source_roots()}

    candidate_module._require_exact_git_source_refs(inputs, refs)
    with pytest.raises(RouterError, match="does not match"):
        candidate_module._require_exact_git_source_refs(
            inputs,
            {**refs, "aoa-sdk": "0" * 40},
        )
    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(RouterError, match="must be clean"):
        candidate_module._require_exact_git_source_refs(inputs, refs)
