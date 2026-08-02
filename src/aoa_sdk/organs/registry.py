"""Deterministic, secret-free projection of an explicit private organ registry."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..contracts.organs import (
    NON_DISCOVERABLE_STATES,
    MaturityEvidence,
    OrganProjectionEntry,
    OrganRecord,
    OrganRegistryProjection,
    OrganRegistrySource,
    QualifiedEvidenceRef,
)
from ..errors import AoASDKError


class OrganRegistryError(AoASDKError, ValueError):
    """The explicit organ registry is absent, invalid, stale, or inconsistent."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_digest(value: Any) -> str:
    return f"sha256:{hashlib.sha256(canonical_json_bytes(value)).hexdigest()}"


def load_registry_source(path: str | Path) -> OrganRegistrySource:
    resolved = Path(path).expanduser().resolve(strict=False)
    if not resolved.is_file():
        raise OrganRegistryError(
            f"explicit organ registry source does not exist: {resolved}"
        )
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
        reject_secret_material(payload)
        source = OrganRegistrySource.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise OrganRegistryError(f"invalid organ registry source {resolved}: {exc}") from exc
    return source


def compile_registry(
    source: OrganRegistrySource,
    *,
    compiled_at: datetime | None = None,
) -> OrganRegistryProjection:
    """Compile a deterministic projection without discovering or activating anything."""

    timestamp = compiled_at or source.authored_at
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise OrganRegistryError("compiled_at must be timezone-aware")
    timestamp = timestamp.astimezone(timezone.utc)
    if timestamp > source.expires_at:
        raise OrganRegistryError("registry source is expired at compile time")

    source_payload = source.model_dump(mode="json")
    reject_secret_material(source_payload)
    source_digest = sha256_digest(source_payload)
    entries = tuple(
        _project_record(
            record,
            registry_id=source.registry_id,
            source_digest=source_digest,
            compiled_at=timestamp,
            expires_at=source.expires_at,
        )
        for record in sorted(source.records, key=lambda item: item.organ_id)
    )
    unsigned = {
        "schema_version": "aoa_organ_registry_projection_v1",
        "registry_id": source.registry_id,
        "workspace_owner": source.workspace_owner,
        "source_digest": source_digest,
        "compiled_at": timestamp.isoformat().replace("+00:00", "Z"),
        "expires_at": source.expires_at.isoformat().replace("+00:00", "Z"),
        "default_admission": "deny",
        "contains_secrets": False,
        "entries": [entry.model_dump(mode="json") for entry in entries],
    }
    projection_digest = sha256_digest(unsigned)
    return OrganRegistryProjection.model_validate(
        {
            **unsigned,
            "projection_digest": projection_digest,
        }
    )


def assert_projection_digest(projection: OrganRegistryProjection) -> None:
    payload = projection.model_dump(mode="json")
    claimed = payload.pop("projection_digest")
    actual = sha256_digest(payload)
    if actual != claimed:
        raise OrganRegistryError(
            f"organ registry projection digest mismatch: expected {claimed}, got {actual}"
        )


def _project_record(
    record: OrganRecord,
    *,
    registry_id: str,
    source_digest: str,
    compiled_at: datetime,
    expires_at: datetime,
) -> OrganProjectionEntry:
    credentials = tuple(
        sorted(
            value
            for value in record.credential_contours.model_dump().values()
            if value is not None
        )
    )
    indexed_evidence = QualifiedEvidenceRef(
        owner="aoa-sdk",
        evidence_ref=(
            f"registry://{registry_id}/{source_digest}/{record.organ_id}"
        ),
        revision=source_digest,
        observed_at=compiled_at,
        expires_at=expires_at,
    )
    maturity = record.maturity.model_copy(
        update={
            "registry_indexed": MaturityEvidence(
                state="asserted",
                evidence=indexed_evidence,
                freshness_policy="registry-projection-expiry-v1",
            )
        }
    )
    return OrganProjectionEntry(
        organ_id=record.organ_id,
        display_name=record.display_name,
        description=record.description,
        registry_state=record.registry_state,
        discoverable=record.registry_state not in NON_DISCOVERABLE_STATES,
        owners=record.owners,
        authority_ceiling=record.authority_ceiling,
        authentication_requirements=record.authentication_requirements,
        credential_classes=credentials,
        revisions=record.revisions,
        freshness_policy=record.freshness_policy,
        freshness_state=record.freshness_state,
        freshness_evidence=record.freshness_evidence,
        eval_refs=record.eval_refs,
        eval_status=record.eval_status,
        eval_evidence=record.eval_evidence,
        capabilities=tuple(
            sorted(record.capabilities, key=lambda item: item.capability_id)
        ),
        endpoint=record.endpoint,
        consumer_compatibility=tuple(
            sorted(
                record.consumer_compatibility,
                key=lambda item: item.consumer_id,
            )
        ),
        maturity=maturity,
        activation_preconditions=record.activation_preconditions,
        rollback_route=record.rollback_route,
        support_route=record.support_route,
        handoff=record.handoff,
    )


_FORBIDDEN_SECRET_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "bearer",
        "client_secret",
        "credential_material",
        "password",
        "private_key",
        "refresh_token",
        "secret",
        "token",
    }
)


def reject_secret_material(
    value: Any,
    path: str = "$",
    *,
    context: str = "organ registry",
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _FORBIDDEN_SECRET_KEYS:
                raise OrganRegistryError(
                    f"secret-bearing key is forbidden in {context} at {path}.{key}"
                )
            reject_secret_material(child, f"{path}.{key}", context=context)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secret_material(child, f"{path}[{index}]", context=context)
    elif isinstance(value, str):
        lowered = value.lower()
        if lowered.startswith(("bearer ", "sk-", "ghp_", "github_pat_")):
                raise OrganRegistryError(
                    f"secret-like value is forbidden in {context} at {path}"
                )
