#!/usr/bin/env python3
"""Verify the released routing shadow through the complete G4 evidence chain."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


PART_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PART_ROOT.parents[3]
EVIDENCE_PATH = PART_ROOT / "evidence" / "routing-succession-g4-evidence.json"
RUNTIME_DOC_FIXTURE_ROOT = PART_ROOT / "fixtures" / "routing-runtime-mirror"
PREDECESSOR_PIN_REL = Path(
    "mechanics/release-support/parts/release-gate-routing/config/sdk_shadow_release_pin.json"
)
PREDECESSOR_PIN_SCHEMA_REL = Path(
    "mechanics/release-support/parts/release-gate-routing/schemas/sdk-shadow-release-pin.schema.json"
)
PREDECESSOR_PROBE_REL = Path(
    "mechanics/release-support/parts/release-gate-routing/scripts/sdk_shadow_release_probe.py"
)
SDK_FIXTURE_ARCHIVE_REL = Path(
    "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/"
    "fixtures/routing-shadow/inputs.tar.gz"
)
SDK_CANONICAL_ARCHIVE_REL = Path(
    "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/"
    "fixtures/routing-shadow/canonical-generated.tar.gz"
)
SDK_TRUST_VALIDATOR_REL = Path(
    "mechanics/release-support/parts/release-audit-publish-helper/"
    "scripts/validate_abyss_machine_package_artifact_bundle.py"
)
SDK_DISTRIBUTION_MANIFEST_REL = Path(
    "sdk/distribution/manifests/python_distribution.bundle.json"
)
ABYSS_ROUTING_CONFIG_REL = Path(
    "config-templates/Configs/federation/aoa-routing.yaml"
)
ABYSS_SYNC_WRAPPER_REL = Path(
    "mechanics/federation-seams/parts/sync-wrapper/aoa_sync_federation_surfaces.sh"
)
ABYSS_ROUTE_API_REL = Path("config-templates/Services/route-api/app/main.py")
FULL_CORPUS_REPOSITORIES = (
    "aoa-techniques",
    "aoa-skills",
    "aoa-evals",
    "aoa-memo",
    "aoa-stats",
    "aoa-agents",
    "Agents-of-Abyss",
    "aoa-playbooks",
    "aoa-kag",
    "Tree-of-Sophia",
    "aoa-sdk",
    "Dionysus",
    "8Dionysus",
    "abyss-stack",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build and trust-check the exact SDK shadow release, compare the "
            "predecessor, and load an isolated abyss-stack routing mirror."
        )
    )
    parser.add_argument("--sdk-release-root", type=Path, required=True)
    parser.add_argument("--predecessor-root", type=Path, required=True)
    parser.add_argument("--abyss-stack-root", type=Path, required=True)
    parser.add_argument("--abyss-machine-root", type=Path, required=True)
    parser.add_argument(
        "--input-workspace-root",
        type=Path,
        required=True,
        help=(
            "Git repository parent for the pinned full-corpus owner inputs; "
            "repository directory names must match the evidence pin names."
        ),
    )
    parser.add_argument(
        "--abyss-stack-input-root",
        type=Path,
        required=True,
        help=(
            "Git repository that contains the pinned abyss-stack full-corpus "
            "input commit. It is read through git archive and is never mutated."
        ),
    )
    return parser.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected a JSON object: {path}")
    return payload


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(
    command: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=capture_output,
        text=True,
    )


def _git_output(root: Path, *args: str) -> str:
    return _run(
        ["git", *args],
        root,
        capture_output=True,
    ).stdout.strip()


def _require_exact_checkout(root: Path, expected_ref: str, label: str) -> None:
    if not root.is_dir():
        raise RuntimeError(f"{label} root is missing: {root}")
    observed = _git_output(root, "rev-parse", "HEAD")
    if observed != expected_ref:
        raise RuntimeError(
            f"{label} source ref mismatch: expected {expected_ref}, observed {observed}"
        )
    tracked_status = _git_output(
        root,
        "status",
        "--porcelain",
        "--untracked-files=no",
    )
    if tracked_status:
        raise RuntimeError(f"{label} checkout has tracked modifications")


def _require_annotated_release(
    sdk_root: Path,
    release: dict[str, Any],
) -> None:
    _require_exact_checkout(sdk_root, str(release["source_ref"]), "aoa-sdk release")
    tag_ref = f"refs/tags/{release['tag']}"
    if _git_output(sdk_root, "cat-file", "-t", tag_ref) != "tag":
        raise RuntimeError(f"SDK release tag is not annotated: {release['tag']}")
    if _git_output(sdk_root, "rev-parse", tag_ref) != release["tag_object_ref"]:
        raise RuntimeError("SDK annotated tag object differs from the G4 pin")
    if _git_output(sdk_root, "rev-parse", f"{tag_ref}^{{}}") != release["source_ref"]:
        raise RuntimeError("SDK annotated tag does not peel to the G4 source pin")


def _validate_predecessor_pin(
    predecessor_root: Path,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    pin_path = predecessor_root / PREDECESSOR_PIN_REL
    pin = _read_json(pin_path)
    schema = _read_json(predecessor_root / PREDECESSOR_PIN_SCHEMA_REL)
    errors = sorted(
        Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        ).iter_errors(pin),
        key=lambda error: list(error.path),
    )
    if errors:
        rendered = "; ".join(error.message for error in errors)
        raise RuntimeError(f"invalid predecessor SDK release pin: {rendered}")
    if _sha256(pin_path) != evidence["pins"]["predecessor"]["release_pin_sha256"]:
        raise RuntimeError("predecessor SDK release pin hash differs from G4 evidence")
    release = evidence["pins"]["sdk_release"]
    expected_release_fields = {
        "tag": release["tag"],
        "tag_object_ref": release["tag_object_ref"],
        "source_ref": release["source_ref"],
        "version": release["version"],
        "release_url": release["release_url"],
    }
    for field, value in expected_release_fields.items():
        if pin["sdk_release"].get(field) != value:
            raise RuntimeError(f"predecessor release pin field drifted: {field}")
    observed_artifact = pin["sdk_release"]["artifact_observation"]
    expected_artifact_fields = {
        "release_artifacts_run_id": release["release_artifacts_run_id"],
        "artifact_id": release["artifact_id"],
        "artifact_digest_sha256": release["artifact_digest_sha256"],
        "wheel_sha256": release["wheel_sha256"],
        "sdist_sha256": release["sdist_sha256"],
    }
    for field, value in expected_artifact_fields.items():
        if observed_artifact.get(field) != value:
            raise RuntimeError(f"predecessor artifact observation drifted: {field}")
    return pin


def _temporary_root() -> Path | None:
    configured = os.environ.get("ABYSS_MACHINE_TMP_ROOT")
    if configured:
        root = Path(configured).expanduser()
        if root.is_dir():
            return root
    host_tmp = Path("/srv/abyss-machine/tmp")
    return host_tmp if host_tmp.is_dir() else None


def _clone_release_source(source_root: Path, target: Path, source_ref: str) -> None:
    _run(
        [
            "git",
            "clone",
            "--no-local",
            "--quiet",
            str(source_root),
            str(target),
        ],
        target.parent,
    )
    _run(["git", "checkout", "--quiet", source_ref], target)
    _require_exact_checkout(target, source_ref, "temporary aoa-sdk release clone")


def _build_release_distribution(
    release_clone: Path,
    version: str,
) -> tuple[Path, Path]:
    dist = release_clone / "dist"
    _run(
        [
            sys.executable,
            "-m",
            "build",
            "--outdir",
            str(dist),
        ],
        release_clone,
    )
    wheels = sorted(dist.glob(f"aoa_sdk-{version}-*.whl"))
    sdists = sorted(dist.glob(f"aoa_sdk-{version}.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(
            f"expected one wheel and one sdist, found {len(wheels)} and {len(sdists)}"
        )
    return wheels[0], sdists[0]


def _create_installed_environment(
    wheel: Path,
    environment_root: Path,
) -> tuple[Path, dict[str, str]]:
    venv.EnvBuilder(with_pip=True, clear=False).create(environment_root)
    python = environment_root / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    _run(
        [
            str(python),
            "-m",
            "pip",
            "--disable-pip-version-check",
            "install",
            str(wheel),
        ],
        environment_root.parent,
        env=environment,
    )
    return python, environment


def _safe_materialize_fixture(archive_path: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    seen: set[PurePosixPath] = set()
    with tarfile.open(archive_path, mode="r:gz") as archive:
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            if name == PurePosixPath("."):
                if not member.isdir():
                    raise RuntimeError("fixture archive root member must be a directory")
                continue
            if (
                name.is_absolute()
                or not name.parts
                or any(part in {"", ".", ".."} for part in name.parts)
            ):
                raise RuntimeError(f"unsafe fixture archive path: {member.name}")
            if name in seen:
                raise RuntimeError(f"duplicate fixture archive path: {member.name}")
            seen.add(name)
            if member.issym() or member.islnk() or not (
                member.isdir() or member.isfile()
            ):
                raise RuntimeError(
                    f"unsupported fixture archive member: {member.name}"
                )
            destination = target.joinpath(*name.parts)
            resolved = destination.resolve()
            if target.resolve() not in resolved.parents:
                raise RuntimeError(f"fixture archive path escapes target: {member.name}")
            if member.isdir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RuntimeError(f"unable to read fixture member: {member.name}")
            with source, destination.open("xb") as output:
                shutil.copyfileobj(source, output)


def _materialize_git_tree(
    repository_root: Path,
    source_ref: str,
    target: Path,
) -> list[str]:
    if not repository_root.is_dir():
        raise RuntimeError(f"full-corpus input repository is missing: {repository_root}")
    object_check = subprocess.run(
        ["git", "cat-file", "-e", f"{source_ref}^{{commit}}"],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if object_check.returncode != 0:
        raise RuntimeError(
            f"full-corpus input ref is unavailable in {repository_root}: {source_ref}"
        )
    target.mkdir(parents=True, exist_ok=False)
    process = subprocess.Popen(
        ["git", "archive", "--format=tar", source_ref],
        cwd=repository_root,
        stdout=subprocess.PIPE,
    )
    if process.stdout is None:
        raise RuntimeError(f"could not read git archive from {repository_root}")
    skipped_symlinks: list[str] = []
    try:
        with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
            for member in archive:
                name = PurePosixPath(member.name)
                if (
                    name.is_absolute()
                    or not name.parts
                    or any(part in {"", ".", ".."} for part in name.parts)
                ):
                    raise RuntimeError(
                        f"unsafe full-corpus archive path: {member.name}"
                    )
                destination = target.joinpath(*name.parts)
                resolved = destination.resolve()
                if target.resolve() not in resolved.parents:
                    raise RuntimeError(
                        f"full-corpus archive path escapes target: {member.name}"
                    )
                if member.isdir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                if member.issym() or member.islnk():
                    if name.parts[:2] != (".agents", "skills"):
                        raise RuntimeError(
                            "unexpected full-corpus symlink outside the non-input "
                            f".agents/skills lane: {member.name}"
                        )
                    skipped_symlinks.append(name.as_posix())
                    continue
                if not member.isfile():
                    raise RuntimeError(
                        f"unsupported full-corpus archive member: {member.name}"
                    )
                destination.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise RuntimeError(
                        f"unable to read full-corpus archive member: {member.name}"
                    )
                with source, destination.open("xb") as output:
                    shutil.copyfileobj(source, output)
    except Exception:
        process.kill()
        process.wait()
        raise
    if process.wait() != 0:
        raise RuntimeError(f"git archive failed for {repository_root}@{source_ref}")
    return skipped_symlinks


def _materialize_full_corpus(
    *,
    evidence: dict[str, Any],
    workspace_root: Path,
    abyss_stack_input_root: Path,
    target: Path,
) -> dict[str, list[str]]:
    input_refs = evidence["pins"]["full_corpus"]["input_source_refs"]
    if not isinstance(input_refs, dict):
        raise RuntimeError("G4 full-corpus input refs must be an object")
    if tuple(input_refs) != FULL_CORPUS_REPOSITORIES:
        raise RuntimeError(
            "G4 full-corpus input refs differ from the producer root contract"
        )
    target.mkdir(parents=True, exist_ok=False)
    skipped: dict[str, list[str]] = {}
    for repository_name, source_ref in input_refs.items():
        repository_root = (
            abyss_stack_input_root
            if repository_name == "abyss-stack"
            else workspace_root / repository_name
        )
        skipped_paths = _materialize_git_tree(
            repository_root.resolve(),
            str(source_ref),
            target / repository_name,
        )
        if skipped_paths:
            skipped[repository_name] = skipped_paths
    return skipped


def _probe_installed_shadow(
    *,
    python: Path,
    environment: dict[str, str],
    predecessor_root: Path,
    release_clone: Path,
    fixture_root: Path,
    output_dir: Path,
    predecessor_ref: str,
) -> dict[str, Any]:
    completed = _run(
        [
            str(python),
            str(predecessor_root / PREDECESSOR_PROBE_REL),
            "--fixture-root",
            str(fixture_root),
            "--output-dir",
            str(output_dir),
            "--pin",
            str(predecessor_root / PREDECESSOR_PIN_REL),
            "--sdk-checkout",
            str(release_clone),
            "--predecessor-source-ref",
            predecessor_ref,
        ],
        output_dir.parent,
        env=environment,
        capture_output=True,
    )
    report = json.loads(completed.stdout)
    if not isinstance(report, dict):
        raise RuntimeError("installed SDK probe did not return an object")
    return report


def _predecessor_build_args(
    fixture_root: Path,
    output_dir: Path,
) -> list[str]:
    roots = tuple(
        zip(
            (
                "techniques",
                "skills",
                "evals",
                "memo",
                "stats",
                "agents",
                "aoa",
                "playbooks",
                "kag",
                "tos",
                "sdk",
                "source-route",
                "profile",
                "abyss-stack",
            ),
            FULL_CORPUS_REPOSITORIES,
            strict=True,
        )
    )
    result: list[str] = []
    for argument, directory in roots:
        result.extend([f"--{argument}-root", str(fixture_root / directory)])
    result.extend(["--generated-dir", str(output_dir)])
    return result


def _artifact_hashes(
    output_dir: Path,
    artifact_names: list[str],
) -> dict[str, str]:
    return {
        name: _sha256(output_dir / name)
        for name in artifact_names
    }


def _require_exact_artifact_set(
    output_dir: Path,
    artifact_names: list[str],
    label: str,
) -> None:
    observed = {
        path.name
        for path in output_dir.iterdir()
        if path.is_file()
    }
    expected = set(artifact_names)
    if observed != expected:
        raise RuntimeError(
            f"{label} artifact set drifted: "
            f"missing={sorted(expected - observed)}, "
            f"unexpected={sorted(observed - expected)}"
        )


def _build_installed_outputs(
    *,
    python: Path,
    environment: dict[str, str],
    input_root: Path,
    output_dir: Path,
) -> None:
    _run(
        [
            str(python),
            "-m",
            "aoa_sdk.control_plane.routing.producer",
            *_predecessor_build_args(input_root, output_dir),
        ],
        output_dir.parent,
        env=environment,
    )


def _verify_predecessor_rollback(
    predecessor_root: Path,
    fixture_root: Path,
    output_dir: Path,
    baseline_ref: str,
    artifact_names: list[str],
    sdk_output: Path,
) -> dict[str, str]:
    producer_paths = [
        "routing/core/schemas",
        "scripts/build_router.py",
        "scripts/router_core.py",
    ]
    comparison = subprocess.run(
        ["git", "diff", "--quiet", baseline_ref, "--", *producer_paths],
        cwd=predecessor_root,
        check=False,
    )
    if comparison.returncode != 0:
        raise RuntimeError("predecessor producer changed after the G4 baseline")
    _run(
        [
            sys.executable,
            "scripts/build_router.py",
            *_predecessor_build_args(fixture_root, output_dir),
        ],
        predecessor_root,
    )
    mismatches = [
        name
        for name in artifact_names
        if (output_dir / name).read_bytes() != (sdk_output / name).read_bytes()
    ]
    if mismatches:
        raise RuntimeError(f"rollback producer byte mismatches: {mismatches}")
    return {
        name: _sha256(output_dir / name)
        for name in artifact_names
    }


def _verify_full_corpus(
    *,
    evidence: dict[str, Any],
    release_clone: Path,
    predecessor_root: Path,
    python: Path,
    environment: dict[str, str],
    input_root: Path,
    temporary_root: Path,
    artifact_names: list[str],
) -> tuple[Path, dict[str, str]]:
    full_pin = evidence["pins"]["full_corpus"]
    if Path(full_pin["canonical_archive_path"]) != SDK_CANONICAL_ARCHIVE_REL:
        raise RuntimeError("canonical generated fixture path differs from G4 evidence")
    if full_pin["canonical_predecessor_ref"] != evidence["pins"]["predecessor"][
        "implementation_baseline_ref"
    ]:
        raise RuntimeError("full-corpus predecessor authority pin drifted")
    canonical_archive = release_clone / SDK_CANONICAL_ARCHIVE_REL
    if _sha256(canonical_archive) != full_pin["canonical_archive_sha256"]:
        raise RuntimeError("canonical generated fixture archive differs from G4 evidence")
    canonical_root = temporary_root / "canonical-generated"
    _safe_materialize_fixture(canonical_archive, canonical_root)
    _require_exact_artifact_set(
        canonical_root,
        artifact_names,
        "canonical generated fixture",
    )
    expected_hashes = full_pin["output_sha256"]
    if _artifact_hashes(canonical_root, artifact_names) != expected_hashes:
        raise RuntimeError("canonical generated fixture hashes differ from G4 evidence")

    predecessor_checked_in = predecessor_root / "generated"
    checked_in_hashes = _artifact_hashes(predecessor_checked_in, artifact_names)
    if checked_in_hashes != expected_hashes:
        raise RuntimeError(
            "current predecessor generated artifacts differ from the G4 canonical pin"
        )

    first_output = temporary_root / "sdk-full-corpus-first"
    second_output = temporary_root / "sdk-full-corpus-second"
    _build_installed_outputs(
        python=python,
        environment=environment,
        input_root=input_root,
        output_dir=first_output,
    )
    _build_installed_outputs(
        python=python,
        environment=environment,
        input_root=input_root,
        output_dir=second_output,
    )
    for label, output_dir in (
        ("first installed full-corpus build", first_output),
        ("second installed full-corpus build", second_output),
    ):
        _require_exact_artifact_set(output_dir, artifact_names, label)
        if _artifact_hashes(output_dir, artifact_names) != expected_hashes:
            raise RuntimeError(f"{label} hashes differ from the G4 canonical pin")
    byte_mismatches = [
        name
        for name in artifact_names
        if (first_output / name).read_bytes()
        != (second_output / name).read_bytes()
        or (first_output / name).read_bytes()
        != (canonical_root / name).read_bytes()
    ]
    if byte_mismatches:
        raise RuntimeError(
            f"installed full-corpus canonical byte mismatches: {byte_mismatches}"
        )

    rollback_hashes = _verify_predecessor_rollback(
        predecessor_root,
        input_root,
        temporary_root / "predecessor-full-corpus",
        evidence["pins"]["predecessor"]["implementation_baseline_ref"],
        artifact_names,
        first_output,
    )
    if rollback_hashes != expected_hashes:
        raise RuntimeError(
            "predecessor full-corpus rollback hashes differ from the G4 canonical pin"
        )
    router = _read_json(first_output / "aoa_router.min.json")
    route_count = len(router.get("entries", []))
    if route_count != evidence["verification_matrix"]["route_count"]:
        raise RuntimeError(
            f"full-corpus build produced {route_count} routes instead of the G4 pin"
        )
    return first_output, expected_hashes


def _installed_schema_root(
    python: Path,
    environment: dict[str, str],
    cwd: Path,
) -> Path:
    completed = _run(
        [
            str(python),
            "-c",
            (
                "from aoa_sdk.control_plane.routing.validator import SCHEMA_ROOT;"
                "print(SCHEMA_ROOT.resolve())"
            ),
        ],
        cwd,
        env=environment,
        capture_output=True,
    )
    schema_root = Path(completed.stdout.strip())
    if not schema_root.is_dir() or Path(python).resolve().parents[1] not in schema_root.parents:
        raise RuntimeError("routing schemas were not loaded from the fresh environment")
    return schema_root


def _git_blob(predecessor_root: Path, source_ref: str, rel_path: str) -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{source_ref}:{rel_path}"],
        cwd=predecessor_root,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _assemble_runtime_source(
    *,
    evidence: dict[str, Any],
    predecessor_root: Path,
    sdk_output: Path,
    schema_root: Path,
    target: Path,
) -> dict[str, str]:
    target.mkdir(parents=True, exist_ok=False)
    contract = evidence["runtime_mirror_contract"]
    historical_ref = evidence["pins"]["predecessor"][
        "historical_runtime_docs_ref"
    ]
    observed_hashes: dict[str, str] = {}
    for rel_path in contract["required_files"]:
        destination = target / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if rel_path.startswith("generated/"):
            source = sdk_output / Path(rel_path).name
            shutil.copy2(source, destination)
        elif rel_path.startswith("schemas/"):
            source = schema_root / Path(rel_path).name
            shutil.copy2(source, destination)
        elif rel_path.startswith("docs/"):
            fixture = RUNTIME_DOC_FIXTURE_ROOT / Path(rel_path).name
            historical_bytes = _git_blob(predecessor_root, historical_ref, rel_path)
            if fixture.read_bytes() != historical_bytes:
                raise RuntimeError(
                    f"runtime compatibility doc fixture differs from {historical_ref}:{rel_path}"
                )
            expected_hash = contract["historical_compatibility_docs"][rel_path]
            if _sha256_bytes(historical_bytes) != expected_hash:
                raise RuntimeError(
                    f"runtime compatibility doc source hash drifted: {rel_path}"
                )
            shutil.copy2(fixture, destination)
        else:
            raise RuntimeError(f"unsupported runtime mirror path: {rel_path}")
        if destination.is_symlink() or not destination.is_file():
            raise RuntimeError(f"runtime candidate entry is not a regular file: {rel_path}")
        observed_hashes[rel_path] = _sha256(destination)
    actual_files = {
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_file()
    }
    if actual_files != set(contract["required_files"]):
        raise RuntimeError("runtime candidate file set differs from the pinned contract")
    return observed_hashes


def _verify_abyss_owner_pins(
    abyss_stack_root: Path,
    evidence: dict[str, Any],
) -> None:
    owner_pin = evidence["pins"]["runtime_owner"]
    _require_exact_checkout(
        abyss_stack_root,
        owner_pin["source_ref"],
        "abyss-stack runtime owner",
    )
    pinned_paths = {
        ABYSS_ROUTING_CONFIG_REL: owner_pin["routing_config_sha256"],
        ABYSS_SYNC_WRAPPER_REL: owner_pin["sync_wrapper_sha256"],
        ABYSS_ROUTE_API_REL: owner_pin["route_api_sha256"],
    }
    for rel_path, expected_hash in pinned_paths.items():
        if _sha256(abyss_stack_root / rel_path) != expected_hash:
            raise RuntimeError(f"abyss-stack owner surface drifted: {rel_path}")


def _load_route_api_module(module_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "aoa_sdk_g4_abyss_route_api",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load route-api module: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


def _runtime_mirror_dry_run(
    *,
    evidence: dict[str, Any],
    abyss_stack_root: Path,
    candidate_source: Path,
    temporary_root: Path,
    candidate_hashes: dict[str, str],
) -> dict[str, Any]:
    stack_root = temporary_root / "runtime-stack"
    live_root = Path("/srv/AbyssOS/abyss-stack").resolve()
    if stack_root.resolve() == live_root or live_root in stack_root.resolve().parents:
        raise RuntimeError("G4 runtime dry run must not target the live runtime root")
    environment = os.environ.copy()
    environment["AOA_STACK_ROOT"] = str(stack_root)
    environment["AOA_ROUTING_ROOT"] = str(candidate_source)
    sync_script = abyss_stack_root / "scripts" / "aoa-sync-federation-surfaces"
    _run([str(sync_script), "--layer", "aoa-routing"], abyss_stack_root, env=environment)
    checked = _run(
        [
            str(sync_script),
            "--check",
            "--json",
            "--layer",
            "aoa-routing",
        ],
        abyss_stack_root,
        env=environment,
        capture_output=True,
    )
    check_payload = json.loads(checked.stdout)
    if check_payload.get("status") != "ok":
        raise RuntimeError(f"isolated runtime mirror check failed: {check_payload}")
    if check_payload.get("freshness_status") != "source_commit_unavailable":
        raise RuntimeError("G4 candidate assembly unexpectedly claimed a native Git source")
    mirror_root = stack_root / "Knowledge" / "federation" / "aoa-routing"
    manifest = _read_json(
        mirror_root / "manifest" / "federation_mirror_manifest.json"
    )
    if manifest.get("required_file_count") != evidence["runtime_mirror_contract"][
        "required_file_count"
    ]:
        raise RuntimeError("isolated runtime manifest required-file count drifted")
    if manifest.get("file_sha256") != candidate_hashes:
        raise RuntimeError("isolated runtime manifest hashes differ from the candidate")
    mirrored_hashes = {
        rel_path: _sha256(mirror_root / rel_path)
        for rel_path in evidence["runtime_mirror_contract"]["required_files"]
    }
    if mirrored_hashes != candidate_hashes:
        raise RuntimeError("isolated runtime mirror bytes differ from the candidate")

    config = yaml.safe_load(
        (abyss_stack_root / ABYSS_ROUTING_CONFIG_REL).read_text(encoding="utf-8")
    )
    if not isinstance(config, dict):
        raise RuntimeError("abyss-stack routing config must be a mapping")
    config["mirror_root"] = str(mirror_root)
    dry_config_path = temporary_root / "aoa-routing.dry-run.yaml"
    dry_config_path.write_text(
        yaml.safe_dump(config, sort_keys=False),
        encoding="utf-8",
    )
    module = _load_route_api_module(abyss_stack_root / ABYSS_ROUTE_API_REL)
    layer = module.load_routing_layer(dry_config_path, config, mirror_root)
    status = module.layer_status(layer)
    expected_provenance_reasons = evidence["gate_g4"][
        "runtime_mirror_expected_provenance_debt"
    ]
    expected_closure_status = {
        "mirror_ready": True,
        "consumer_ready": True,
        "provenance_ready": False,
        "closure_ready": False,
        "consumer_reasons": [],
        "provenance_reasons": expected_provenance_reasons,
        "reasons": expected_provenance_reasons,
    }
    if status["closure_status"] != expected_closure_status:
        raise RuntimeError(
            f"route-api routing layer rejected the isolated mirror: {status}"
        )
    route_count = len(layer.payloads["router"].get("entries", []))
    if route_count != evidence["verification_matrix"]["route_count"]:
        raise RuntimeError(
            f"route-api observed {route_count} routes instead of the G4 pin"
        )
    return {
        "required_file_count": manifest["required_file_count"],
        "route_count": route_count,
        "mirror_ready": status["closure_status"]["mirror_ready"],
        "consumer_ready": status["closure_status"]["consumer_ready"],
        "provenance_ready": status["closure_status"]["provenance_ready"],
        "closure_ready": status["closure_status"]["closure_ready"],
        "expected_provenance_debt": status["closure_status"][
            "provenance_reasons"
        ],
        "freshness_status": check_payload["freshness_status"],
        "native_source_ref_available": False,
        "live_runtime_mutated": False,
    }


def _verify_package_trust(
    *,
    release_clone: Path,
    abyss_machine_root: Path,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    trust_pin = evidence["pins"]["trust_owner"]
    _require_exact_checkout(
        abyss_machine_root,
        trust_pin["source_ref"],
        "abyss-machine trust owner",
    )
    manifest = _read_json(release_clone / SDK_DISTRIBUTION_MANIFEST_REL)
    if manifest.get("artifact_class") != trust_pin["artifact_class"]:
        raise RuntimeError("SDK distribution artifact class differs from G4 evidence")
    consumer_commands = manifest.get("consumer_command")
    if not isinstance(consumer_commands, list) or not any(
        "verify_routing_shadow_wheel.py" in command
        for command in consumer_commands
        if isinstance(command, str)
    ):
        raise RuntimeError("SDK trust manifest omits the installed routing shadow gate")
    environment = os.environ.copy()
    environment["ABYSS_MACHINE_REPO_ROOT"] = str(abyss_machine_root)
    completed = _run(
        [
            sys.executable,
            str(release_clone / SDK_TRUST_VALIDATOR_REL),
            "--json",
        ],
        release_clone,
        env=environment,
        capture_output=True,
    )
    payload = json.loads(completed.stdout)
    if payload.get("ok") is not True:
        raise RuntimeError("temporary package artifact trust verification failed")
    if payload.get("required_controls") != trust_pin["required_controls"]:
        raise RuntimeError("package artifact trust required controls drifted")
    if payload.get("verified_controls") != trust_pin["required_controls"]:
        raise RuntimeError("package artifact trust verified controls drifted")
    trust_gate = payload.get("trust_gate", {})
    if trust_gate.get("ok") is not True:
        raise RuntimeError("temporary package artifact trust gate did not allow")
    return {
        "artifact_class": payload["artifact_class"],
        "required_controls": payload["required_controls"],
        "verified_controls": payload["verified_controls"],
        "temporary_registry": True,
        "temporary_subject_store": True,
        "host_registry_mutated": False,
        "live_runtime_admission_claimed": False,
    }


def main() -> int:
    args = parse_args()
    sdk_release_root = args.sdk_release_root.resolve()
    predecessor_root = args.predecessor_root.resolve()
    abyss_stack_root = args.abyss_stack_root.resolve()
    abyss_machine_root = args.abyss_machine_root.resolve()
    input_workspace_root = args.input_workspace_root.resolve()
    abyss_stack_input_root = args.abyss_stack_input_root.resolve()
    evidence = _read_json(EVIDENCE_PATH)
    release_pin = evidence["pins"]["sdk_release"]
    predecessor_pin = evidence["pins"]["predecessor"]

    _require_annotated_release(sdk_release_root, release_pin)
    _require_exact_checkout(
        predecessor_root,
        predecessor_pin["parity_consumer_ref"],
        "aoa-routing parity consumer",
    )
    pin = _validate_predecessor_pin(predecessor_root, evidence)
    _verify_abyss_owner_pins(abyss_stack_root, evidence)

    with tempfile.TemporaryDirectory(
        prefix="aoa-sdk-routing-g4-",
        dir=_temporary_root(),
    ) as temporary:
        root = Path(temporary)
        release_clone = root / "sdk-release"
        _clone_release_source(
            sdk_release_root,
            release_clone,
            release_pin["source_ref"],
        )
        wheel, sdist = _build_release_distribution(
            release_clone,
            release_pin["version"],
        )
        trust = _verify_package_trust(
            release_clone=release_clone,
            abyss_machine_root=abyss_machine_root,
            evidence=evidence,
        )
        python, environment = _create_installed_environment(
            wheel,
            root / "venv",
        )
        fixture_archive = release_clone / SDK_FIXTURE_ARCHIVE_REL
        if _sha256(fixture_archive) != pin["fixture"]["archive_sha256"]:
            raise RuntimeError("compact release fixture archive differs from its pin")
        fixture_root = root / "fixture"
        _safe_materialize_fixture(
            fixture_archive,
            fixture_root,
        )
        first_output = root / "sdk-shadow-first"
        second_output = root / "sdk-shadow-second"
        first_report = _probe_installed_shadow(
            python=python,
            environment=environment,
            predecessor_root=predecessor_root,
            release_clone=release_clone,
            fixture_root=fixture_root,
            output_dir=first_output,
            predecessor_ref=predecessor_pin["parity_consumer_ref"],
        )
        second_report = _probe_installed_shadow(
            python=python,
            environment=environment,
            predecessor_root=predecessor_root,
            release_clone=release_clone,
            fixture_root=fixture_root,
            output_dir=second_output,
            predecessor_ref=predecessor_pin["parity_consumer_ref"],
        )
        if first_report["artifact_sha256"] != second_report["artifact_sha256"]:
            raise RuntimeError("two installed SDK shadow builds were not deterministic")
        if first_report["artifact_count"] != 14 or first_report["schema_count"] != 17:
            raise RuntimeError("installed SDK shadow artifact or schema count drifted")
        artifact_names = pin["artifact_names"]
        compact_expected_payload = _read_json(
            release_clone / pin["fixture"]["expected_hashes_path"]
        )
        compact_expected_hashes = compact_expected_payload["output_sha256"]
        if first_report["artifact_sha256"] != compact_expected_hashes:
            raise RuntimeError(
                "installed SDK compact-fixture hashes differ from the release pin"
            )
        deterministic_byte_mismatches = [
            name
            for name in artifact_names
            if (first_output / name).read_bytes()
            != (second_output / name).read_bytes()
        ]
        if deterministic_byte_mismatches:
            raise RuntimeError(
                "installed SDK deterministic byte mismatches: "
                f"{deterministic_byte_mismatches}"
            )
        predecessor_hashes = _verify_predecessor_rollback(
            predecessor_root,
            fixture_root,
            root / "predecessor-output",
            predecessor_pin["implementation_baseline_ref"],
            artifact_names,
            first_output,
        )
        if predecessor_hashes != first_report["artifact_sha256"]:
            raise RuntimeError("predecessor rollback hashes differ from SDK shadow")

        full_input_root = root / "full-corpus-inputs"
        skipped_symlinks = _materialize_full_corpus(
            evidence=evidence,
            workspace_root=input_workspace_root,
            abyss_stack_input_root=abyss_stack_input_root,
            target=full_input_root,
        )
        full_output, full_hashes = _verify_full_corpus(
            evidence=evidence,
            release_clone=release_clone,
            predecessor_root=predecessor_root,
            python=python,
            environment=environment,
            input_root=full_input_root,
            temporary_root=root,
            artifact_names=artifact_names,
        )

        schema_root = _installed_schema_root(python, environment, root)
        candidate_hashes = _assemble_runtime_source(
            evidence=evidence,
            predecessor_root=predecessor_root,
            sdk_output=full_output,
            schema_root=schema_root,
            target=root / "runtime-candidate",
        )
        runtime = _runtime_mirror_dry_run(
            evidence=evidence,
            abyss_stack_root=abyss_stack_root,
            candidate_source=root / "runtime-candidate",
            temporary_root=root,
            candidate_hashes=candidate_hashes,
        )

        receipt = {
            "schema_version": "aoa_sdk_routing_succession_g4_run_v1",
            "status": "pass",
            "state": "sdk_shadow",
            "canonical_producer": "aoa-routing",
            "sdk_release": {
                "tag": release_pin["tag"],
                "tag_object_ref": release_pin["tag_object_ref"],
                "source_ref": release_pin["source_ref"],
                "package_version": first_report["package_version"],
                "local_wheel_sha256": _sha256(wheel),
                "local_sdist_sha256": _sha256(sdist),
                "published_archive_hash_equivalence_claimed": False,
            },
            "shadow": {
                "artifact_count": first_report["artifact_count"],
                "schema_count": first_report["schema_count"],
                "compact_fixture_byte_parity": "14/14",
                "full_corpus_byte_parity": "14/14",
                "deterministic_builds": {
                    "compact_fixture": 2,
                    "full_corpus": 2,
                },
                "full_corpus_route_count": runtime["route_count"],
                "full_corpus_input_refs": evidence["pins"]["full_corpus"][
                    "input_source_refs"
                ],
                "full_corpus_output_sha256": full_hashes,
                "skipped_non_input_symlinks": skipped_symlinks,
                "module_path_inside_fresh_environment": True,
                "publication_posture": first_report["publication_posture"],
            },
            "predecessor": {
                "source_ref": predecessor_pin["parity_consumer_ref"],
                "implementation_unchanged_from": predecessor_pin[
                    "implementation_baseline_ref"
                ],
                "compact_fixture_rollback_byte_parity": "14/14",
                "full_corpus_rollback_byte_parity": "14/14",
            },
            "runtime_mirror": runtime,
            "package_trust": trust,
            "authority": {
                "g4_passed": True,
                "g5_owner_switch": False,
                "runtime_publication_authorized": False,
                "live_runtime_mutated": False,
                "repository_archive_authorized": False,
            },
        }
        print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
