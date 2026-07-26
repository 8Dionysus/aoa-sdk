"""Build and validate the receipt-bound canonical SDK routing release.

The G5 artifact deliberately consumes the already-public G5 release candidate
as its byte-parity trust root.  It then adds a separate owner-switch receipt
and canonical provenance.  This avoids a self-referential release digest while
making the authority change explicit and independently reviewable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Mapping, cast

from jsonschema.exceptions import ValidationError

from .candidate import (
    CANDIDATE_ASSEMBLY_FILES,
    CANDIDATE_DIRECTORIES,
    G5RoutingCandidateBundle,
    build_g5_candidate_bundle,
)
from .core import REPO_ROOT, RouterError, default_dependency_root
from .identity import SDK_G5_CANDIDATE
from .release_candidate import _write_canonical_gzip
from .shadow import RoutingProducerInputs
from .validator import get_schema_validator, validate_generated_outputs


CANONICAL_PROFILE_ID = "aoa-sdk-g5-canonical"
CANONICAL_MANIFEST_REL = Path("artifact.bundle.json")
CANONICAL_PROVENANCE_REL = Path(
    "succession/routing-g5-canonical-provenance.json"
)
OWNER_SWITCH_RECEIPT_REL = Path(
    "succession/routing-g5-owner-switch.json"
)
OWNER_SWITCH_RECEIPT_SCHEMA = (
    "aoa_sdk_routing_g5_owner_switch_receipt_v1"
)
PUBLIC_RELEASE_ARCHIVE_PREFIX = Path(
    "aoa-sdk-routing-g5-release-candidate"
)
ABI_EPOCH = "aoa_routing_thin_router_v1"
ARTIFACT_CLASS = "thin_routing_readmodel_bundle"
GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
SHA256_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
RFC3339_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
)

G5_CANONICAL_AUTHORITY = {
    "archive_authorized": False,
    "canonical_producer_switch_authorized": True,
    "compatibility_window_started": True,
    "live_runtime_mutation_authorized": True,
    "predecessor_maintenance_only": True,
    "sdk_canonical": True,
}
ARCHIVE_STOP_LINE = (
    "Repository archival remains forbidden without consumer-zero, "
    "compatibility exit, and separate exact operator approval."
)


@dataclass(frozen=True)
class G5RoutingCanonicalBundle:
    """One exact SDK-canonical routing artifact and its authorization."""

    output_root: Path
    generated_root: Path
    provenance_path: Path
    receipt_path: Path
    manifest_path: Path
    sdk_source_ref: str
    predecessor_source_ref: str
    input_source_refs: Mapping[str, str]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_digest(path: Path) -> str:
    return f"sha256:{_sha256(path)}"


def _stable_digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterError(f"could not load {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RouterError(f"{label} must contain an object")
    return payload


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _require_source_ref(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or value != value.lower()
        or not GIT_OBJECT_ID.fullmatch(value)
    ):
        raise RouterError(f"{label} must be a full lowercase Git object ID")
    return value


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA256_DIGEST.fullmatch(value):
        raise RouterError(f"{label} must be a sha256 digest")
    return value


def _require_timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not RFC3339_TIMESTAMP.fullmatch(value):
        raise RouterError(f"{label} must be an RFC 3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RouterError(f"{label} must be an RFC 3339 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RouterError(f"{label} must include a timezone offset")
    return parsed


def _require_date(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RouterError(f"{label} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise RouterError(f"{label} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise RouterError(f"{label} must be an ISO date")
    return value


def _git_output(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _require_exact_checkout(root: Path, source_ref: str, label: str) -> None:
    try:
        head = _git_output(root, "rev-parse", "HEAD")
        status = _git_output(
            root,
            "status",
            "--porcelain",
            "--untracked-files=all",
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise RouterError(f"{label} must be an exact Git checkout") from exc
    if head != source_ref:
        raise RouterError(
            f"{label} checkout {head} does not match {source_ref}"
        )
    if status:
        raise RouterError(f"{label} checkout must be clean")


def _fresh_output_root(
    output_root: Path,
    forbidden_roots: Mapping[str, Path],
) -> Path:
    requested = output_root.expanduser().absolute()
    if requested.is_symlink():
        raise RouterError("G5 canonical output root must not be a symlink")
    target = requested.resolve()
    for owner, root in sorted(forbidden_roots.items()):
        resolved = root.resolve()
        if target == resolved or resolved in target.parents:
            raise RouterError(
                "G5 canonical output root must stay outside producer inputs; "
                f"target is inside {owner}"
            )
    if target.exists() and not target.is_dir():
        raise RouterError("G5 canonical output root must be a directory")
    if target.exists() and any(target.iterdir()):
        raise RouterError("G5 canonical output root must be absent or empty")
    target.mkdir(parents=True, exist_ok=True)
    return target


def _public_release_members(
    archive_path: Path,
    *,
    expected_digest: str,
    release_source_ref: str,
    predecessor_source_ref: str,
) -> dict[str, bytes]:
    requested = archive_path.expanduser().absolute()
    if requested.is_symlink():
        raise RouterError("public release asset must not be a symlink")
    archive = requested.resolve(strict=True)
    if not archive.is_file():
        raise RouterError("public release asset must be a regular file")
    if _sha256_digest(archive) != expected_digest:
        raise RouterError("public release asset digest drifted")

    wanted = {
        (
            PUBLIC_RELEASE_ARCHIVE_PREFIX
            / "candidate"
            / relative
        ).as_posix(): relative
        for relative in CANDIDATE_ASSEMBLY_FILES
    }
    release_provenance_name = (
        PUBLIC_RELEASE_ARCHIVE_PREFIX
        / "succession"
        / "routing-g5-release-candidate-provenance.json"
    ).as_posix()
    payloads: dict[str, bytes] = {}
    release_provenance: dict[str, Any] | None = None
    try:
        with tarfile.open(archive, mode="r:gz") as tar:
            names: set[str] = set()
            for member in tar.getmembers():
                member_path = PurePosixPath(member.name)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise RouterError(
                        "public release archive contains an unsafe path"
                    )
                if member.name in names:
                    raise RouterError(
                        "public release archive contains duplicate paths"
                    )
                names.add(member.name)
                if member.issym() or member.islnk():
                    raise RouterError(
                        "public release archive must not contain links"
                    )
                if not member.isfile() and not member.isdir():
                    raise RouterError(
                        "public release archive contains an unsupported member"
                    )
                if not member.isfile():
                    continue
                extracted = tar.extractfile(member)
                if extracted is None:
                    raise RouterError(
                        "public release archive member could not be read"
                    )
                body = extracted.read()
                relative = wanted.get(member.name)
                if relative is not None:
                    payloads[relative] = body
                elif member.name == release_provenance_name:
                    parsed = json.loads(body.decode("utf-8"))
                    if not isinstance(parsed, dict):
                        raise RouterError(
                            "public release provenance must be an object"
                        )
                    release_provenance = parsed
    except (OSError, tarfile.TarError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RouterError(f"could not inspect public release asset: {exc}") from exc

    if set(payloads) != set(CANDIDATE_ASSEMBLY_FILES):
        missing = sorted(set(CANDIDATE_ASSEMBLY_FILES) - set(payloads))
        raise RouterError(
            f"public release asset lacks routing assembly files: {missing}"
        )
    if release_provenance is None:
        raise RouterError("public release provenance is missing")
    producer = release_provenance.get("candidate_producer")
    predecessor = release_provenance.get("current_canonical_producer")
    if (
        release_provenance.get("schema_version")
        != "aoa_sdk_routing_g5_release_candidate_provenance_v1"
        or not isinstance(producer, dict)
        or producer.get("source_ref") != release_source_ref
        or not isinstance(predecessor, dict)
        or predecessor.get("source_ref") != predecessor_source_ref
    ):
        raise RouterError("public release provenance source binding drifted")
    return payloads


def _copy_candidate_assembly(
    candidate: G5RoutingCandidateBundle,
    target: Path,
    public_members: Mapping[str, bytes],
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in CANDIDATE_ASSEMBLY_FILES:
        source = candidate.output_root / relative
        body = source.read_bytes()
        if body != public_members[relative]:
            raise RouterError(
                "G5 owner switch would change released routing bytes: "
                f"{relative}"
            )
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)
        hashes[relative] = hashlib.sha256(body).hexdigest()
    return hashes


def _owner_switch_receipt(
    *,
    sdk_source_ref: str,
    sdk_version: str,
    predecessor_source_ref: str,
    public_release_ref: str,
    public_release_source_ref: str,
    public_release_asset_name: str,
    public_release_asset_digest: str,
    runtime_consumer_source_ref: str,
    compatibility_started_on: str,
    authorized_at: datetime,
) -> dict[str, Any]:
    return {
        "schema": OWNER_SWITCH_RECEIPT_SCHEMA,
        "status": "g5_switch_authorized",
        "transition": {
            "from_state": "predecessor_canonical",
            "to_state": "sdk_canonical",
            "canonical_owner_before": "aoa-routing",
            "canonical_owner_after": "aoa-sdk",
        },
        "sdk": {
            "owner_repo": "aoa-sdk",
            "source_ref": sdk_source_ref,
            "version": sdk_version,
            "abi_epoch": ABI_EPOCH,
        },
        "predecessor": {
            "owner_repo": "aoa-routing",
            "source_ref": predecessor_source_ref,
            "rollback_posture": "retained",
        },
        "public_release": {
            "release_ref": public_release_ref,
            "source_ref": public_release_source_ref,
            "asset_name": public_release_asset_name,
            "asset_digest": public_release_asset_digest,
        },
        "runtime_consumer": {
            "owner_repo": "abyss-stack",
            "source_ref": runtime_consumer_source_ref,
            "contract_ref": (
                "docs/decisions/"
                "ABYSS-STACK-D-0086-receipt-bound-sdk-routing-cutover.md"
            ),
        },
        "compatibility_window": {
            "state": "started",
            "started_on": compatibility_started_on,
            "started_by_sdk_version": sdk_version,
        },
        "authorized_at": authorized_at.isoformat().replace("+00:00", "Z"),
        "g5_authority": dict(G5_CANONICAL_AUTHORITY),
        "archive_stop_line": ARCHIVE_STOP_LINE,
    }


def _artifact_subjects() -> list[dict[str, str]]:
    subjects: list[dict[str, str]] = []
    for relative in CANDIDATE_ASSEMBLY_FILES:
        if relative.startswith("generated/"):
            role = "routing_readmodel"
        elif relative.startswith("schemas/"):
            role = "routing_schema"
        else:
            role = "runtime_compatibility_boundary"
        subjects.append({"path": relative, "role": role})
    subjects.extend(
        [
            {
                "path": OWNER_SWITCH_RECEIPT_REL.as_posix(),
                "role": "owner_switch_receipt",
            },
            {
                "path": CANONICAL_PROVENANCE_REL.as_posix(),
                "role": "canonical_owner_succession_provenance",
            },
        ]
    )
    return subjects


def _canonical_manifest(sdk_source_ref: str) -> dict[str, Any]:
    return {
        "schema": "abyss_machine_artifact_bundle_manifest_v1",
        "id": f"aoa-sdk-routing-g5-canonical-{sdk_source_ref[:16]}",
        "artifact_class": ARTIFACT_CLASS,
        "owner_repo": "aoa-sdk",
        "producer_admission_profile_id": CANONICAL_PROFILE_ID,
        "policy_ref": (
            "repo:abyss-machine/"
            "manifests/artifact_signature_policy.manifest.json"
        ),
        "mode": "github_release",
        "public_safe": True,
        "purpose": (
            "Publish the receipt-bound SDK canonical routing artifact after "
            "exact public-release parity and before owner-routed runtime cutover."
        ),
        "privacy_boundary": (
            "public routing readmodels, schemas, boundary docs, and exact "
            "succession evidence only; no private payloads or runtime state"
        ),
        "subject_repo_root": ".",
        "artifact_source": {
            "kind": "generated_thin_routing_readmodel_canonical",
            "content_identity_ref": "generated/aoa_router.min.json",
            "artifact_identity_ref": (
                "generated/aoa_router.min.json#/artifact_identity"
            ),
            "producer_source_ref": sdk_source_ref,
        },
        "artifact_identity": {
            "artifact_class": ARTIFACT_CLASS,
            "abi_epoch": ABI_EPOCH,
        },
        "abi_subject": {
            "path": "generated/aoa_router.min.json",
            "artifact_identity_pointer": "/artifact_identity",
        },
        "artifact_subjects": _artifact_subjects(),
        "build_type": (
            "urn:abyssos:buildtype:aoa-sdk-routing-g5-canonical:v1"
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
                "python -m aoa_sdk.control_plane.routing.canonical "
                "--check --output-dir CANONICAL_ROOT "
                "--public-release-archive PUBLIC_RELEASE_ASSET "
                "--runtime-consumer-root ABYSS_STACK_ROOT"
            ),
            "consumer_expectation": (
                "Normal runtime requires the latest public-release record, "
                "exact subject store, canonical producer admission, owner-switch "
                "receipt, SDK/predecessor refs, ABI, and all required controls."
            ),
            "registry_required": True,
            "subject_store_required": True,
            "admission_gate": "fail_closed_consumer_admission",
            "consumer_verdict": "runtime_allow_required_before_cutover",
        },
        "consumer_command": [
            (
                "abyss-machine artifacts build-sidecars --manifest "
                "CANONICAL_ROOT/artifact.bundle.json --bundle-dir BUNDLE_DIR"
            ),
            "abyss-machine artifacts sign BUNDLE_DIR",
            "abyss-machine artifacts verify BUNDLE_DIR",
            "abyss-machine artifacts release-check BUNDLE_DIR",
            (
                "abyss-machine artifacts evidence-promote BUNDLE_DIR "
                "--registry-dir REGISTRY_DIR --lifecycle-state release-ready "
                "--consumer-ref abyss-stack:routing-canonical --evidence-ref "
                "BUNDLE_DIR/artifact.verify.json --source-repo aoa-sdk "
                f"--source-ref {sdk_source_ref} "
                "--producer aoa-sdk-routing-canonical-builder "
                "--trust-root-mode public_release --json"
            ),
            (
                "abyss-machine artifacts materialize-subjects BUNDLE_DIR "
                "--store-root SUBJECT_STORE_ROOT --registry-dir REGISTRY_DIR "
                "--manifest CANONICAL_ROOT/artifact.bundle.json "
                "--consumer-intent runtime --source-repo aoa-sdk "
                "--trust-root-mode public_release --json"
            ),
            (
                "abyss-machine artifacts trust-gate --registry-dir REGISTRY_DIR "
                f"--artifact-class {ARTIFACT_CLASS} --consumer-intent runtime "
                "--source-repo aoa-sdk --trust-root-mode public_release "
                "--subject-digest SUBJECT_DIGEST --json"
            ),
        ],
    }


def build_g5_canonical_bundle(
    inputs: RoutingProducerInputs,
    output_root: Path,
    *,
    predecessor_source_ref: str,
    sdk_source_ref: str,
    sdk_version: str,
    input_source_refs: Mapping[str, str],
    public_release_archive: Path,
    public_release_ref: str,
    public_release_source_ref: str,
    public_release_asset_digest: str,
    runtime_consumer_root: Path,
    runtime_consumer_source_ref: str,
    compatibility_started_on: str,
    observed_at: datetime | None = None,
) -> G5RoutingCanonicalBundle:
    """Build one canonical artifact only when every predecessor byte agrees."""

    sdk_ref = _require_source_ref(sdk_source_ref, "sdk_source_ref")
    predecessor_ref = _require_source_ref(
        predecessor_source_ref,
        "predecessor_source_ref",
    )
    release_source_ref = _require_source_ref(
        public_release_source_ref,
        "public_release_source_ref",
    )
    runtime_ref = _require_source_ref(
        runtime_consumer_source_ref,
        "runtime_consumer_source_ref",
    )
    release_digest = _require_sha256(
        public_release_asset_digest,
        "public_release_asset_digest",
    )
    started_on = _require_date(
        compatibility_started_on,
        "compatibility_started_on",
    )
    if not sdk_version or sdk_version.strip() != sdk_version:
        raise RouterError("sdk_version must be a non-empty exact version")
    if not public_release_ref or public_release_ref.strip() != public_release_ref:
        raise RouterError("public_release_ref must be non-empty")
    _require_exact_checkout(
        runtime_consumer_root.resolve(),
        runtime_ref,
        "abyss-stack runtime consumer",
    )
    if not runtime_consumer_root.joinpath(
        "docs/decisions/"
        "ABYSS-STACK-D-0086-receipt-bound-sdk-routing-cutover.md"
    ).is_file():
        raise RouterError("abyss-stack G5 cutover contract is missing")

    timestamp = observed_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise RouterError("observed_at must be timezone-aware")
    if date.fromisoformat(started_on) > timestamp.date():
        raise RouterError(
            "compatibility window cannot start after authorization time"
        )

    resolved_inputs = inputs.resolved()
    target = _fresh_output_root(
        output_root,
        {
            **resolved_inputs.source_roots(),
            "runtime-consumer": runtime_consumer_root.resolve(),
        },
    )
    public_members = _public_release_members(
        public_release_archive,
        expected_digest=release_digest,
        release_source_ref=release_source_ref,
        predecessor_source_ref=predecessor_ref,
    )

    with tempfile.TemporaryDirectory(
        prefix=".aoa-sdk-g5-canonical-candidate-",
        dir=target.parent,
    ) as temporary:
        candidate = build_g5_candidate_bundle(
            resolved_inputs,
            Path(temporary) / "candidate",
            predecessor_source_ref=predecessor_ref,
            sdk_source_ref=sdk_ref,
            input_source_refs=input_source_refs,
            observed_at=timestamp,
        )
        assembly_hashes = _copy_candidate_assembly(
            candidate,
            target,
            public_members,
        )

    receipt = _owner_switch_receipt(
        sdk_source_ref=sdk_ref,
        sdk_version=sdk_version,
        predecessor_source_ref=predecessor_ref,
        public_release_ref=public_release_ref,
        public_release_source_ref=release_source_ref,
        public_release_asset_name=public_release_archive.name,
        public_release_asset_digest=release_digest,
        runtime_consumer_source_ref=runtime_ref,
        compatibility_started_on=started_on,
        authorized_at=timestamp,
    )
    receipt_path = target / OWNER_SWITCH_RECEIPT_REL
    _write_json(receipt_path, receipt)
    provenance = {
        "schema_version": (
            "aoa_sdk_routing_g5_canonical_provenance_v1"
        ),
        "state": "sdk_canonical",
        "publication_posture": "public_release_canonical",
        "canonical_producer": {
            "owner_repo": "aoa-sdk",
            "source_ref": sdk_ref,
            "implementation": "aoa_sdk.control_plane.routing",
        },
        "canonical_predecessor": {
            "owner_repo": "aoa-routing",
            "source_ref": predecessor_ref,
            "posture": (
                "compatibility_security_rollback_deprecation_only"
            ),
        },
        "public_release_trust_root": {
            "release_ref": public_release_ref,
            "source_ref": release_source_ref,
            "asset_name": public_release_archive.name,
            "asset_digest": release_digest,
            "byte_parity": True,
        },
        "runtime_consumer_contract": {
            "owner_repo": "abyss-stack",
            "source_ref": runtime_ref,
            "decision_id": "ABYSS-STACK-D-0086",
            "live_cutover_executed": False,
        },
        "artifact_identity": {
            "artifact_class": ARTIFACT_CLASS,
            "owner_repo": "aoa-sdk",
            "abi_epoch": ABI_EPOCH,
        },
        "assembly_file_sha256": dict(sorted(assembly_hashes.items())),
        "input_source_refs": dict(sorted(input_source_refs.items())),
        "owner_switch_receipt": {
            "path": OWNER_SWITCH_RECEIPT_REL.as_posix(),
            "schema": OWNER_SWITCH_RECEIPT_SCHEMA,
            "status": "g5_switch_authorized",
            "digest": _stable_digest(receipt),
        },
        "observed_at": timestamp.isoformat().replace("+00:00", "Z"),
        "g5_authority": dict(G5_CANONICAL_AUTHORITY),
        "archive_stop_line": ARCHIVE_STOP_LINE,
    }
    provenance_path = target / CANONICAL_PROVENANCE_REL
    _write_json(provenance_path, provenance)
    manifest_path = target / CANONICAL_MANIFEST_REL
    _write_json(manifest_path, _canonical_manifest(sdk_ref))
    bundle = G5RoutingCanonicalBundle(
        output_root=target,
        generated_root=target / "generated",
        provenance_path=provenance_path,
        receipt_path=receipt_path,
        manifest_path=manifest_path,
        sdk_source_ref=sdk_ref,
        predecessor_source_ref=predecessor_ref,
        input_source_refs=dict(sorted(input_source_refs.items())),
    )
    validate_g5_canonical_bundle(
        bundle,
        resolved_inputs,
        public_release_archive=public_release_archive,
        runtime_consumer_root=runtime_consumer_root,
    )
    return bundle


def load_g5_canonical_bundle(
    output_root: Path,
) -> G5RoutingCanonicalBundle:
    target = output_root.expanduser().resolve(strict=True)
    provenance_path = target / CANONICAL_PROVENANCE_REL
    receipt_path = target / OWNER_SWITCH_RECEIPT_REL
    manifest_path = target / CANONICAL_MANIFEST_REL
    provenance = _read_json_object(
        provenance_path,
        "G5 canonical provenance",
    )
    canonical = provenance.get("canonical_producer")
    predecessor = provenance.get("canonical_predecessor")
    refs = provenance.get("input_source_refs")
    if (
        not isinstance(canonical, dict)
        or not isinstance(predecessor, dict)
        or not isinstance(refs, dict)
    ):
        raise RouterError("G5 canonical provenance bindings are missing")
    return G5RoutingCanonicalBundle(
        output_root=target,
        generated_root=target / "generated",
        provenance_path=provenance_path,
        receipt_path=receipt_path,
        manifest_path=manifest_path,
        sdk_source_ref=str(canonical.get("source_ref") or ""),
        predecessor_source_ref=str(predecessor.get("source_ref") or ""),
        input_source_refs={
            str(owner): str(source_ref)
            for owner, source_ref in refs.items()
        },
    )


def validate_g5_canonical_bundle(
    bundle: G5RoutingCanonicalBundle,
    inputs: RoutingProducerInputs,
    *,
    public_release_archive: Path,
    runtime_consumer_root: Path,
) -> None:
    target = bundle.output_root.resolve(strict=True)
    expected_files = set(CANDIDATE_ASSEMBLY_FILES) | {
        OWNER_SWITCH_RECEIPT_REL.as_posix(),
        CANONICAL_PROVENANCE_REL.as_posix(),
        CANONICAL_MANIFEST_REL.as_posix(),
    }
    actual_files: set[str] = set()
    for path in target.rglob("*"):
        if path.is_symlink():
            raise RouterError("G5 canonical bundle must not contain symlinks")
        if path.is_file():
            actual_files.add(path.relative_to(target).as_posix())
        elif not path.is_dir():
            raise RouterError(
                "G5 canonical bundle contains an unsupported entry"
            )
    if actual_files != expected_files:
        raise RouterError(
            "G5 canonical file set drifted; "
            f"missing={sorted(expected_files - actual_files)}, "
            f"extra={sorted(actual_files - expected_files)}"
        )
    actual_directories = {
        path.relative_to(target).as_posix()
        for path in target.rglob("*")
        if path.is_dir() and not path.is_symlink()
    }
    if actual_directories != set(CANDIDATE_DIRECTORIES):
        raise RouterError(
            "G5 canonical directory set drifted; "
            f"missing={sorted(set(CANDIDATE_DIRECTORIES) - actual_directories)}, "
            f"extra={sorted(actual_directories - set(CANDIDATE_DIRECTORIES))}"
        )

    receipt = _read_json_object(
        bundle.receipt_path,
        "G5 owner-switch receipt",
    )
    provenance = _read_json_object(
        bundle.provenance_path,
        "G5 canonical provenance",
    )
    manifest = _read_json_object(
        bundle.manifest_path,
        "G5 canonical manifest",
    )
    try:
        get_schema_validator(
            "routing-g5-owner-switch-receipt.schema.json"
        ).validate(receipt)
        get_schema_validator(
            "routing-g5-canonical-provenance.schema.json"
        ).validate(provenance)
    except ValidationError as exc:
        raise RouterError(
            f"G5 canonical schema violations: {exc.message}"
        ) from exc

    sdk_ref = _require_source_ref(
        bundle.sdk_source_ref,
        "canonical SDK source ref",
    )
    predecessor_ref = _require_source_ref(
        bundle.predecessor_source_ref,
        "canonical predecessor source ref",
    )
    if manifest != _canonical_manifest(sdk_ref):
        raise RouterError("G5 canonical manifest content drifted")
    if receipt.get("g5_authority") != G5_CANONICAL_AUTHORITY:
        raise RouterError("G5 owner-switch authority drifted")
    if provenance.get("g5_authority") != G5_CANONICAL_AUTHORITY:
        raise RouterError("G5 canonical provenance authority drifted")
    if receipt.get("archive_stop_line") != ARCHIVE_STOP_LINE:
        raise RouterError("G5 owner-switch archive stop line drifted")
    if provenance.get("archive_stop_line") != ARCHIVE_STOP_LINE:
        raise RouterError("G5 canonical archive stop line drifted")
    sdk = receipt.get("sdk")
    predecessor = receipt.get("predecessor")
    public_release = receipt.get("public_release")
    runtime_consumer = receipt.get("runtime_consumer")
    if (
        not isinstance(sdk, dict)
        or sdk.get("source_ref") != sdk_ref
        or sdk.get("abi_epoch") != ABI_EPOCH
        or not isinstance(predecessor, dict)
        or predecessor.get("source_ref") != predecessor_ref
        or not isinstance(public_release, dict)
        or not isinstance(runtime_consumer, dict)
    ):
        raise RouterError("G5 owner-switch receipt binding drifted")
    compatibility = receipt.get("compatibility_window")
    if (
        not isinstance(compatibility, dict)
        or compatibility.get("state") != "started"
        or compatibility.get("started_by_sdk_version") != sdk.get("version")
    ):
        raise RouterError("G5 compatibility-window binding drifted")
    release_digest = _require_sha256(
        public_release.get("asset_digest"),
        "receipt public release digest",
    )
    release_source_ref = _require_source_ref(
        public_release.get("source_ref"),
        "receipt public release source ref",
    )
    runtime_ref = _require_source_ref(
        runtime_consumer.get("source_ref"),
        "receipt runtime consumer source ref",
    )
    if public_release.get("asset_name") != public_release_archive.name:
        raise RouterError("G5 public release asset-name binding drifted")
    expected_canonical = {
        "owner_repo": "aoa-sdk",
        "source_ref": sdk_ref,
        "implementation": "aoa_sdk.control_plane.routing",
    }
    expected_predecessor = {
        "owner_repo": "aoa-routing",
        "source_ref": predecessor_ref,
        "posture": "compatibility_security_rollback_deprecation_only",
    }
    expected_public_release = {
        **public_release,
        "byte_parity": True,
    }
    expected_runtime = {
        "owner_repo": "abyss-stack",
        "source_ref": runtime_ref,
        "decision_id": "ABYSS-STACK-D-0086",
        "live_cutover_executed": False,
    }
    if (
        provenance.get("canonical_producer") != expected_canonical
        or provenance.get("canonical_predecessor") != expected_predecessor
        or provenance.get("public_release_trust_root")
        != expected_public_release
        or provenance.get("runtime_consumer_contract") != expected_runtime
        or provenance.get("artifact_identity")
        != {
            "artifact_class": ARTIFACT_CLASS,
            "owner_repo": "aoa-sdk",
            "abi_epoch": ABI_EPOCH,
        }
    ):
        raise RouterError("G5 canonical cross-owner binding drifted")
    _require_exact_checkout(
        runtime_consumer_root.resolve(),
        runtime_ref,
        "abyss-stack runtime consumer",
    )
    public_members = _public_release_members(
        public_release_archive,
        expected_digest=release_digest,
        release_source_ref=release_source_ref,
        predecessor_source_ref=predecessor_ref,
    )
    hashes = provenance.get("assembly_file_sha256")
    if not isinstance(hashes, dict) or set(hashes) != set(
        CANDIDATE_ASSEMBLY_FILES
    ):
        raise RouterError("G5 canonical assembly hash set drifted")
    for relative in CANDIDATE_ASSEMBLY_FILES:
        path = target / relative
        if path.read_bytes() != public_members[relative]:
            raise RouterError(
                "G5 canonical public-release byte parity drifted: "
                f"{relative}"
            )
        if hashes.get(relative) != _sha256(path):
            raise RouterError(
                f"G5 canonical assembly digest drifted: {relative}"
            )
    receipt_summary = provenance.get("owner_switch_receipt")
    if (
        not isinstance(receipt_summary, dict)
        or receipt_summary.get("path")
        != OWNER_SWITCH_RECEIPT_REL.as_posix()
        or receipt_summary.get("schema")
        != OWNER_SWITCH_RECEIPT_SCHEMA
        or receipt_summary.get("status") != receipt.get("status")
        or receipt_summary.get("digest") != _stable_digest(receipt)
    ):
        raise RouterError("G5 canonical receipt digest binding drifted")
    observed_at = _require_timestamp(
        provenance.get("observed_at"),
        "G5 canonical observed_at",
    )
    authorized_at = _require_timestamp(
        receipt.get("authorized_at"),
        "G5 owner-switch authorized_at",
    )
    if observed_at != authorized_at:
        raise RouterError("G5 authorization timestamp binding drifted")
    started_on = _require_date(
        compatibility.get("started_on"),
        "G5 compatibility started_on",
    )
    if date.fromisoformat(started_on) > authorized_at.date():
        raise RouterError(
            "compatibility window cannot start after authorization time"
        )
    resolved_inputs = inputs.resolved()
    issues = validate_generated_outputs(
        bundle.generated_root,
        resolved_inputs.techniques_root,
        resolved_inputs.skills_root,
        resolved_inputs.evals_root,
        resolved_inputs.memo_root,
        resolved_inputs.stats_root,
        resolved_inputs.agents_root,
        resolved_inputs.aoa_root,
        resolved_inputs.playbooks_root,
        resolved_inputs.kag_root,
        resolved_inputs.tos_root,
        resolved_inputs.sdk_root,
        resolved_inputs.source_route_root,
        resolved_inputs.profile_root,
        resolved_inputs.abyss_stack_root,
        REPO_ROOT,
        producer_posture=SDK_G5_CANDIDATE,
    )
    if issues:
        rendered = "; ".join(
            f"{issue.location}: {issue.message}" for issue in issues
        )
        raise RouterError(rendered)

    with tempfile.TemporaryDirectory(
        prefix=".aoa-sdk-g5-canonical-validate-",
        dir=target.parent,
    ) as temporary:
        rebuilt = build_g5_candidate_bundle(
            resolved_inputs,
            Path(temporary) / "candidate",
            predecessor_source_ref=predecessor_ref,
            sdk_source_ref=sdk_ref,
            input_source_refs=bundle.input_source_refs,
            observed_at=_require_timestamp(
                provenance.get("observed_at"),
                "G5 canonical observed_at",
            ),
        )
        for relative in CANDIDATE_ASSEMBLY_FILES:
            if (rebuilt.output_root / relative).read_bytes() != (
                target / relative
            ).read_bytes():
                raise RouterError(
                    f"G5 canonical deterministic rebuild drifted: {relative}"
                )


def write_deterministic_canonical_archive(
    bundle: G5RoutingCanonicalBundle,
    archive_path: Path,
) -> str:
    """Write a path- and zlib-independent canonical routing tar.gz."""

    archive = archive_path.expanduser().absolute()
    archive.parent.mkdir(parents=True, exist_ok=True)
    prefix = Path("aoa-sdk-routing-g5-canonical")
    paths = sorted(
        bundle.output_root.rglob("*"),
        key=lambda path: path.relative_to(bundle.output_root).as_posix(),
    )
    if any(path.is_symlink() for path in paths):
        raise RouterError("canonical archive input must not contain symlinks")
    with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as tar_stream:
        with tarfile.open(
            fileobj=tar_stream,
            mode="w",
            format=tarfile.PAX_FORMAT,
        ) as tar:
            for path in paths:
                relative = path.relative_to(bundle.output_root)
                info = tar.gettarinfo(
                    str(path),
                    arcname=(prefix / relative).as_posix(),
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a receipt-bound SDK canonical routing artifact."
    )
    dependency_args = (
        ("techniques", "aoa-techniques"),
        ("skills", "aoa-skills"),
        ("evals", "aoa-evals"),
        ("memo", "aoa-memo"),
        ("stats", "aoa-stats"),
        ("agents", "aoa-agents"),
        ("aoa", "Agents-of-Abyss"),
        ("playbooks", "aoa-playbooks"),
        ("kag", "aoa-kag"),
        ("tos", "Tree-of-Sophia"),
        ("sdk", "aoa-sdk"),
        ("source-route", "Dionysus"),
        ("profile", "8Dionysus"),
        ("abyss-stack", "abyss-stack"),
    )
    for argument, repo_name in dependency_args:
        parser.add_argument(
            f"--{argument}-root",
            type=Path,
            default=default_dependency_root(repo_name),
        )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--public-release-archive", type=Path, required=True)
    parser.add_argument("--runtime-consumer-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def _inputs_from_args(args: argparse.Namespace) -> RoutingProducerInputs:
    return RoutingProducerInputs(
        techniques_root=args.techniques_root,
        skills_root=args.skills_root,
        evals_root=args.evals_root,
        memo_root=args.memo_root,
        stats_root=args.stats_root,
        agents_root=args.agents_root,
        aoa_root=args.aoa_root,
        playbooks_root=args.playbooks_root,
        kag_root=args.kag_root,
        tos_root=args.tos_root,
        sdk_root=args.sdk_root,
        source_route_root=args.source_route_root,
        profile_root=args.profile_root,
        abyss_stack_root=args.abyss_stack_root,
    )


def main() -> int:
    args = _parse_args()
    if not args.check:
        raise RouterError(
            "canonical module validates existing artifacts only; "
            "use build_routing_g5_canonical.py to build"
        )
    bundle = load_g5_canonical_bundle(args.output_dir)
    validate_g5_canonical_bundle(
        bundle,
        _inputs_from_args(args),
        public_release_archive=args.public_release_archive,
        runtime_consumer_root=args.runtime_consumer_root,
    )
    print(
        f"[ok] validated receipt-bound SDK canonical routing G5 "
        f"{bundle.sdk_source_ref}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RouterError as exc:
        print(f"[error] {exc}")
        raise SystemExit(1)
