"""Build and validate a non-publishing SDK routing G5 candidate assembly."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .core import REPO_ROOT, RouterError, default_dependency_root
from .identity import SDK_G5_CANDIDATE, SDK_OWNER_REPO, apply_routing_producer_posture
from .producer import build_outputs, render_output_text
from .shadow import RoutingProducerInputs
from .validator import (
    OUTPUT_SCHEMA_NAMES,
    SCHEMA_ROOT,
    get_schema_validator,
    validate_generated_outputs,
)


CANDIDATE_PROVENANCE_REL = Path(
    "succession/routing-g5-candidate-provenance.json"
)
CANDIDATE_MANIFEST_REL = Path("artifact.bundle.json")
RUNTIME_COMPATIBILITY_ROOT = Path(__file__).resolve().parent / "runtime_compatibility"
GIT_OBJECT_ID_PATTERN = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
RFC3339_TIMESTAMP_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
)

ARTIFACT_FILENAMES = tuple(sorted(OUTPUT_SCHEMA_NAMES))
RUNTIME_GENERATED_FILENAMES = (
    "aoa_router.min.json",
    "cross_repo_registry.min.json",
    "task_to_surface_hints.json",
    "task_to_tier_hints.json",
    "recommended_paths.min.json",
    "pairing_hints.min.json",
    "kag_source_lift_relation_hints.min.json",
    "federation_entrypoints.min.json",
    "return_navigation_hints.min.json",
    "tiny_model_entrypoints.json",
)
RUNTIME_SCHEMA_FILENAMES = (
    "aoa-router.schema.json",
    "cross-repo-registry.schema.json",
    "task-to-surface-hints.schema.json",
    "task-to-tier-hints.schema.json",
    "recommended-paths.schema.json",
    "pairing-hints.schema.json",
    "kag-source-lift-relation-hints.schema.json",
    "federation-entrypoints.schema.json",
    "return-navigation-hints.schema.json",
    "tiny-model-entrypoints.schema.json",
    "router-entry.schema.json",
)
RUNTIME_DOC_FILENAMES = (
    "FEDERATION_ENTRY_ABI.md",
    "RECURRENCE_NAVIGATION_BOUNDARY.md",
)
RUNTIME_REQUIRED_FILES = tuple(
    [f"docs/{name}" for name in RUNTIME_DOC_FILENAMES]
    + [f"generated/{name}" for name in RUNTIME_GENERATED_FILENAMES]
    + [f"schemas/{name}" for name in RUNTIME_SCHEMA_FILENAMES]
)
CANDIDATE_ASSEMBLY_FILES = tuple(
    sorted(
        {f"generated/{name}" for name in ARTIFACT_FILENAMES}
        | {f"schemas/{name}" for name in RUNTIME_SCHEMA_FILENAMES}
        | {f"docs/{name}" for name in RUNTIME_DOC_FILENAMES}
    )
)
CANDIDATE_DIRECTORIES = (
    "docs",
    "generated",
    "schemas",
    "succession",
)
AUTHORITY_STOP_LINE = (
    "This assembly is a non-publishing SDK G5 candidate only. "
    "aoa-routing remains canonical; durable trust admission, live runtime "
    "cutover, the G5 receipt, predecessor maintenance-only posture, the "
    "compatibility window, and archival authority remain separate gates."
)


@dataclass(frozen=True)
class G5RoutingCandidateBundle:
    output_root: Path
    generated_root: Path
    provenance_path: Path
    manifest_path: Path
    artifact_sha256: Mapping[str, str]
    assembly_file_sha256: Mapping[str, str]
    input_source_refs: Mapping[str, str]
    predecessor_source_ref: str
    sdk_source_ref: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RouterError(f"could not load {label}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RouterError(f"{label} must contain an object")
    return payload


def _mapping_field(
    payload: Mapping[str, Any],
    field_name: str,
    label: str,
) -> dict[str, Any]:
    value = payload.get(field_name)
    if not isinstance(value, dict):
        raise RouterError(f"{label} {field_name} must contain an object")
    return dict(value)


def _require_source_ref(value: object, location: str) -> str:
    if not isinstance(value, str):
        raise RouterError(f"{location} must be a full lowercase Git object ID")
    if value != value.strip() or value != value.lower():
        raise RouterError(f"{location} must be a full lowercase Git object ID")
    if not GIT_OBJECT_ID_PATTERN.fullmatch(value):
        raise RouterError(f"{location} must be a full lowercase Git object ID")
    return value


def _require_observed_at(value: object) -> datetime:
    if not isinstance(value, str) or not RFC3339_TIMESTAMP_PATTERN.fullmatch(value):
        raise RouterError(
            "G5 candidate provenance observed_at must be an RFC 3339 timestamp"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RouterError(
            "G5 candidate provenance observed_at must be an RFC 3339 timestamp"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RouterError(
            "G5 candidate provenance observed_at must include an offset"
        )
    return parsed


def _require_exact_input_refs(
    inputs: RoutingProducerInputs,
    input_source_refs: Mapping[str, str],
) -> dict[str, str]:
    expected_names = set(inputs.source_roots())
    if set(input_source_refs) != expected_names:
        missing = sorted(expected_names - set(input_source_refs))
        extra = sorted(set(input_source_refs) - expected_names)
        raise RouterError(
            "input_source_refs must match producer inputs; "
            f"missing={missing}, extra={extra}"
        )
    return {
        name: _require_source_ref(ref, f"input_source_refs[{name!r}]")
        for name, ref in sorted(input_source_refs.items())
    }


def _require_exact_git_source_refs(
    inputs: RoutingProducerInputs,
    input_source_refs: Mapping[str, str],
) -> None:
    """Bind every consumed working tree to the exact clean Git ref claimed."""

    for name, root in sorted(inputs.resolved().source_roots().items()):
        try:
            head = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            status = subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "status",
                    "--porcelain",
                    "--untracked-files=all",
                ],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError) as exc:
            raise RouterError(
                f"producer input {name} must be an exact Git checkout: {root}"
            ) from exc
        if head != input_source_refs[name]:
            raise RouterError(
                f"producer input {name} HEAD {head} does not match "
                f"{input_source_refs[name]}"
            )
        if status:
            raise RouterError(
                f"producer input {name} must be clean before provenance capture"
            )


def _fresh_candidate_root(
    output_root: Path,
    forbidden_roots: Mapping[str, Path],
) -> Path:
    requested_target = output_root.expanduser().absolute()
    if requested_target.is_symlink():
        raise RouterError("G5 candidate output root must not be a symlink")
    target = requested_target.resolve()
    if target.name == "generated":
        raise RouterError("G5 candidate output root must not be named 'generated'")
    for owner, root in sorted(forbidden_roots.items()):
        resolved_root = root.resolve()
        if target == resolved_root or resolved_root in target.parents:
            raise RouterError(
                "G5 candidate output root must stay outside producer inputs; "
                f"target is inside {owner}"
            )
    if target.exists() and not target.is_dir():
        raise RouterError("G5 candidate output root must be a directory")
    if target.exists() and any(target.iterdir()):
        raise RouterError("G5 candidate output root must be absent or empty")
    target.mkdir(parents=True, exist_ok=True)
    return target


def _artifact_subjects() -> list[dict[str, str]]:
    subjects: list[dict[str, str]] = []
    for rel_path in CANDIDATE_ASSEMBLY_FILES:
        if rel_path.startswith("generated/"):
            role = "routing_readmodel"
        elif rel_path.startswith("schemas/"):
            role = "routing_schema"
        else:
            role = "runtime_compatibility_boundary"
        subjects.append({"path": rel_path, "role": role})
    subjects.append(
        {
            "path": CANDIDATE_PROVENANCE_REL.as_posix(),
            "role": "owner_succession_candidate_provenance",
        }
    )
    return subjects


def _candidate_manifest(sdk_source_ref: str) -> dict[str, Any]:
    return {
        "schema": "abyss_machine_artifact_bundle_manifest_v1",
        "id": f"aoa-sdk-routing-g5-candidate-{sdk_source_ref[:16]}",
        "artifact_class": "thin_routing_readmodel_bundle",
        "owner_repo": SDK_OWNER_REPO,
        "policy_ref": (
            "repo:abyss-machine/manifests/artifact_signature_policy.manifest.json"
        ),
        "mode": "os_abyss_local",
        "public_safe": True,
        "purpose": (
            "Non-publishing SDK routing-owner candidate for stronger-owner trust "
            "review and isolated runtime canary admission."
        ),
        "subject_repo_root": ".",
        "artifact_source": {
            "kind": "generated_thin_routing_readmodel_family",
            "content_identity_ref": "generated/aoa_router.min.json",
            "artifact_identity_ref": (
                "generated/aoa_router.min.json#/artifact_identity"
            ),
            "producer_source_ref": sdk_source_ref,
        },
        "artifact_identity": {
            "artifact_class": "thin_routing_readmodel_bundle",
            "abi_epoch": "aoa_routing_thin_router_v1",
        },
        "abi_subject": {
            "path": "generated/aoa_router.min.json",
            "artifact_identity_pointer": "/artifact_identity",
        },
        "artifact_subjects": _artifact_subjects(),
        "build_type": "urn:abyssos:buildtype:aoa-sdk-routing-readmodel:v1",
        "package": {
            "ecosystem": "generated-readmodel",
            "name": "aoa-sdk-routing-readmodel",
            "purl": f"pkg:generic/aoa-sdk-routing-readmodel@{sdk_source_ref}",
        },
        "lifecycle": {
            "initial_state": "candidate",
            "promotion_path": [
                "candidate",
                "built-local",
                "manually-verified",
                "superseded",
                "revoked",
            ],
            "latest_eligible_states": ["manually-verified"],
        },
        "consumer_contract": {
            "stable_interface": (
                "python -m aoa_sdk.control_plane.routing.candidate "
                "--check --output-dir CANDIDATE_ROOT"
            ),
            "consumer_expectation": (
                "Consumers admit only the exact SDK source ref and artifact-subject "
                "digest after ABI, SBOM, SLSA/in-toto, durable registry, subject "
                "store, source-owner, latest-record, and runtime-intent checks pass."
            ),
            "registry_required": True,
            "subject_store_required": True,
            "admission_gate": "fail_closed_consumer_admission",
            "consumer_verdict": "allow_or_deny_required_before_use",
        },
        "consumer_command": [
            (
                "abyss-machine artifacts build-sidecars --manifest "
                "CANDIDATE_ROOT/artifact.bundle.json --bundle-dir BUNDLE_DIR"
            ),
            "abyss-machine artifacts sign BUNDLE_DIR",
            "abyss-machine artifacts verify BUNDLE_DIR",
            "abyss-machine artifacts release-check BUNDLE_DIR",
            (
                "abyss-machine artifacts evidence-promote BUNDLE_DIR "
                "--registry-dir REGISTRY_DIR --lifecycle-state manually-verified "
                "--consumer-ref abyss-stack:routing-canary --evidence-ref "
                "BUNDLE_DIR/artifact.verify.json --source-repo aoa-sdk "
                f"--source-ref {sdk_source_ref} "
                "--producer aoa-sdk-routing-readmodel-builder "
                "--trust-root-mode host_managed --json"
            ),
            (
                "abyss-machine artifacts materialize-subjects BUNDLE_DIR "
                "--store-root SUBJECT_STORE_ROOT --registry-dir REGISTRY_DIR "
                "--manifest CANDIDATE_ROOT/artifact.bundle.json "
                "--consumer-intent runtime_canary --source-repo aoa-sdk "
                "--trust-root-mode host_managed --json"
            ),
            (
                "abyss-machine artifacts trust-gate --registry-dir REGISTRY_DIR "
                "--artifact-class thin_routing_readmodel_bundle "
                "--consumer-intent runtime_canary --source-repo aoa-sdk "
                "--trust-root-mode host_managed --subject-digest SUBJECT_DIGEST "
                "--json"
            ),
            (
                "abyss-machine artifacts registry-latest --registry-dir "
                "REGISTRY_DIR --artifact-class thin_routing_readmodel_bundle "
                "--consumer-intent runtime_canary --source-repo aoa-sdk "
                "--trust-root-mode host_managed --json"
            ),
        ],
    }


def build_g5_candidate_bundle(
    inputs: RoutingProducerInputs,
    output_root: Path,
    *,
    predecessor_source_ref: str,
    sdk_source_ref: str,
    input_source_refs: Mapping[str, str],
    observed_at: datetime | None = None,
) -> G5RoutingCandidateBundle:
    """Build a standalone SDK-identified candidate without authorizing G5."""

    predecessor_ref = _require_source_ref(
        predecessor_source_ref,
        "predecessor_source_ref",
    )
    sdk_ref = _require_source_ref(sdk_source_ref, "sdk_source_ref")
    resolved_inputs = inputs.resolved()
    normalized_input_refs = _require_exact_input_refs(
        resolved_inputs,
        input_source_refs,
    )
    if normalized_input_refs["aoa-sdk"] != sdk_ref:
        raise RouterError(
            "sdk_source_ref must match input_source_refs['aoa-sdk']"
        )
    _require_exact_git_source_refs(resolved_inputs, normalized_input_refs)

    timestamp = observed_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise RouterError("observed_at must be timezone-aware")

    target = _fresh_candidate_root(
        output_root,
        resolved_inputs.source_roots(),
    )
    generated_root = target / "generated"
    generated_root.mkdir()
    outputs = apply_routing_producer_posture(
        build_outputs(
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
        ),
        SDK_G5_CANDIDATE,
    )
    artifact_sha256: dict[str, str] = {}
    for filename, payload in outputs.items():
        rendered = render_output_text(filename, payload)
        path = generated_root / filename
        path.write_text(rendered, encoding="utf-8", newline="\n")
        artifact_sha256[filename] = hashlib.sha256(
            rendered.encode("utf-8")
        ).hexdigest()

    schema_target = target / "schemas"
    schema_target.mkdir()
    for filename in RUNTIME_SCHEMA_FILENAMES:
        shutil.copy2(SCHEMA_ROOT / filename, schema_target / filename)
    docs_target = target / "docs"
    docs_target.mkdir()
    for filename in RUNTIME_DOC_FILENAMES:
        shutil.copy2(
            RUNTIME_COMPATIBILITY_ROOT / filename,
            docs_target / filename,
        )

    assembly_file_sha256 = {
        rel_path: _sha256(target / rel_path)
        for rel_path in CANDIDATE_ASSEMBLY_FILES
    }
    provenance = {
        "schema_version": "aoa_sdk_routing_g5_candidate_provenance_v1",
        "state": "sdk_g5_candidate",
        "publication_posture": "non_publishing_canary",
        "current_canonical_producer": {
            "owner_repo": "aoa-routing",
            "source_ref": predecessor_ref,
        },
        "candidate_producer": {
            "owner_repo": SDK_OWNER_REPO,
            "source_ref": sdk_ref,
            "implementation": "aoa_sdk.control_plane.routing",
        },
        "candidate_artifact_identity": {
            "artifact_class": "thin_routing_readmodel_bundle",
            "owner_repo": SDK_OWNER_REPO,
            "abi_epoch": "aoa_routing_thin_router_v1",
        },
        "abi_epoch": "aoa_routing_thin_router_v1",
        "artifact_sha256": dict(sorted(artifact_sha256.items())),
        "assembly_file_sha256": assembly_file_sha256,
        "input_source_refs": normalized_input_refs,
        "observed_at": timestamp.isoformat().replace("+00:00", "Z"),
        "trust_posture": {
            "artifact_class": "thin_routing_readmodel_bundle",
            "required_controls": [
                "abi_signature",
                "sbom",
                "slsa_in_toto",
            ],
            "stronger_owner": "abyss-machine",
            "admission_status": "pending_stronger_owner",
            "runtime_consumer": "abyss-stack",
        },
        "g5_authority": {
            "canonical_producer_switch_authorized": False,
            "sdk_canonical": False,
            "live_runtime_mutation_authorized": False,
            "predecessor_maintenance_only": False,
            "compatibility_window_started": False,
            "archive_authorized": False,
        },
        "authority_stop_line": AUTHORITY_STOP_LINE,
    }
    provenance_path = target / CANDIDATE_PROVENANCE_REL
    provenance_path.parent.mkdir()
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    manifest_path = target / CANDIDATE_MANIFEST_REL
    manifest_path.write_text(
        json.dumps(
            _candidate_manifest(sdk_ref),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    bundle = G5RoutingCandidateBundle(
        output_root=target,
        generated_root=generated_root,
        provenance_path=provenance_path,
        manifest_path=manifest_path,
        artifact_sha256=artifact_sha256,
        assembly_file_sha256=assembly_file_sha256,
        input_source_refs=normalized_input_refs,
        predecessor_source_ref=predecessor_ref,
        sdk_source_ref=sdk_ref,
    )
    validate_g5_candidate_bundle(bundle, resolved_inputs)
    return bundle


def load_g5_candidate_bundle(output_root: Path) -> G5RoutingCandidateBundle:
    target = output_root.resolve()
    provenance_path = target / CANDIDATE_PROVENANCE_REL
    provenance = _read_json_object(
        provenance_path,
        "G5 candidate provenance",
    )
    current = provenance.get("current_canonical_producer")
    candidate = provenance.get("candidate_producer")
    if not isinstance(current, dict) or not isinstance(candidate, dict):
        raise RouterError("G5 candidate provenance producer bindings are missing")
    return G5RoutingCandidateBundle(
        output_root=target,
        generated_root=target / "generated",
        provenance_path=provenance_path,
        manifest_path=target / CANDIDATE_MANIFEST_REL,
        artifact_sha256=_mapping_field(
            provenance,
            "artifact_sha256",
            "G5 candidate provenance",
        ),
        assembly_file_sha256=_mapping_field(
            provenance,
            "assembly_file_sha256",
            "G5 candidate provenance",
        ),
        input_source_refs=_mapping_field(
            provenance,
            "input_source_refs",
            "G5 candidate provenance",
        ),
        predecessor_source_ref=str(current.get("source_ref") or ""),
        sdk_source_ref=str(candidate.get("source_ref") or ""),
    )


def validate_g5_candidate_bundle(
    bundle: G5RoutingCandidateBundle,
    inputs: RoutingProducerInputs,
) -> None:
    """Fail closed on candidate content, schema, source, or authority drift."""

    resolved_inputs = inputs.resolved()
    normalized_refs = _require_exact_input_refs(
        resolved_inputs,
        bundle.input_source_refs,
    )
    _require_source_ref(bundle.predecessor_source_ref, "predecessor_source_ref")
    sdk_ref = _require_source_ref(bundle.sdk_source_ref, "sdk_source_ref")
    if normalized_refs["aoa-sdk"] != sdk_ref:
        raise RouterError(
            "candidate SDK source ref differs from the aoa-sdk input source ref"
        )
    _require_exact_git_source_refs(resolved_inputs, normalized_refs)

    expected_files = set(CANDIDATE_ASSEMBLY_FILES) | {
        CANDIDATE_PROVENANCE_REL.as_posix(),
        CANDIDATE_MANIFEST_REL.as_posix(),
    }
    actual_entries = {
        path.relative_to(bundle.output_root).as_posix(): path
        for path in bundle.output_root.rglob("*")
        if path.is_file() or path.is_symlink()
    }
    if set(actual_entries) != expected_files:
        missing = sorted(expected_files - set(actual_entries))
        extra = sorted(set(actual_entries) - expected_files)
        raise RouterError(
            f"G5 candidate file set drifted; missing={missing}, extra={extra}"
        )
    actual_directories = {
        path.relative_to(bundle.output_root).as_posix()
        for path in bundle.output_root.rglob("*")
        if path.is_dir() and not path.is_symlink()
    }
    if actual_directories != set(CANDIDATE_DIRECTORIES):
        missing = sorted(set(CANDIDATE_DIRECTORIES) - actual_directories)
        extra = sorted(actual_directories - set(CANDIDATE_DIRECTORIES))
        raise RouterError(
            f"G5 candidate directory set drifted; missing={missing}, extra={extra}"
        )
    invalid_entries = sorted(
        name
        for name, path in actual_entries.items()
        if path.is_symlink() or not path.is_file()
    )
    if invalid_entries:
        raise RouterError(
            f"G5 candidate entries must be regular files: {invalid_entries}"
        )

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

    provenance = _read_json_object(
        bundle.provenance_path,
        "G5 candidate provenance",
    )
    errors = sorted(
        get_schema_validator(
            "routing-g5-candidate-provenance.schema.json"
        ).iter_errors(provenance),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if errors:
        rendered = "; ".join(error.message for error in errors)
        raise RouterError(f"G5 candidate provenance schema violations: {rendered}")
    _require_observed_at(provenance.get("observed_at"))

    artifact_hashes = {
        filename: _sha256(bundle.generated_root / filename)
        for filename in ARTIFACT_FILENAMES
    }
    if artifact_hashes != dict(bundle.artifact_sha256):
        raise RouterError("G5 candidate artifact hashes drifted")
    if provenance.get("artifact_sha256") != artifact_hashes:
        raise RouterError("G5 candidate provenance artifact hashes drifted")
    assembly_hashes = {
        rel_path: _sha256(bundle.output_root / rel_path)
        for rel_path in CANDIDATE_ASSEMBLY_FILES
    }
    if assembly_hashes != dict(bundle.assembly_file_sha256):
        raise RouterError("G5 candidate assembly file hashes drifted")
    if provenance.get("assembly_file_sha256") != assembly_hashes:
        raise RouterError("G5 candidate provenance assembly hashes drifted")

    router = json.loads(
        (bundle.generated_root / "aoa_router.min.json").read_text(encoding="utf-8")
    )
    identity = router.get("artifact_identity")
    if not isinstance(identity, dict) or identity.get("owner_repo") != SDK_OWNER_REPO:
        raise RouterError("G5 candidate router must carry SDK producer identity")

    manifest = _read_json_object(
        bundle.manifest_path,
        "G5 candidate artifact manifest",
    )
    if manifest.get("schema") != "abyss_machine_artifact_bundle_manifest_v1":
        raise RouterError("G5 candidate artifact manifest schema drifted")
    if manifest.get("artifact_class") != "thin_routing_readmodel_bundle":
        raise RouterError("G5 candidate artifact class drifted")
    if manifest.get("owner_repo") != SDK_OWNER_REPO:
        raise RouterError("G5 candidate artifact manifest owner drifted")
    if manifest != _candidate_manifest(sdk_ref):
        raise RouterError("G5 candidate artifact manifest content drifted")
    artifact_source = manifest.get("artifact_source")
    if (
        not isinstance(artifact_source, dict)
        or artifact_source.get("producer_source_ref") != sdk_ref
    ):
        raise RouterError("G5 candidate artifact manifest source ref drifted")
    subjects = manifest.get("artifact_subjects")
    subject_paths = (
        {item.get("path") for item in subjects if isinstance(item, dict)}
        if isinstance(subjects, list)
        else set()
    )
    expected_subjects = set(CANDIDATE_ASSEMBLY_FILES) | {
        CANDIDATE_PROVENANCE_REL.as_posix()
    }
    if subject_paths != expected_subjects:
        raise RouterError("G5 candidate artifact subject set drifted")
    abi_subject = manifest.get("abi_subject")
    if not isinstance(abi_subject, dict) or abi_subject.get("path") != (
        "generated/aoa_router.min.json"
    ):
        raise RouterError("G5 candidate ABI subject drifted")
    if provenance.get("g5_authority") != {
        "canonical_producer_switch_authorized": False,
        "sdk_canonical": False,
        "live_runtime_mutation_authorized": False,
        "predecessor_maintenance_only": False,
        "compatibility_window_started": False,
        "archive_authorized": False,
    }:
        raise RouterError("G5 candidate authority stop line drifted")
    if provenance.get("authority_stop_line") != AUTHORITY_STOP_LINE:
        raise RouterError("G5 candidate authority stop-line text drifted")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build or validate a non-publishing aoa-sdk routing G5 candidate."
        )
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
    parser.add_argument("--predecessor-source-ref")
    parser.add_argument("--sdk-source-ref")
    parser.add_argument(
        "--source-ref",
        action="append",
        default=[],
        metavar="OWNER=GIT_REF",
    )
    parser.add_argument("--observed-at")
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


def _source_refs_from_args(values: list[str]) -> dict[str, str]:
    refs: dict[str, str] = {}
    for value in values:
        owner, separator, source_ref = value.partition("=")
        if not separator or not owner or not source_ref:
            raise RouterError("--source-ref must use OWNER=GIT_REF")
        if owner in refs:
            raise RouterError(f"duplicate --source-ref owner: {owner}")
        refs[owner] = source_ref
    return refs


def main() -> int:
    args = _parse_args()
    inputs = _inputs_from_args(args)
    if args.check:
        bundle = load_g5_candidate_bundle(args.output_dir)
        validate_g5_candidate_bundle(bundle, inputs)
        print(
            f"[ok] validated non-publishing SDK G5 candidate "
            f"{bundle.sdk_source_ref}"
        )
        return 0
    if not args.predecessor_source_ref or not args.sdk_source_ref:
        raise RouterError(
            "candidate build requires --predecessor-source-ref and --sdk-source-ref"
        )
    timestamp = (
        _require_observed_at(args.observed_at)
        if args.observed_at
        else None
    )
    bundle = build_g5_candidate_bundle(
        inputs,
        args.output_dir,
        predecessor_source_ref=args.predecessor_source_ref,
        sdk_source_ref=args.sdk_source_ref,
        input_source_refs=_source_refs_from_args(args.source_ref),
        observed_at=timestamp,
    )
    print(
        f"[ok] built {len(bundle.artifact_sha256)}/14 SDK G5 candidate "
        f"artifacts under {bundle.output_root}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RouterError as exc:
        print(f"[error] {exc}")
        raise SystemExit(1)
