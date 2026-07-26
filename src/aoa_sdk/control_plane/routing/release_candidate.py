"""Build a public G5 release candidate without authorizing the owner switch."""

from __future__ import annotations

import binascii
import hashlib
import json
import struct
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, BinaryIO, Mapping, cast

from .candidate import (
    AUTHORITY_STOP_LINE,
    CANDIDATE_ASSEMBLY_FILES,
    CANDIDATE_MANIFEST_REL,
    CANDIDATE_PROVENANCE_REL,
    G5RoutingCandidateBundle,
    build_g5_candidate_bundle,
    load_g5_candidate_bundle,
    validate_g5_candidate_bundle,
)
from .core import RouterError
from .shadow import RoutingProducerInputs
from .validator import get_schema_validator


RELEASE_CANDIDATE_PROFILE_ID = "aoa-sdk-g5-release-candidate"
RELEASE_CANDIDATE_PROVENANCE_REL = Path(
    "succession/routing-g5-release-candidate-provenance.json"
)
RELEASE_CANDIDATE_MANIFEST_REL = Path("artifact.bundle.json")
RELEASE_CANDIDATE_PAYLOAD_ROOT = Path("candidate")
RELEASE_CANDIDATE_STOP_LINE = (
    "This public asset is an SDK G5 release candidate, not the G5 owner-switch "
    "receipt. aoa-routing remains canonical; production runtime admission, "
    "canonical generation, predecessor maintenance-only posture, the "
    "compatibility window, consumer-zero, and archival authority remain "
    "separate gates."
)
G5_FALSE_AUTHORITY = {
    "canonical_producer_switch_authorized": False,
    "sdk_canonical": False,
    "live_runtime_mutation_authorized": False,
    "predecessor_maintenance_only": False,
    "compatibility_window_started": False,
    "archive_authorized": False,
}


