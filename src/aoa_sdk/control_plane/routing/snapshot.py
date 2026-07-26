"""Receipt-bound inputs for deterministic Agent OS route resolution."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Literal

from jsonschema.exceptions import ValidationError as JSONSchemaError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ...contracts.control_plane import ABIRef, Digest, ProvenanceRef
from ...contracts.routing import RegistryEntry, RoutingHint
from ...contracts.skills import CapabilityGraph
from ...errors import AoASDKError, RepoNotFound
from ...workspace.discovery import Workspace
from .core import RouterError
from .validator import get_schema_validator


SOURCE_LOCK_RESOURCE = "data/canonical-routing-source-lock.v1.json"
RUNTIME_MANIFEST_PATH = "manifest/federation_mirror_manifest.json"
PACKAGED_SCHEMA_ROOT = Path(__file__).resolve().parent / "schemas"
_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_CANONICAL_LOCKED_PATHS = {
    "cross_repo_registry": "generated/cross_repo_registry.min.json",
    "cross_repo_registry_schema": "schemas/cross-repo-registry.schema.json",
    "router_entry_schema": "schemas/router-entry.schema.json",
    "task_to_surface_hints": "generated/task_to_surface_hints.json",
    "task_to_surface_hints_schema": "schemas/task-to-surface-hints.schema.json",
    "capability_graph": "generated/capability_graph.json",
}


class RoutingSnapshotError(AoASDKError, ValueError):
    """The configured routing snapshot is absent, stale, or not SDK-canonical."""


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LockedArtifact(_StrictModel):
    owner_repo: str = Field(min_length=1)
    relative_path: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    artifact_digest: Digest
    schema_ref: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)


class RoutingABISourceLock(_StrictModel):
    abi_id: Literal["aoa_routing_thin_router_v1"]
    abi_version: Literal["aoa_routing_thin_router_v1"]
    owner_repo: Literal["aoa-sdk"]
    schema_ref: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    artifact_digest: Digest


class RoutingResolutionSourceLock(_StrictModel):
    schema_version: Literal["aoa_control_plane_routing_source_lock_v1"]
    routing_abi: RoutingABISourceLock
    routing_bundle_subject_digest: Digest
    owner_switch_receipt_digest: Digest
    runtime_consumer_source_ref: str = Field(min_length=1)
    runtime_manifest_schema_ref: str = Field(min_length=1)
    cross_repo_registry: LockedArtifact
    cross_repo_registry_schema: LockedArtifact
    router_entry_schema: LockedArtifact
    task_to_surface_hints: LockedArtifact
    task_to_surface_hints_schema: LockedArtifact
    capability_graph: LockedArtifact
    owner_source_refs: dict[str, str]


@dataclass(frozen=True, slots=True)
class RoutingResolutionSnapshot:
    source_lock: RoutingResolutionSourceLock
    registry_entries: tuple[RegistryEntry, ...]
    routing_hints: dict[str, RoutingHint]
    capability_graph: CapabilityGraph
    input_snapshot_digest: str
    routing_registry_provenance: ProvenanceRef
    capability_graph_provenance: ProvenanceRef
    runtime_mirror_provenance: ProvenanceRef
    routing_abi: ABIRef


def load_routing_resolution_snapshot(
    workspace: Workspace,
    *,
    routing_bundle_root: str | Path | None = None,
    source_lock_path: str | Path | None = None,
) -> RoutingResolutionSnapshot:
    """Load the exact canonical bundle and its pinned owner projection."""

    bundle_root = _resolve_bundle_root(workspace, routing_bundle_root)
    source_lock, source_lock_bytes = _load_source_lock(
        source_lock_path or workspace.routing_source_lock_path
    )

    registry_bytes = _read_locked_bundle_artifact(
        bundle_root, source_lock.cross_repo_registry
    )
    registry_schema_bytes = _read_locked_bundle_artifact(
        bundle_root, source_lock.cross_repo_registry_schema
    )
    router_entry_schema_bytes = _read_locked_bundle_artifact(
        bundle_root, source_lock.router_entry_schema
    )
    hints_bytes = _read_locked_bundle_artifact(
        bundle_root, source_lock.task_to_surface_hints
    )
    hints_schema_bytes = _read_locked_bundle_artifact(
        bundle_root, source_lock.task_to_surface_hints_schema
    )
    manifest_path = bundle_root / RUNTIME_MANIFEST_PATH
    manifest_bytes = _read_bytes(manifest_path, "routing runtime manifest")

    registry_payload = _decode_json(registry_bytes, "cross-repo routing registry")
    _decode_json(registry_schema_bytes, "cross-repo routing registry schema")
    _decode_json(router_entry_schema_bytes, "routing registry entry schema")
    hints_payload = _decode_json(hints_bytes, "task-to-surface hints")
    _decode_json(hints_schema_bytes, "task-to-surface hints schema")
    manifest = _decode_json(manifest_bytes, "routing runtime manifest")
    _assert_packaged_schema_bytes(
        source_lock.cross_repo_registry.schema_ref,
        registry_schema_bytes,
    )
    _assert_packaged_schema_bytes(
        source_lock.router_entry_schema.schema_ref,
        router_entry_schema_bytes,
    )
    _assert_packaged_schema_bytes(
        source_lock.task_to_surface_hints.schema_ref,
        hints_schema_bytes,
    )
    _validate_json_schema(
        registry_payload,
        source_lock.cross_repo_registry.schema_ref,
        "routing registry",
    )
    _validate_json_schema(
        hints_payload,
        source_lock.task_to_surface_hints.schema_ref,
        "routing hints",
    )
    _validate_runtime_manifest(manifest, source_lock, registry_bytes, hints_bytes)

    try:
        entries = tuple(
            RegistryEntry.model_validate(item)
            for item in registry_payload.get("entries", ())
        )
        hints = {
            hint.kind: hint
            for hint in (
                RoutingHint.model_validate(item)
                for item in hints_payload.get("hints", ())
            )
        }
    except ValidationError as exc:
        raise RoutingSnapshotError(
            f"routing snapshot contains an invalid typed record: {exc}"
        ) from exc
    if not entries:
        raise RoutingSnapshotError("routing registry contains no entries")
    entry_keys = [(entry.repo, entry.kind, entry.id) for entry in entries]
    if len(entry_keys) != len(set(entry_keys)):
        raise RoutingSnapshotError("routing registry entry identities must be unique")
    if len(hints) != len(hints_payload.get("hints", ())):
        raise RoutingSnapshotError("routing hint kinds must be unique")

    capability_graph_bytes = _read_locked_git_artifact(
        workspace, source_lock.capability_graph
    )
    try:
        capability_graph = CapabilityGraph.model_validate(
            _decode_json(capability_graph_bytes, "aoa-skills capability graph")
        )
    except ValidationError as exc:
        raise RoutingSnapshotError(
            f"pinned aoa-skills capability graph is invalid: {exc}"
        ) from exc

    registry_provenance = _artifact_provenance(
        source_lock.cross_repo_registry
    )
    graph_provenance = _artifact_provenance(source_lock.capability_graph)
    manifest_digest = _sha256(manifest_bytes)
    mirror_provenance = ProvenanceRef(
        owner_repo="abyss-stack",
        artifact_ref=RUNTIME_MANIFEST_PATH,
        source_ref=source_lock.runtime_consumer_source_ref,
        artifact_digest=manifest_digest,
        schema_ref=source_lock.runtime_manifest_schema_ref,
        schema_version=str(manifest.get("schema", "unknown")),
    )
    snapshot_identity = {
        "source_lock_digest": _sha256(source_lock_bytes),
        "runtime_manifest_digest": manifest_digest,
        "routing_registry_digest": _sha256(registry_bytes),
        "routing_hints_digest": _sha256(hints_bytes),
        "capability_graph_digest": _sha256(capability_graph_bytes),
        "routing_bundle_subject_digest": source_lock.routing_bundle_subject_digest,
        "owner_switch_receipt_digest": source_lock.owner_switch_receipt_digest,
    }
    return RoutingResolutionSnapshot(
        source_lock=source_lock,
        registry_entries=entries,
        routing_hints=hints,
        capability_graph=capability_graph,
        input_snapshot_digest=_canonical_digest(snapshot_identity),
        routing_registry_provenance=registry_provenance,
        capability_graph_provenance=graph_provenance,
        runtime_mirror_provenance=mirror_provenance,
        routing_abi=ABIRef.model_validate(source_lock.routing_abi.model_dump()),
    )


def _resolve_bundle_root(
    workspace: Workspace,
    override: str | Path | None,
) -> Path:
    selected = (
        Path(override).expanduser().resolve(strict=False)
        if override is not None
        else workspace.routing_bundle_root
    )
    if selected is None:
        raise RoutingSnapshotError(
            "no explicit routing bundle configured; set "
            "AOA_SDK_ROUTING_BUNDLE_ROOT or "
            "[control_plane].routing_bundle_root"
        )
    if not selected.is_dir():
        raise RoutingSnapshotError(
            f"explicit routing bundle root does not exist: {selected}"
        )
    return selected


def _load_source_lock(
    path: str | Path | None,
) -> tuple[RoutingResolutionSourceLock, bytes]:
    try:
        if path is None:
            resource = resources.files("aoa_sdk.control_plane.routing").joinpath(
                SOURCE_LOCK_RESOURCE
            )
            raw = resource.read_bytes()
        else:
            raw = _read_bytes(
                Path(path).expanduser().resolve(strict=False),
                "routing source lock",
            )
        lock = RoutingResolutionSourceLock.model_validate(
            _decode_json(raw, "routing source lock")
        )
    except (OSError, ValidationError) as exc:
        raise RoutingSnapshotError(f"invalid routing source lock: {exc}") from exc
    sdk_source_ref = lock.routing_abi.source_ref
    if not _OID_RE.fullmatch(sdk_source_ref):
        raise RoutingSnapshotError(
            "routing source lock must name an exact canonical SDK Git OID"
        )
    if not _OID_RE.fullmatch(lock.runtime_consumer_source_ref):
        raise RoutingSnapshotError(
            "routing source lock must name an exact runtime-consumer Git OID"
        )
    if lock.owner_source_refs.get("aoa-sdk") != sdk_source_ref:
        raise RoutingSnapshotError(
            "routing source lock must bind aoa-sdk to the canonical ABI source ref"
        )
    sdk_artifacts = (
        lock.cross_repo_registry,
        lock.cross_repo_registry_schema,
        lock.router_entry_schema,
        lock.task_to_surface_hints,
        lock.task_to_surface_hints_schema,
    )
    if any(
        artifact.owner_repo != "aoa-sdk"
        or artifact.source_ref != sdk_source_ref
        for artifact in sdk_artifacts
    ):
        raise RoutingSnapshotError(
            "routing bundle artifacts must share the canonical aoa-sdk source ref"
        )
    if (
        lock.capability_graph.owner_repo != "aoa-skills"
        or lock.owner_source_refs.get("aoa-skills")
        != lock.capability_graph.source_ref
    ):
        raise RoutingSnapshotError(
            "capability graph must match the pinned aoa-skills source ref"
        )
    for field_name, expected_path in _CANONICAL_LOCKED_PATHS.items():
        artifact = getattr(lock, field_name)
        if artifact.relative_path != expected_path:
            raise RoutingSnapshotError(
                f"routing source lock field {field_name!r} must use "
                f"canonical path {expected_path!r}"
            )
        _require_safe_relative_path(artifact.relative_path, field_name)
    return lock, raw


def _read_locked_bundle_artifact(
    root: Path,
    artifact: LockedArtifact,
) -> bytes:
    raw = _read_bytes(root / artifact.relative_path, artifact.relative_path)
    _assert_digest(raw, artifact)
    return raw


def _read_locked_git_artifact(
    workspace: Workspace,
    artifact: LockedArtifact,
) -> bytes:
    if not _OID_RE.fullmatch(artifact.source_ref):
        raise RoutingSnapshotError(
            f"pinned source ref for {artifact.owner_repo} is not an exact Git OID"
        )
    try:
        repo_root = workspace.repo_path(artifact.owner_repo)
    except RepoNotFound as exc:
        raise RoutingSnapshotError(
            f"required owner repository is unavailable: {artifact.owner_repo}"
        ) from exc
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "show",
            f"{artifact.source_ref}:{artifact.relative_path}",
        ],
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RoutingSnapshotError(
            f"cannot read pinned {artifact.owner_repo}:{artifact.relative_path}"
            f"@{artifact.source_ref}: {detail or 'git show failed'}"
        )
    _assert_digest(result.stdout, artifact)
    return result.stdout


def _validate_runtime_manifest(
    manifest: dict,
    lock: RoutingResolutionSourceLock,
    registry_bytes: bytes,
    hints_bytes: bytes,
) -> None:
    expected_authority = {
        "archive_authorized": False,
        "canonical_producer_switch_authorized": True,
        "compatibility_window_started": True,
        "live_runtime_mutation_authorized": True,
        "predecessor_maintenance_only": True,
        "sdk_canonical": True,
    }
    required_equalities = {
        "schema": "abyss_stack_federation_mirror_manifest_v1",
        "layer": "aoa-routing",
        "source_git_commit": lock.routing_abi.source_ref,
        "routing_producer_posture": "sdk_canonical",
        "cutover_activation_mode": "authorized_live_cutover",
        "mirror_is_authority": False,
        "artifact_subject_digest": lock.routing_bundle_subject_digest,
        "owner_switch_receipt_digest": lock.owner_switch_receipt_digest,
    }
    for field, expected in required_equalities.items():
        if manifest.get(field) != expected:
            raise RoutingSnapshotError(
                f"routing runtime manifest field {field!r} is not {expected!r}"
            )
    if manifest.get("g5_authority") != expected_authority:
        raise RoutingSnapshotError(
            "routing runtime manifest does not carry the exact G5 authority posture"
        )
    canonical = manifest.get("canonical_producer", {})
    if canonical != {
        "owner_repo": "aoa-sdk",
        "source_ref": lock.routing_abi.source_ref,
    }:
        raise RoutingSnapshotError(
            "routing runtime manifest does not name the locked SDK canonical producer"
        )
    receipt = manifest.get("owner_switch_receipt", {})
    if (
        not isinstance(receipt, dict)
        or _canonical_digest(receipt) != lock.owner_switch_receipt_digest
    ):
        raise RoutingSnapshotError(
            "routing owner-switch receipt does not match the locked digest"
        )
    receipt_sdk = receipt.get("sdk")
    receipt_runtime_consumer = receipt.get("runtime_consumer")
    if (
        receipt.get("schema") != "aoa_sdk_routing_g5_owner_switch_receipt_v1"
        or receipt.get("status") != "g5_switch_authorized"
        or receipt.get("g5_authority") != expected_authority
        or not isinstance(receipt_sdk, dict)
        or receipt_sdk.get("source_ref") != lock.routing_abi.source_ref
        or not isinstance(receipt_runtime_consumer, dict)
        or receipt_runtime_consumer.get("owner_repo") != "abyss-stack"
        or receipt_runtime_consumer.get("source_ref")
        != lock.runtime_consumer_source_ref
    ):
        raise RoutingSnapshotError(
            "routing owner-switch receipt is missing or outside the locked scope"
        )
    trust = _require_manifest_object(
        manifest.get("trust_verdict"),
        "routing runtime trust verdict",
    )
    trust_decision = _require_manifest_object(
        trust.get("decision"),
        "routing runtime trust decision",
    )
    if (
        trust.get("ok") is not True
        or trust.get("verdict") != "allow"
        or trust.get("subject_digest") != lock.routing_bundle_subject_digest
        or trust_decision.get("allow") is not True
    ):
        raise RoutingSnapshotError(
            "routing runtime trust verdict is not an exact allow for the locked subject"
        )
    trust_record = _require_manifest_object(
        trust.get("record"),
        "routing runtime trust record",
    )
    producer_admission = _require_manifest_object(
        trust_record.get("producer_admission"),
        "routing runtime canonical producer admission",
    )
    receipt_summary = _require_manifest_object(
        producer_admission.get("owner_switch_receipt"),
        "routing runtime canonical producer receipt summary",
    )
    if (
        producer_admission.get("profile_id") != "aoa-sdk-g5-canonical"
        or producer_admission.get("owner_repo") != "aoa-sdk"
        or producer_admission.get("canonical_owner_repo") != "aoa-sdk"
        or producer_admission.get("source_ref") != lock.routing_abi.source_ref
        or producer_admission.get("status") != "canonical_producer"
        or producer_admission.get("g5_authority") != expected_authority
        or receipt_summary.get("digest") != lock.owner_switch_receipt_digest
    ):
        raise RoutingSnapshotError(
            "routing runtime trust verdict lacks the exact canonical producer admission"
        )
    file_hashes = _require_manifest_object(
        manifest.get("file_sha256"),
        "routing runtime manifest file hashes",
    )
    expected_hashes = {
        "generated/aoa_router.min.json": (
            lock.routing_abi.artifact_digest.removeprefix("sha256:")
        ),
        lock.cross_repo_registry.relative_path: _sha256(registry_bytes).removeprefix(
            "sha256:"
        ),
        lock.task_to_surface_hints.relative_path: _sha256(hints_bytes).removeprefix(
            "sha256:"
        ),
        lock.cross_repo_registry_schema.relative_path: (
            lock.cross_repo_registry_schema.artifact_digest.removeprefix("sha256:")
        ),
        lock.router_entry_schema.relative_path: (
            lock.router_entry_schema.artifact_digest.removeprefix("sha256:")
        ),
        lock.task_to_surface_hints_schema.relative_path: (
            lock.task_to_surface_hints_schema.artifact_digest.removeprefix("sha256:")
        ),
    }
    for relative_path, digest in expected_hashes.items():
        if file_hashes.get(relative_path) != digest:
            raise RoutingSnapshotError(
                f"routing runtime manifest hash mismatch for {relative_path}"
            )


def _require_manifest_object(
    value: object,
    label: str,
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RoutingSnapshotError(f"{label} must be a JSON object")
    return value


def _validate_json_schema(
    payload: object,
    schema_ref: str,
    label: str,
) -> None:
    try:
        get_schema_validator(Path(schema_ref).name).validate(payload)
    except (RouterError, JSONSchemaError) as exc:
        raise RoutingSnapshotError(f"{label} schema validation failed: {exc}") from exc


def _assert_packaged_schema_bytes(schema_ref: str, locked_bytes: bytes) -> None:
    schema_name = Path(schema_ref).name
    packaged_bytes = _read_bytes(
        PACKAGED_SCHEMA_ROOT / schema_name,
        f"packaged routing schema {schema_name}",
    )
    if packaged_bytes != locked_bytes:
        raise RoutingSnapshotError(
            f"packaged routing schema {schema_name} differs from the source lock"
        )


def _artifact_provenance(artifact: LockedArtifact) -> ProvenanceRef:
    return ProvenanceRef(
        owner_repo=artifact.owner_repo,
        artifact_ref=artifact.relative_path,
        source_ref=artifact.source_ref,
        artifact_digest=artifact.artifact_digest,
        schema_ref=artifact.schema_ref,
        schema_version=artifact.schema_version,
    )


def _require_safe_relative_path(value: str, label: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise RoutingSnapshotError(
            f"routing source lock field {label!r} is not a safe relative path"
        )


def _assert_digest(raw: bytes, artifact: LockedArtifact) -> None:
    actual = _sha256(raw)
    if actual != artifact.artifact_digest:
        raise RoutingSnapshotError(
            f"digest mismatch for {artifact.owner_repo}:{artifact.relative_path}; "
            f"expected {artifact.artifact_digest}, got {actual}"
        )


def _read_bytes(path: Path, label: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RoutingSnapshotError(f"cannot read {label} at {path}: {exc}") from exc


def _decode_json(raw: bytes, label: str) -> dict:
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RoutingSnapshotError(f"{label} is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RoutingSnapshotError(f"{label} must be a JSON object")
    return payload


def _sha256(raw: bytes) -> str:
    return f"sha256:{hashlib.sha256(raw).hexdigest()}"


def _canonical_digest(payload: object) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(raw)
