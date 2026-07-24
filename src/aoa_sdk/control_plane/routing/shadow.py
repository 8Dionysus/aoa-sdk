"""Non-publishing routing shadow bundle construction and validation."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from .core import REPO_ROOT, RouterError
from .producer import (
    build_outputs,
    ensure_non_publishing_output_dir,
    render_output_text,
)
from .validator import (
    OUTPUT_SCHEMA_NAMES,
    get_schema_validator,
    validate_generated_outputs,
)


SHADOW_PROVENANCE_FILENAME = "routing-shadow-provenance.json"
GIT_OBJECT_ID_PATTERN = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
RFC3339_TIMESTAMP_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})"
)


@dataclass(frozen=True)
class RoutingProducerInputs:
    techniques_root: Path
    skills_root: Path
    evals_root: Path
    memo_root: Path
    stats_root: Path
    agents_root: Path
    aoa_root: Path
    playbooks_root: Path
    kag_root: Path
    tos_root: Path
    sdk_root: Path
    source_route_root: Path
    profile_root: Path
    abyss_stack_root: Path

    def resolved(self) -> "RoutingProducerInputs":
        return RoutingProducerInputs(
            **{
                field_name: getattr(self, field_name).resolve()
                for field_name in self.__dataclass_fields__
            }
        )

    def source_roots(self) -> dict[str, Path]:
        return {
            "aoa-techniques": self.techniques_root,
            "aoa-skills": self.skills_root,
            "aoa-evals": self.evals_root,
            "aoa-memo": self.memo_root,
            "aoa-stats": self.stats_root,
            "aoa-agents": self.agents_root,
            "Agents-of-Abyss": self.aoa_root,
            "aoa-playbooks": self.playbooks_root,
            "aoa-kag": self.kag_root,
            "Tree-of-Sophia": self.tos_root,
            "aoa-sdk": self.sdk_root,
            "Dionysus": self.source_route_root,
            "8Dionysus": self.profile_root,
            "abyss-stack": self.abyss_stack_root,
        }


@dataclass(frozen=True)
class ShadowRoutingBundle:
    output_dir: Path
    provenance_path: Path
    artifact_sha256: Mapping[str, str]
    input_source_refs: Mapping[str, str]
    predecessor_source_ref: str
    sdk_source_ref: str


def _require_source_ref(value: str, location: str) -> str:
    if value != value.strip() or value != value.lower():
        raise RouterError(f"{location} must be a full lowercase Git object ID")
    if not GIT_OBJECT_ID_PATTERN.fullmatch(value):
        raise RouterError(f"{location} must be a full lowercase Git object ID")
    return value


def _require_observed_at(value: object) -> None:
    if not isinstance(value, str) or not RFC3339_TIMESTAMP_PATTERN.fullmatch(value):
        raise RouterError("shadow provenance observed_at must be an RFC 3339 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RouterError(
            "shadow provenance observed_at must be an RFC 3339 timestamp"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RouterError("shadow provenance observed_at must include an offset")


def build_shadow_bundle(
    inputs: RoutingProducerInputs,
    output_dir: Path,
    *,
    predecessor_source_ref: str,
    sdk_source_ref: str,
    input_source_refs: Mapping[str, str],
    observed_at: datetime | None = None,
) -> ShadowRoutingBundle:
    """Build fourteen compatibility artifacts plus dual-producer provenance."""

    predecessor_ref = _require_source_ref(
        predecessor_source_ref,
        "predecessor_source_ref",
    )
    sdk_ref = _require_source_ref(sdk_source_ref, "sdk_source_ref")
    resolved_inputs = inputs.resolved()
    expected_input_names = set(resolved_inputs.source_roots())
    if set(input_source_refs) != expected_input_names:
        missing = sorted(expected_input_names - set(input_source_refs))
        extra = sorted(set(input_source_refs) - expected_input_names)
        raise RouterError(
            f"input_source_refs must match producer inputs; missing={missing}, extra={extra}"
        )
    normalized_input_refs = {
        name: _require_source_ref(ref, f"input_source_refs[{name!r}]")
        for name, ref in sorted(input_source_refs.items())
    }

    target = ensure_non_publishing_output_dir(output_dir)
    if target.exists() and not target.is_dir():
        raise RouterError("shadow output path must be a directory")
    if target.exists() and any(target.iterdir()):
        raise RouterError("shadow output directory must be absent or empty")
    target.mkdir(parents=True, exist_ok=True)
    outputs = build_outputs(
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
    )
    artifact_sha256: dict[str, str] = {}
    for filename, payload in outputs.items():
        rendered = render_output_text(filename, payload)
        (target / filename).write_text(rendered, encoding="utf-8", newline="\n")
        artifact_sha256[filename] = hashlib.sha256(rendered.encode("utf-8")).hexdigest()

    timestamp = observed_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise RouterError("observed_at must be timezone-aware")
    provenance = {
        "schema_version": "aoa_sdk_routing_shadow_provenance_v1",
        "state": "sdk_shadow",
        "publication_posture": "non_publishing",
        "canonical_producer": {
            "owner_repo": "aoa-routing",
            "source_ref": predecessor_ref,
        },
        "shadow_producer": {
            "owner_repo": "aoa-sdk",
            "source_ref": sdk_ref,
            "implementation": "aoa_sdk.control_plane.routing",
        },
        "abi_epoch": "aoa_routing_thin_router_v1",
        "artifact_sha256": dict(sorted(artifact_sha256.items())),
        "input_source_refs": normalized_input_refs,
        "observed_at": timestamp.isoformat().replace("+00:00", "Z"),
        "authority_stop_line": (
            "This sidecar proves shadow construction only. aoa-routing remains canonical; "
            "no runtime consumer, trust record, or G5 authority is changed."
        ),
    }
    provenance_path = target / SHADOW_PROVENANCE_FILENAME
    provenance_path.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return ShadowRoutingBundle(
        output_dir=target,
        provenance_path=provenance_path,
        artifact_sha256=artifact_sha256,
        input_source_refs=normalized_input_refs,
        predecessor_source_ref=predecessor_ref,
        sdk_source_ref=sdk_ref,
    )


def validate_shadow_bundle(
    bundle: ShadowRoutingBundle,
    inputs: RoutingProducerInputs,
) -> None:
    """Fail closed on schema, semantic, rebuild, hash, or provenance drift."""

    resolved_inputs = inputs.resolved()
    issues = validate_generated_outputs(
        bundle.output_dir,
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
    )
    if issues:
        rendered = "; ".join(f"{issue.location}: {issue.message}" for issue in issues)
        raise RouterError(rendered)

    expected_provenance_path = bundle.output_dir / SHADOW_PROVENANCE_FILENAME
    if bundle.provenance_path != expected_provenance_path:
        raise RouterError("shadow provenance path must stay inside the bundle")
    expected_bundle_names = set(OUTPUT_SCHEMA_NAMES) | {SHADOW_PROVENANCE_FILENAME}
    actual_bundle_entries = {path.name: path for path in bundle.output_dir.iterdir()}
    if set(actual_bundle_entries) != expected_bundle_names:
        missing = sorted(expected_bundle_names - set(actual_bundle_entries))
        extra = sorted(set(actual_bundle_entries) - expected_bundle_names)
        raise RouterError(
            f"shadow bundle file set drifted; missing={missing}, extra={extra}"
        )
    invalid_entries = sorted(
        name
        for name, path in actual_bundle_entries.items()
        if path.is_symlink() or not path.is_file()
    )
    if invalid_entries:
        raise RouterError(
            f"shadow bundle entries must be regular files: {invalid_entries}"
        )
    provenance = json.loads(bundle.provenance_path.read_text(encoding="utf-8"))
    provenance_errors = sorted(
        get_schema_validator("routing-shadow-provenance.schema.json").iter_errors(
            provenance
        ),
        key=lambda error: (list(error.absolute_path), error.message),
    )
    if provenance_errors:
        rendered_errors = "; ".join(error.message for error in provenance_errors)
        raise RouterError(f"shadow provenance schema violations: {rendered_errors}")
    _require_observed_at(provenance.get("observed_at"))
    if provenance.get("state") != "sdk_shadow":
        raise RouterError("shadow provenance state must stay sdk_shadow")
    if provenance.get("publication_posture") != "non_publishing":
        raise RouterError("shadow provenance must stay non_publishing")
    if provenance.get("canonical_producer") != {
        "owner_repo": "aoa-routing",
        "source_ref": bundle.predecessor_source_ref,
    }:
        raise RouterError("shadow provenance canonical producer drifted")
    if provenance.get("shadow_producer") != {
        "owner_repo": "aoa-sdk",
        "source_ref": bundle.sdk_source_ref,
        "implementation": "aoa_sdk.control_plane.routing",
    }:
        raise RouterError("shadow provenance SDK producer drifted")
    if provenance.get("input_source_refs") != dict(bundle.input_source_refs):
        raise RouterError("shadow provenance input source refs drifted")
    if set(bundle.artifact_sha256) != set(OUTPUT_SCHEMA_NAMES):
        raise RouterError("shadow bundle must contain exactly fourteen routing artifacts")

    actual_hashes: dict[str, str] = {}
    for filename in sorted(bundle.artifact_sha256):
        artifact_path = bundle.output_dir / filename
        actual_hashes[filename] = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    if actual_hashes != dict(bundle.artifact_sha256):
        raise RouterError("shadow routing artifact hashes changed after construction")
    if provenance.get("artifact_sha256") != actual_hashes:
        raise RouterError("shadow provenance artifact hashes do not match the bundle")
