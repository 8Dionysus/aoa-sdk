from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .models import ManifestDiagnostic, ManifestKind, RecurrenceComponent


SCHEMA_VERSION_TO_KIND: dict[str, ManifestKind] = {
    "aoa_recurrence_component_v1": "recurrence_component",
    "aoa_recurrence_component_v2": "recurrence_component",
    "aoa_recurrence_component_v3": "recurrence_component",
    "aoa_hook_binding_set_v1": "hook_binding_set",
    "recurrence_hook_binding_set_v1": "hook_binding_set",
    "aoa_review_queue_v1": "review_surface",
    "aoa_candidate_dossier_packet_v1": "review_surface",
    "aoa_owner_review_summary_v1": "review_surface",
    "aoa_wiring_plan_v1": "wiring_plan",
    "aoa_rollout_window_bundle_v1": "rollout_bundle",
}

KNOWN_MANIFEST_KINDS = {
    "recurrence_component",
    "hook_binding_set",
    "agon_recurrence_adapter",
    "review_surface",
    "rollout_bundle",
    "wiring_plan",
    "unknown",
}

AGON_SHAPE_KEYS = {
    "authority",
    "component_id",
    "forbidden_actions",
    "observation_only",
    "observed_surfaces",
    "recurrence_watch",
    "stop_lines",
    "surface_refs",
    "surfaces",
    "wave",
}


@dataclass(slots=True)
class ManifestClassification:
    repo: str
    repo_root: Path
    path: Path
    payload: dict[str, Any] | None
    manifest_kind: ManifestKind
    diagnostics: list[ManifestDiagnostic]

    @property
    def manifest_ref(self) -> str:
        return manifest_ref(self.repo, self.repo_root, self.path)


class ManifestLoadError(Exception):
    """Raised inside compatibility helpers before conversion to diagnostics."""


def manifest_ref(repo: str, repo_root: Path, path: Path) -> str:
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        relative = path
    relative_str = str(relative).replace("\\", "/")
    return f"manifest:{repo}:{relative_str}"


def manifest_path_string(repo_root: Path, path: Path) -> str:
    try:
        relative = path.relative_to(repo_root)
    except ValueError:
        relative = path
    return str(relative).replace("\\", "/")


def _diagnostic(
    *,
    repo: str,
    repo_root: Path,
    path: Path,
    manifest_kind: ManifestKind,
    diagnostic_kind: str,
    severity: str,
    message: str,
    evidence: dict[str, Any] | None = None,
) -> ManifestDiagnostic:
    return ManifestDiagnostic(
        manifest_ref=manifest_ref(repo, repo_root, path),
        repo=repo,
        path=manifest_path_string(repo_root, path),
        manifest_kind=manifest_kind,
        diagnostic_kind=diagnostic_kind,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        message=message,
        evidence=evidence or {},
    )


def load_json_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ManifestLoadError("manifest payload must be a JSON object")
    return payload


def detect_manifest_kind(payload: dict[str, Any]) -> ManifestKind:
    explicit = payload.get("manifest_kind")
    if isinstance(explicit, str):
        if explicit in KNOWN_MANIFEST_KINDS:
            return explicit  # type: ignore[return-value]
        return "unknown"

    schema_version = payload.get("schema_version")
    if isinstance(schema_version, str) and schema_version in SCHEMA_VERSION_TO_KIND:
        return SCHEMA_VERSION_TO_KIND[schema_version]

    if any(key in payload for key in ("bindings", "hooks", "hook_binding_set_id", "hook_set_id")):
        return "hook_binding_set"

    if "component_ref" in payload and "owner_repo" in payload:
        return "recurrence_component"

    if AGON_SHAPE_KEYS.intersection(payload):
        return "agon_recurrence_adapter"

    return "unknown"


def prepare_recurrence_component_payload(payload: dict[str, Any]) -> dict[str, Any]:
    prepared = dict(payload)
    prepared.setdefault("manifest_kind", "recurrence_component")
    prepared.setdefault("schema_version", "aoa_recurrence_component_v2")
    return prepared


def looks_like_agon_adapter_payload(payload: dict[str, Any]) -> bool:
    schema_version = payload.get("schema_version")
    if schema_version == "recurrence_component_manifest_v1":
        return True

    text_fields = (
        payload.get("component_ref"),
        payload.get("component_id"),
        payload.get("status"),
        payload.get("wave"),
    )
    if any(isinstance(value, str) and "agon" in value.lower() for value in text_fields):
        return True

    tags = payload.get("tags")
    if isinstance(tags, list) and any(
        isinstance(tag, str) and tag.lower() == "agon" for tag in tags
    ):
        return True

    return bool(AGON_SHAPE_KEYS.intersection(payload))


