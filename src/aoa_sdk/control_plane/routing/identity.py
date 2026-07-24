"""Explicit routing-producer identity postures for the owner-only switch."""

from __future__ import annotations

import copy
from typing import Any, Literal, Mapping

from .core import RouterError


RoutingProducerPosture = Literal["predecessor_compatible", "sdk_g5_candidate"]

PREDECESSOR_COMPATIBLE: RoutingProducerPosture = "predecessor_compatible"
SDK_G5_CANDIDATE: RoutingProducerPosture = "sdk_g5_candidate"

PREDECESSOR_OWNER_REPO = "aoa-routing"
SDK_OWNER_REPO = "aoa-sdk"

_OWNER_ROUTE_KEYS = frozenset(
    {
        "owner_repo",
        "source_repo",
        "surface_repo",
        "target_repo",
    }
)

SDK_ROUTING_READMODEL_ARTIFACT_IDENTITY: dict[str, Any] = {
    "artifact_class": "thin_routing_readmodel_bundle",
    "surface_state": "public_generated_routing_surfaces",
    "owner_repo": SDK_OWNER_REPO,
    "authority_ref": "docs/boundaries.md#owner-only-routing-succession",
    "producer": (
        "aoa_sdk.control_plane.routing from owner-qualified sibling projections "
        "under an explicit producer posture"
    ),
    "consumer_expectation": (
        "Consumers verify artifact_identity, router_version, schema conformance, "
        "the SDK candidate validator, exact source refs, durable artifact trust, "
        "and source-owned next-hop refs before using routing surfaces for dispatch."
    ),
    "privacy_boundary": (
        "public route refs and compact summaries only; no private source payloads, "
        "secrets, live runtime state, or owner-corpus copies"
    ),
    "content_identity": (
        "generated routing family rooted at generated/aoa_router.min.json and "
        "rebuilt by aoa_sdk.control_plane.routing"
    ),
    "abi_epoch": "aoa_routing_thin_router_v1",
    "contract_version": (
        "routing/core/schemas/aoa-router.schema.json@"
        "aoa_routing_thin_router_v1#artifact_identity"
    ),
    "trust_layer": [
        "abi_contract_signature",
        "sbom",
        "slsa_in_toto",
    ],
    "verification": [
        (
            "python -m aoa_sdk.control_plane.routing.candidate "
            "--check --output-dir CANDIDATE_ROOT"
        ),
        (
            "python mechanics/boundary-bridge/parts/"
            "consumed-surface-posture-gate/scripts/"
            "verify_routing_g5_candidate_wheel.py"
        ),
        "python scripts/release_check.py",
    ],
}

SDK_FEDERATION_ENTRY_ARTIFACT_IDENTITY: dict[str, Any] = {
    "artifact_class": "generated_readmodel",
    "surface_state": "public_generated_navigation_surface",
    "owner_repo": SDK_OWNER_REPO,
    "authority_ref": (
        "mechanics/boundary-bridge/parts/consumed-surface-posture-gate/"
        "docs/routing-succession-g5-candidate.md"
    ),
    "producer": (
        "aoa_sdk.control_plane.routing from sibling owner-generated source inputs"
    ),
    "consumer_expectation": (
        "consumers verify schema_version, schema_ref, source inputs, exact SDK "
        "producer provenance, and the candidate validator before treating entry "
        "cards as usable orientation"
    ),
    "privacy_boundary": (
        "public route references only; no copied owner payloads, private state, "
        "source corpora, or runtime secrets"
    ),
    "content_identity": (
        "generated/federation_entrypoints.min.json rebuilt from declared "
        "source_inputs by aoa_sdk.control_plane.routing"
    ),
    "abi_epoch": "aoa_routing_federation_entrypoints_v2",
    "contract_version": (
        "federation-entrypoints.schema.json@"
        "aoa_routing_federation_entrypoints_v2#artifact_identity"
    ),
    "trust_layer": ["abi_contract_signature"],
    "verification": [
        (
            "python -m aoa_sdk.control_plane.routing.candidate "
            "--check --output-dir CANDIDATE_ROOT"
        ),
        "python scripts/release_check.py",
    ],
    "action": "ADD_CONSUMER_EXPECTATION",
}


def _rewrite_owner_routes(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: (
                SDK_OWNER_REPO
                if key in _OWNER_ROUTE_KEYS and nested == PREDECESSOR_OWNER_REPO
                else _rewrite_owner_routes(nested)
            )
            for key, nested in value.items()
        }
    if isinstance(value, list):
        return [_rewrite_owner_routes(item) for item in value]
    return value


def apply_routing_producer_posture(
    outputs: Mapping[str, Any],
    posture: RoutingProducerPosture,
) -> dict[str, Any]:
    """Return outputs with only the named producer-authority posture changed.

    The predecessor-compatible posture is byte preserving.  The candidate
    posture changes producer/return-route metadata while keeping filenames,
    schema epochs, route content, and source-owner semantics stable.
    """

    normalized = copy.deepcopy(dict(outputs))
    if posture == PREDECESSOR_COMPATIBLE:
        return normalized
    if posture != SDK_G5_CANDIDATE:
        raise RouterError(f"unsupported routing producer posture: {posture}")

    normalized = _rewrite_owner_routes(normalized)
    try:
        normalized["aoa_router.min.json"]["artifact_identity"] = copy.deepcopy(
            SDK_ROUTING_READMODEL_ARTIFACT_IDENTITY
        )
        normalized["federation_entrypoints.min.json"][
            "artifact_identity"
        ] = copy.deepcopy(SDK_FEDERATION_ENTRY_ARTIFACT_IDENTITY)
    except (KeyError, TypeError) as exc:
        raise RouterError(
            "routing output family is missing the producer identity surfaces"
        ) from exc
    return normalized