@dataclass(frozen=True)
class G5RoutingReleaseCandidateBundle:
    output_root: Path
    candidate: G5RoutingCandidateBundle
    provenance_path: Path
    manifest_path: Path
    sdk_source_ref: str
    predecessor_source_ref: str
    input_source_refs: Mapping[str, str]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_canonical_gzip(source: BinaryIO, destination: BinaryIO) -> None:
    """Encode one cross-zlib-stable gzip stream with stored DEFLATE blocks."""

    destination.write(b"\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\xff")
    crc32 = 0
    size = 0
    block = source.read(65535)
    if not block:
        destination.write(b"\x01\x00\x00\xff\xff")
    while block:
        next_block = source.read(65535)
        destination.write(b"\x01" if not next_block else b"\x00")
        block_size = len(block)
        destination.write(
            struct.pack("<HH", block_size, 0xFFFF ^ block_size)
        )
        destination.write(block)
        crc32 = binascii.crc32(block, crc32)
        size = (size + block_size) & 0xFFFFFFFF
        block = next_block
    destination.write(struct.pack("<II", crc32 & 0xFFFFFFFF, size))


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterError(f"could not load {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RouterError(f"{label} must contain an object")
    return payload


def _fresh_release_root(
    output_root: Path,
    forbidden_roots: Mapping[str, Path],
) -> Path:
    requested = output_root.expanduser().absolute()
    if requested.is_symlink():
        raise RouterError("G5 release-candidate output root must not be a symlink")
    target = requested.resolve()
    for owner, root in sorted(forbidden_roots.items()):
        resolved_root = root.resolve()
        if target == resolved_root or resolved_root in target.parents:
            raise RouterError(
                "G5 release-candidate output root must stay outside producer "
                f"inputs; target is inside {owner}"
            )
    if target.exists() and not target.is_dir():
        raise RouterError("G5 release-candidate output root must be a directory")
    if target.exists() and any(target.iterdir()):
        raise RouterError(
            "G5 release-candidate output root must be absent or empty"
        )
    target.mkdir(parents=True, exist_ok=True)
    return target


def _release_subjects() -> list[dict[str, str]]:
    subjects: list[dict[str, str]] = []
    for rel_path in CANDIDATE_ASSEMBLY_FILES:
        if rel_path.startswith("generated/"):
            role = "routing_readmodel"
        elif rel_path.startswith("schemas/"):
            role = "routing_schema"
        else:
            role = "runtime_compatibility_boundary"
        subjects.append(
            {
                "path": (
                    RELEASE_CANDIDATE_PAYLOAD_ROOT / rel_path
                ).as_posix(),
                "role": role,
            }
        )
    subjects.extend(
        [
            {
                "path": (
                    RELEASE_CANDIDATE_PAYLOAD_ROOT
                    / CANDIDATE_PROVENANCE_REL
                ).as_posix(),
                "role": "owner_succession_candidate_provenance",
            },
            {
                "path": RELEASE_CANDIDATE_PROVENANCE_REL.as_posix(),
                "role": "public_release_candidate_provenance",
            },
        ]
    )
    return subjects


def _release_manifest(sdk_source_ref: str) -> dict[str, Any]:
    return {
        "schema": "abyss_machine_artifact_bundle_manifest_v1",
        "id": f"aoa-sdk-routing-g5-release-candidate-{sdk_source_ref[:16]}",
        "artifact_class": "thin_routing_readmodel_bundle",
        "owner_repo": "aoa-sdk",
        "producer_admission_profile_id": RELEASE_CANDIDATE_PROFILE_ID,
        "policy_ref": (
            "repo:abyss-machine/manifests/artifact_signature_policy.manifest.json"
        ),
        "mode": "github_release",
        "public_safe": True,
        "purpose": (
            "Publicly attest the exact SDK routing-owner release candidate "
            "before the separate G5 owner switch."
        ),
        "privacy_boundary": (
            "public-safe routing readmodels, schemas, runtime boundary docs, "
            "and exact source provenance only; no private payloads, secrets, "
            "runtime state, or copied sibling source authority"
        ),
        "subject_repo_root": ".",
        "artifact_source": {
            "kind": "generated_thin_routing_readmodel_release_candidate",
            "content_identity_ref": "candidate/generated/aoa_router.min.json",
            "artifact_identity_ref": (
                "candidate/generated/aoa_router.min.json#/artifact_identity"
            ),
            "producer_source_ref": sdk_source_ref,
        },
        "artifact_identity": {
            "artifact_class": "thin_routing_readmodel_bundle",
            "abi_epoch": "aoa_routing_thin_router_v1",
        },
        "abi_subject": {
            "path": "candidate/generated/aoa_router.min.json",
            "artifact_identity_pointer": "/artifact_identity",
        },
        "artifact_subjects": _release_subjects(),
        "build_type": (
            "urn:abyssos:buildtype:aoa-sdk-routing-release-candidate:v1"
        ),
        "package": {
            "ecosystem": "generated-readmodel",
            "name": "aoa-sdk-routing-readmodel",
            "purl": f"pkg:generic/aoa-sdk-routing-readmodel@{sdk_source_ref}",
        },
        "lifecycle": {
            "initial_state": "release-ready",
            "promotion_path": [
                "release-ready",
                "published",
                "superseded",
                "revoked",
            ],
            "latest_eligible_states": ["release-ready", "published"],
        },
        "consumer_contract": {
            "stable_interface": (
                "python mechanics/release-support/parts/"
                "release-audit-publish-helper/scripts/"
                "build_routing_g5_release_candidate.py --check "
                "--output-dir RELEASE_CANDIDATE_ROOT"
            ),
            "consumer_expectation": (
                "Release consumers admit only the exact SDK source ref, "
                "artifact-subject digest, public release asset digest, and "
                "stronger-owner record. Normal production runtime remains "
                "denied until the separate G5 receipt changes canonical policy."
            ),
            "registry_required": True,
            "subject_store_required": True,
            "admission_gate": "fail_closed_consumer_admission",
            "consumer_verdict": "allow_or_deny_required_before_use",
        },
        "consumer_command": [
            (
                "abyss-machine artifacts build-sidecars --manifest "
                "RELEASE_CANDIDATE_ROOT/artifact.bundle.json "
                "--bundle-dir BUNDLE_DIR --mode github_release"
            ),
            "abyss-machine artifacts sign BUNDLE_DIR",
            "abyss-machine artifacts verify BUNDLE_DIR",
            "abyss-machine artifacts release-check BUNDLE_DIR",
            (
                "abyss-machine artifacts evidence-promote BUNDLE_DIR "
                "--registry-dir REGISTRY_DIR --lifecycle-state release-ready "
                "--consumer-ref aoa-sdk:routing-g5-release-candidate "
                "--evidence-ref BUNDLE_DIR/artifact.verify.json "
                "--source-repo aoa-sdk "
                f"--source-ref {sdk_source_ref} "
                "--producer aoa-sdk-routing-release-candidate-builder "
                "--trust-root-mode public_release "
                "--trust-root-evidence-json @PUBLIC_RELEASE_EVIDENCE.json --json"
            ),
            (
                "abyss-machine artifacts materialize-subjects BUNDLE_DIR "
                "--store-root SUBJECT_STORE_ROOT --registry-dir REGISTRY_DIR "
                "--manifest RELEASE_CANDIDATE_ROOT/artifact.bundle.json "
                "--consumer-intent release_consumer --source-repo aoa-sdk "
                "--trust-root-mode public_release --json"
            ),
            (
                "abyss-machine artifacts trust-gate --registry-dir REGISTRY_DIR "
                "--artifact-class thin_routing_readmodel_bundle "
                "--consumer-intent release_consumer --source-repo aoa-sdk "
                "--trust-root-mode public_release "
                "--subject-digest SUBJECT_DIGEST --json"
            ),
            (
                "abyss-machine artifacts trust-gate --registry-dir REGISTRY_DIR "
                "--artifact-class thin_routing_readmodel_bundle "
                "--consumer-intent runtime --source-repo aoa-sdk "
                "--subject-digest SUBJECT_DIGEST --json # must deny before G5"
            ),
        ],
    }


def _release_provenance(
    candidate: G5RoutingCandidateBundle,
    *,
    observed_at: datetime,
) -> dict[str, Any]:
    timestamp = observed_at.isoformat().replace("+00:00", "Z")
    candidate_content = {
        "artifact_sha256": dict(sorted(candidate.artifact_sha256.items())),
        "assembly_file_sha256": dict(
            sorted(candidate.assembly_file_sha256.items())
        ),
        "candidate_manifest_sha256": _sha256(candidate.manifest_path),
        "candidate_provenance_sha256": _sha256(candidate.provenance_path),
    }
    return {
        "schema_version": "aoa_sdk_routing_g5_release_candidate_provenance_v1",
        "state": "sdk_g5_release_candidate",
        "publication_posture": "public_release_candidate",
        "current_canonical_producer": {
            "owner_repo": "aoa-routing",
            "source_ref": candidate.predecessor_source_ref,
        },
        "candidate_producer": {
            "owner_repo": "aoa-sdk",
            "source_ref": candidate.sdk_source_ref,
            "implementation": "aoa_sdk.control_plane.routing",
        },
        "candidate_artifact_identity": {
            "artifact_class": "thin_routing_readmodel_bundle",
            "owner_repo": "aoa-sdk",
            "abi_epoch": "aoa_routing_thin_router_v1",
        },
        "abi_epoch": "aoa_routing_thin_router_v1",
        "candidate_bundle": {
            "root": RELEASE_CANDIDATE_PAYLOAD_ROOT.as_posix(),
            "manifest_ref": (
                RELEASE_CANDIDATE_PAYLOAD_ROOT / CANDIDATE_MANIFEST_REL
            ).as_posix(),
            "provenance_ref": (
                RELEASE_CANDIDATE_PAYLOAD_ROOT / CANDIDATE_PROVENANCE_REL
            ).as_posix(),
            **candidate_content,
            "content_digest": _stable_digest(candidate_content),
        },
        "input_source_refs": dict(sorted(candidate.input_source_refs.items())),
        "observed_at": timestamp,
        "trust_posture": {
            "artifact_class": "thin_routing_readmodel_bundle",
            "required_controls": [
                "abi_signature",
                "sbom",
                "slsa_in_toto",
            ],
            "stronger_owner": "abyss-machine",
            "admission_status": "pending_public_release_verification",
            "runtime_consumer": "abyss-stack",
        },
        "g5_authority": dict(G5_FALSE_AUTHORITY),
        "authority_stop_line": RELEASE_CANDIDATE_STOP_LINE,
        "wrapped_candidate_stop_line": AUTHORITY_STOP_LINE,
    }


def build_g5_release_candidate_bundle(
    inputs: RoutingProducerInputs,
    output_root: Path,
    *,
    predecessor_source_ref: str,
    sdk_source_ref: str,
    input_source_refs: Mapping[str, str],
    observed_at: datetime,
) -> G5RoutingReleaseCandidateBundle:
    """Build an exact public-release envelope around a valid SDK candidate."""

    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise RouterError("observed_at must be timezone-aware")
    resolved_inputs = inputs.resolved()
    target = _fresh_release_root(output_root, resolved_inputs.source_roots())
    candidate = build_g5_candidate_bundle(
        resolved_inputs,
        target / RELEASE_CANDIDATE_PAYLOAD_ROOT,
        predecessor_source_ref=predecessor_source_ref,
        sdk_source_ref=sdk_source_ref,
        input_source_refs=input_source_refs,
        observed_at=observed_at,
    )
    provenance_path = target / RELEASE_CANDIDATE_PROVENANCE_REL
    provenance_path.parent.mkdir()
    provenance_path.write_text(
        json.dumps(
            _release_provenance(candidate, observed_at=observed_at),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    manifest_path = target / RELEASE_CANDIDATE_MANIFEST_REL
    manifest_path.write_text(
        json.dumps(
            _release_manifest(candidate.sdk_source_ref),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    bundle = G5RoutingReleaseCandidateBundle(
        output_root=target,
        candidate=candidate,
        provenance_path=provenance_path,
        manifest_path=manifest_path,
        sdk_source_ref=candidate.sdk_source_ref,
        predecessor_source_ref=candidate.predecessor_source_ref,
        input_source_refs=candidate.input_source_refs,
    )
    validate_g5_release_candidate_bundle(bundle, resolved_inputs)
    return bundle


def load_g5_release_candidate_bundle(
    output_root: Path,
) -> G5RoutingReleaseCandidateBundle:
    target = output_root.resolve()
    candidate = load_g5_candidate_bundle(
        target / RELEASE_CANDIDATE_PAYLOAD_ROOT
    )
    return G5RoutingReleaseCandidateBundle(
        output_root=target,
        candidate=candidate,
        provenance_path=target / RELEASE_CANDIDATE_PROVENANCE_REL,
        manifest_path=target / RELEASE_CANDIDATE_MANIFEST_REL,
        sdk_source_ref=candidate.sdk_source_ref,
        predecessor_source_ref=candidate.predecessor_source_ref,
        input_source_refs=candidate.input_source_refs,
    )


def validate_g5_release_candidate_bundle(
    bundle: G5RoutingReleaseCandidateBundle,
    inputs: RoutingProducerInputs,
) -> None:
    """Fail closed on wrapped-candidate, release, source, or authority drift."""

    validate_g5_candidate_bundle(bundle.candidate, inputs)
    candidate_entries = {
        (
            RELEASE_CANDIDATE_PAYLOAD_ROOT
            / path.relative_to(bundle.candidate.output_root)
        ).as_posix()
        for path in bundle.candidate.output_root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    expected_entries = candidate_entries | {
        RELEASE_CANDIDATE_PROVENANCE_REL.as_posix(),
        RELEASE_CANDIDATE_MANIFEST_REL.as_posix(),
    }
    actual_entries = {
        path.relative_to(bundle.output_root).as_posix(): path
        for path in bundle.output_root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if set(actual_entries) != expected_entries:
        missing = sorted(expected_entries - set(actual_entries))
        extra = sorted(set(actual_entries) - expected_entries)
        raise RouterError(
            "G5 release-candidate file set drifted; "
            f"missing={missing}, extra={extra}"
        )
    expected_directories = {
        parent.as_posix()
        for rel_path in expected_entries
        for parent in Path(rel_path).parents
        if parent != Path(".")
    }
    actual_directories = {
        path.relative_to(bundle.output_root).as_posix()
        for path in bundle.output_root.rglob("*")
        if path.is_dir() and not path.is_symlink()
    }
    if actual_directories != expected_directories:
        missing = sorted(expected_directories - actual_directories)
        extra = sorted(actual_directories - expected_directories)
        raise RouterError(
            "G5 release-candidate directory set drifted; "
            f"missing={missing}, extra={extra}"
        )
    invalid_entries = sorted(
        name
        for name, path in actual_entries.items()
        if path.is_symlink() or not path.is_file()
    )
    if invalid_entries:
        raise RouterError(
            "G5 release-candidate entries must be regular files: "
            f"{invalid_entries}"
        )

    provenance = _read_json_object(
        bundle.provenance_path,
        "G5 release-candidate provenance",
    )
    errors = sorted(
        get_schema_validator(
            "routing-g5-release-candidate-provenance.schema.json"
        ).iter_errors(provenance),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        rendered = "; ".join(error.message for error in errors)
        raise RouterError(
            f"G5 release-candidate provenance schema violations: {rendered}"
        )
    try:
        observed_at = datetime.fromisoformat(
            str(provenance["observed_at"]).replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise RouterError(
            "G5 release-candidate observed_at must be RFC 3339"
        ) from exc
    expected_provenance = _release_provenance(
        bundle.candidate,
        observed_at=observed_at,
    )
    if provenance != expected_provenance:
        raise RouterError("G5 release-candidate provenance content drifted")
    if provenance.get("g5_authority") != G5_FALSE_AUTHORITY:
        raise RouterError("G5 release-candidate authority stop line drifted")

    manifest = _read_json_object(
        bundle.manifest_path,
        "G5 release-candidate artifact manifest",
    )
    if manifest != _release_manifest(bundle.sdk_source_ref):
        raise RouterError("G5 release-candidate manifest content drifted")
    if manifest.get("mode") != "github_release":
        raise RouterError("G5 release-candidate manifest mode drifted")
    if manifest.get("producer_admission_profile_id") != (
        RELEASE_CANDIDATE_PROFILE_ID
    ):
        raise RouterError("G5 release-candidate admission profile drifted")
    subject_paths = {
        item.get("path")
        for item in manifest.get("artifact_subjects", [])
        if isinstance(item, dict)
    }
    expected_subjects = {
        (
            RELEASE_CANDIDATE_PAYLOAD_ROOT / rel_path
        ).as_posix()
        for rel_path in CANDIDATE_ASSEMBLY_FILES
    } | {
        (
            RELEASE_CANDIDATE_PAYLOAD_ROOT / CANDIDATE_PROVENANCE_REL
        ).as_posix(),
        RELEASE_CANDIDATE_PROVENANCE_REL.as_posix(),
    }
    if subject_paths != expected_subjects:
        raise RouterError("G5 release-candidate subject set drifted")
    commands = "\n".join(str(item) for item in manifest["consumer_command"])
    if "--consumer-intent runtime " not in commands or "must deny before G5" not in commands:
        raise RouterError("G5 release-candidate runtime denial check drifted")


def write_deterministic_release_archive(
    bundle: G5RoutingReleaseCandidateBundle,
    archive_path: Path,
) -> str:
    """Write a path- and zlib-independent tar.gz and return its SHA-256."""

    archive = archive_path.expanduser().absolute()
    archive.parent.mkdir(parents=True, exist_ok=True)
    prefix = Path("aoa-sdk-routing-g5-release-candidate")
    paths = sorted(
        bundle.output_root.rglob("*"),
        key=lambda path: path.relative_to(bundle.output_root).as_posix(),
    )
    if any(path.is_symlink() for path in paths):
        raise RouterError("release archive input must not contain symlinks")
    with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as tar_stream:
        with tarfile.open(
            fileobj=tar_stream,
            mode="w",
            format=tarfile.PAX_FORMAT,
        ) as tar:
            for path in paths:
                rel_path = path.relative_to(bundle.output_root)
                info = tar.gettarinfo(
                    str(path),
                    arcname=(prefix / rel_path).as_posix(),
                )
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.mtime = 0
                info.mode = 0o755 if path.is_dir() else 0o644
                if path.is_file():
                    with path.open("rb") as handle:
                        tar.addfile(info, handle)
                else:
                    tar.addfile(info)
        tar_stream.seek(0)
        with archive.open("wb") as raw:
            _write_canonical_gzip(cast(BinaryIO, tar_stream), raw)
    return _sha256(archive)