def classify_manifest(repo: str, repo_root: Path, path: Path) -> ManifestClassification:
    diagnostics: list[ManifestDiagnostic] = []
    try:
        payload = load_json_payload(path)
    except json.JSONDecodeError as exc:
        diagnostics.append(
            _diagnostic(
                repo=repo,
                repo_root=repo_root,
                path=path,
                manifest_kind="unknown",
                diagnostic_kind="manifest_json_error",
                severity="high",
                message="manifest JSON could not be parsed; registry scan quarantined it instead of aborting",
                evidence={"error": str(exc)},
            )
        )
        return ManifestClassification(repo, repo_root, path, None, "unknown", diagnostics)
    except ManifestLoadError as exc:
        diagnostics.append(
            _diagnostic(
                repo=repo,
                repo_root=repo_root,
                path=path,
                manifest_kind="unknown",
                diagnostic_kind="invalid_manifest_shape",
                severity="high",
                message=str(exc),
            )
        )
        return ManifestClassification(repo, repo_root, path, None, "unknown", diagnostics)

    manifest_kind = detect_manifest_kind(payload)
    explicit_kind = payload.get("manifest_kind")
    if isinstance(explicit_kind, str) and explicit_kind not in KNOWN_MANIFEST_KINDS:
        diagnostics.append(
            _diagnostic(
                repo=repo,
                repo_root=repo_root,
                path=path,
                manifest_kind="unknown",
                diagnostic_kind="unknown_manifest_kind",
                severity="medium",
                message="manifest_kind is not recognised; scanner quarantined this file from the component registry",
                evidence={"manifest_kind": explicit_kind},
            )
        )
        return ManifestClassification(repo, repo_root, path, payload, "unknown", diagnostics)

    if manifest_kind == "unknown":
        diagnostics.append(
            _diagnostic(
                repo=repo,
                repo_root=repo_root,
                path=path,
                manifest_kind="unknown",
                diagnostic_kind="unknown_manifest_kind",
                severity="medium",
                message="manifest shape did not match a known recurrence-adjacent contract",
                evidence={"keys": sorted(payload.keys())[:24]},
            )
        )
    elif manifest_kind == "agon_recurrence_adapter":
        diagnostics.append(
            _diagnostic(
                repo=repo,
                repo_root=repo_root,
                path=path,
                manifest_kind=manifest_kind,
                diagnostic_kind="adapter_required",
                severity="medium",
                message="Agon-shaped recurrence manifest detected; keep it observation-only until an Agon adapter owns the translation",
                evidence={"keys": sorted(payload.keys())[:24]},
            )
        )
    elif manifest_kind != "recurrence_component":
        diagnostics.append(
            _diagnostic(
                repo=repo,
                repo_root=repo_root,
                path=path,
                manifest_kind=manifest_kind,
                diagnostic_kind="known_foreign_manifest",
                severity="low",
                message="known recurrence-adjacent manifest detected; component registry will not load it as a component",
                evidence={"schema_version": payload.get("schema_version")},
            )
        )

    return ManifestClassification(repo, repo_root, path, payload, manifest_kind, diagnostics)


def validate_recurrence_component_payload(
    *,
    repo: str,
    repo_root: Path,
    path: Path,
    payload: dict[str, Any],
) -> tuple[RecurrenceComponent | None, list[ManifestDiagnostic]]:
    diagnostics: list[ManifestDiagnostic] = []
    try:
        component = RecurrenceComponent.model_validate(
            prepare_recurrence_component_payload(payload)
        )
    except ValidationError as exc:
        if looks_like_agon_adapter_payload(payload):
            diagnostics.append(
                _diagnostic(
                    repo=repo,
                    repo_root=repo_root,
                    path=path,
                    manifest_kind="agon_recurrence_adapter",
                    diagnostic_kind="adapter_required",
                    severity="medium",
                    message="Agon-shaped recurrence manifest needs an adapter before it can enter the component registry",
                    evidence={"errors": exc.errors(), "keys": sorted(payload.keys())[:24]},
                )
            )
            return None, diagnostics

        diagnostics.append(
            _diagnostic(
                repo=repo,
                repo_root=repo_root,
                path=path,
                manifest_kind="recurrence_component",
                diagnostic_kind="invalid_manifest_shape",
                severity="high",
                message="recurrence component manifest failed schema validation and was quarantined",
                evidence={"errors": exc.errors()},
            )
        )
        return None, diagnostics

    if component.owner_repo != repo:
        diagnostics.append(
            _diagnostic(
                repo=repo,
                repo_root=repo_root,
                path=path,
                manifest_kind="recurrence_component",
                diagnostic_kind="owner_repo_mismatch",
                severity="low",
                message="manifest owner_repo did not match workspace repo name; registry rewrote the loaded component owner to the discovered repo",
                evidence={
                    "manifest_owner_repo": component.owner_repo,
                    "discovered_repo": repo,
                    "component_ref": component.component_ref,
                },
            )
        )
        component = component.model_copy(update={"owner_repo": repo})

    diagnostics.append(
        _diagnostic(
            repo=repo,
            repo_root=repo_root,
            path=path,
            manifest_kind="recurrence_component",
            diagnostic_kind="loaded_manifest",
            severity="low",
            message="recurrence component manifest loaded into registry",
            evidence={"component_ref": component.component_ref},
        )
    )
    return component, diagnostics
