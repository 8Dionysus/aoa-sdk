"""Progressive discovery and fail-closed activation-plan compilation."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from ..contracts.organs import (
    ACTIVATABLE_STATES,
    POLICY_RANK,
    ActivationRequest,
    CatalogCapability,
    CatalogEntry,
    CatalogResult,
    CapabilityContract,
    CompatibilityObservation,
    EffectClass,
    FreshnessState,
    OrganActivationPlan,
    OrganProjectionEntry,
    OrganRegistryProjection,
    PolicyFamily,
    RegistryState,
)
from ..contracts.organ_orchestration import (
    CrossOrganOrchestrationRequest,
    CrossOrganOrchestrationRun,
    CrossOrganStageObservation,
)
from ..workspace.discovery import Workspace
from .orchestration import (
    advance_orchestration,
    start_orchestration,
    validate_orchestration_run,
)
from .registry import (
    OrganRegistryError,
    assert_projection_digest,
    canonical_json_bytes,
    compile_registry,
    load_registry_source,
    sha256_digest,
)


class OrgansAPI:
    """SDK-owned organ access surface backed only by explicit configuration."""

    def __init__(
        self,
        workspace: Workspace,
        *,
        registry_path: str | Path | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.workspace = workspace
        self.registry_path = (
            Path(registry_path).expanduser().resolve(strict=False)
            if registry_path is not None
            else workspace.organ_registry_path
        )
        self._projection: OrganRegistryProjection | None = None
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def projection(self) -> OrganRegistryProjection:
        if self.registry_path is None:
            raise OrganRegistryError(
                "no explicit organ registry configured; set "
                "AOA_SDK_ORGAN_REGISTRY or [organ_access].registry_source"
            )
        current = compile_registry(load_registry_source(self.registry_path))
        if (
            self._projection is None
            or self._projection.source_digest != current.source_digest
        ):
            self._projection = current
        assert_projection_digest(self._projection)
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise OrganRegistryError("organ registry clock must be timezone-aware")
        if self._projection.expires_at <= now:
            raise OrganRegistryError("organ registry projection is expired")
        return self._projection

    def catalog(
        self,
        *,
        query: str | None = None,
        source_owner: str | None = None,
        maximum_policy: PolicyFamily = "read",
        freshness_states: tuple[FreshnessState, ...] | None = None,
        effect_classes: tuple[EffectClass, ...] | None = None,
        allowed_organ_ids: tuple[str, ...] | None = None,
        allowed_capability_ids: tuple[str, ...] | None = None,
        max_results: int = 24,
        byte_budget: int = 32_768,
    ) -> CatalogResult:
        if max_results < 1 or byte_budget < 256:
            raise OrganRegistryError("catalog bounds must be positive and explicit")
        projection = self.projection()
        hidden: dict[RegistryState, int] = {}
        candidates: list[CatalogEntry] = []
        query_tokens = {
            token
            for token in (query or "").lower().replace("_", " ").split()
            if token
        }
        for entry in projection.entries:
            if not entry.discoverable:
                hidden[entry.registry_state] = hidden.get(entry.registry_state, 0) + 1
                continue
            if source_owner is not None and entry.owners.source_owner != source_owner:
                continue
            if allowed_organ_ids is not None and entry.organ_id not in allowed_organ_ids:
                continue
            if (
                freshness_states is not None
                and entry.freshness_state not in freshness_states
            ):
                continue
            capabilities = tuple(
                _catalog_capability(entry.organ_id, capability)
                for capability in entry.capabilities
                if POLICY_RANK[capability.policy_family] <= POLICY_RANK[maximum_policy]
                and (
                    allowed_capability_ids is None
                    or capability.capability_id in allowed_capability_ids
                )
                and (
                    effect_classes is None
                    or any(
                        primitive.effect_class in effect_classes
                        for primitive in capability.primitives
                    )
                )
            )
            if not capabilities:
                continue
            if query_tokens and not _matches(entry, capabilities, query_tokens):
                continue
            candidates.append(
                CatalogEntry(
                    organ_id=entry.organ_id,
                    display_name=entry.display_name,
                    registry_state=entry.registry_state,
                    authority_ceiling=entry.authority_ceiling,
                    source_owner=entry.owners.source_owner,
                    access_owner=entry.owners.access_owner,
                    freshness_state=entry.freshness_state,
                    eval_status=entry.eval_status,
                    capabilities=capabilities,
                )
            )

        selected: list[CatalogEntry] = []
        truncated = False
        for candidate in candidates:
            if len(selected) >= max_results:
                truncated = True
                break
            trial = tuple((*selected, candidate))
            size = len(canonical_json_bytes([item.model_dump(mode="json") for item in trial]))
            if size > byte_budget:
                truncated = True
                break
            selected.append(candidate)
        result_bytes = len(
            canonical_json_bytes([item.model_dump(mode="json") for item in selected])
        )
        return CatalogResult(
            registry_digest=projection.projection_digest,
            entries=tuple(selected),
            result_bytes=result_bytes,
            truncated=truncated,
            hidden_state_counts=hidden,
        )

    def inspect_organ(self, organ_id: str) -> OrganProjectionEntry:
        entry = self._find_organ(organ_id, self.projection())
        if not entry.discoverable:
            raise OrganRegistryError(f"organ {organ_id!r} is not discoverable")
        return entry

    def inspect_capability(
        self,
        organ_id: str,
        capability_id: str,
    ) -> CapabilityContract:
        entry = self._find_organ(organ_id, self.projection())
        if not entry.discoverable:
            raise OrganRegistryError(f"organ {organ_id!r} is not discoverable")
        return self._find_capability(entry, capability_id)

    def start_orchestration(
        self,
        request: CrossOrganOrchestrationRequest,
    ) -> CrossOrganOrchestrationRun:
        """Start a host-visible run without calling any owner tool."""

        return start_orchestration(request)

    def advance_orchestration(
        self,
        run: CrossOrganOrchestrationRun,
        observation: CrossOrganStageObservation,
    ) -> CrossOrganOrchestrationRun:
        """Append one explicitly supplied owner observation and receipt."""

        return advance_orchestration(run, observation)

    def validate_orchestration(
        self,
        run: CrossOrganOrchestrationRun,
    ) -> CrossOrganOrchestrationRun:
        """Rebuild and validate a complete or partial orchestration chain."""

        return validate_orchestration_run(run)

    @staticmethod
    def _find_capability(
        entry: OrganProjectionEntry,
        capability_id: str,
    ) -> CapabilityContract:
        for capability in entry.capabilities:
            if capability.capability_id == capability_id:
                return capability
        raise OrganRegistryError(
            f"unknown capability {capability_id!r} for organ {entry.organ_id!r}"
        )

    def compare_observation(
        self,
        *,
        organ_id: str,
        observed_deploy_revision: str | None,
        observed_server_schema_digest: str | None,
        observed_consumer_schema_digest: str | None,
        observed_at: datetime,
    ) -> CompatibilityObservation:
        projection = self.projection()
        entry = self._find_organ(organ_id, projection)
        reasons: list[str] = []
        state: FreshnessState = "exact"
        expected_deploy = (
            entry.revisions.deploy.revision
            if entry.revisions.deploy is not None
            else None
        )
        expected_server = (
            entry.endpoint.server_schema_digest
            if entry.endpoint is not None
            else None
        )
        expected_consumer = (
            entry.revisions.consumer_schema.schema_digest
            if entry.revisions.consumer_schema is not None
            else None
        )
        if expected_deploy != observed_deploy_revision:
            state = "blocked"
            reasons.append("deploy_revision_mismatch")
        if expected_server != observed_server_schema_digest:
            state = "blocked"
            reasons.append("server_schema_digest_mismatch")
        if expected_consumer != observed_consumer_schema_digest:
            state = "blocked"
            reasons.append("consumer_schema_digest_mismatch")
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise OrganRegistryError("observed_at must be timezone-aware")
        return CompatibilityObservation(
            organ_id=organ_id,
            registry_digest=projection.projection_digest,
            expected_deploy_revision=expected_deploy,
            observed_deploy_revision=observed_deploy_revision,
            expected_server_schema_digest=expected_server,
            observed_server_schema_digest=observed_server_schema_digest,
            expected_consumer_schema_digest=expected_consumer,
            observed_consumer_schema_digest=observed_consumer_schema_digest,
            state=state,
            reason_codes=tuple(reasons),
            observed_at=observed_at,
            evidence_refs=(),
        )

    def compile_activation(
        self,
        request: ActivationRequest,
        *,
        evaluated_at: datetime | None = None,
    ) -> OrganActivationPlan:
        projection = self.projection()
        evaluation_time = evaluated_at or self._clock()
        if (
            evaluation_time.tzinfo is None
            or evaluation_time.utcoffset() is None
        ):
            raise OrganRegistryError("activation evaluation time must be timezone-aware")
        if request.requested_at > evaluation_time:
            raise OrganRegistryError("activation request is from the future")
        if request.expires_at <= evaluation_time:
            raise OrganRegistryError("activation request is expired")
        entry = self._find_organ(request.organ_id, projection)
        if entry.registry_state not in ACTIVATABLE_STATES:
            raise OrganRegistryError(
                f"organ {entry.organ_id!r} is {entry.registry_state!r}, not admitted"
            )
        if entry.endpoint is None:
            raise OrganRegistryError("admitted organ has no direct endpoint")
        capability = self._find_capability(entry, request.capability_id)
        primitive = next(
            (
                item
                for item in capability.primitives
                if item.primitive_id == request.primitive_id
            ),
            None,
        )
        if primitive is None:
            raise OrganRegistryError("requested primitive is not declared")
        if request.requested_policy_family != primitive.policy_family:
            raise OrganRegistryError("requested policy does not match primitive policy")
        if request.credential_class != capability.credential_class:
            raise OrganRegistryError("credential class does not match capability contour")
        if primitive.approval_owner is not None:
            if (
                request.approval_ref is None
                or request.approval_ref.owner != primitive.approval_owner
            ):
                raise OrganRegistryError(
                    "approval evidence does not match primitive approval owner"
                )
        if request.expires_at > projection.expires_at:
            raise OrganRegistryError("activation request outlives registry projection")
        if request.observed_server_schema_digest != entry.endpoint.server_schema_digest:
            raise OrganRegistryError("server schema digest drift blocks activation")
        expected_consumer = (
            entry.revisions.consumer_schema.schema_digest
            if entry.revisions.consumer_schema is not None
            else None
        )
        if request.observed_consumer_schema_digest != expected_consumer:
            raise OrganRegistryError("consumer schema digest drift blocks activation")
        consumer = next(
            (
                item
                for item in entry.consumer_compatibility
                if item.consumer_id == request.consumer_id
            ),
            None,
        )
        if (
            consumer is None
            or consumer.support_state != "supported"
            or consumer.evidence_ref is None
        ):
            raise OrganRegistryError(
                "consumer is not explicitly supported by owner evidence"
            )
        if consumer.observed_schema_digest != request.observed_consumer_schema_digest:
            raise OrganRegistryError(
                "selected consumer schema observation does not match the request"
            )
        if not set(consumer.protocol_versions).intersection(
            entry.endpoint.protocol_versions
        ):
            raise OrganRegistryError(
                "selected consumer has no compatible endpoint protocol"
            )
        expected_evidence = {
            (item.owner, item.evidence_ref, item.revision)
            for item in entry.activation_preconditions
        }
        supplied_evidence = {
            (item.owner, item.evidence_ref, item.revision)
            for item in request.precondition_evidence
        }
        if not expected_evidence.issubset(supplied_evidence):
            raise OrganRegistryError("required activation preconditions are missing")
        evidence_expiries: list[datetime] = []
        for evidence in request.precondition_evidence:
            if evidence.observed_at > request.requested_at:
                raise OrganRegistryError("precondition evidence is from the future")
            if evidence.expires_at is not None:
                if evidence.expires_at <= evaluation_time:
                    raise OrganRegistryError(
                        "precondition evidence is expired at plan compilation"
                    )
                evidence_expiries.append(evidence.expires_at)
        if request.approval_ref is not None:
            if request.approval_ref.observed_at > request.requested_at:
                raise OrganRegistryError("approval evidence is from the future")
            if request.approval_ref.expires_at is not None:
                if request.approval_ref.expires_at <= evaluation_time:
                    raise OrganRegistryError(
                        "approval evidence is expired at plan compilation"
                    )
                evidence_expiries.append(request.approval_ref.expires_at)
        if entry.revisions.package is None or entry.revisions.deploy is None:
            raise OrganRegistryError("package/deploy identity is incomplete")
        plan_expiry = min(
            request.expires_at,
            projection.expires_at,
            *evidence_expiries,
        )
        unsigned = {
            "schema_version": "aoa_organ_activation_plan_v1",
            "plan_kind": "candidate_only",
            "execution_authorized": False,
            "registry_digest": projection.projection_digest,
            "organ_id": entry.organ_id,
            "capability_id": capability.capability_id,
            "primitive_id": primitive.primitive_id,
            "owners": entry.owners.model_dump(mode="json"),
            "policy_family": primitive.policy_family,
            "effect_class": primitive.effect_class,
            "credential_class": capability.credential_class,
            "endpoint": entry.endpoint.model_dump(mode="json"),
            "source_revision": entry.revisions.source.model_dump(mode="json"),
            "package_revision": entry.revisions.package.model_dump(mode="json"),
            "deploy_revision": entry.revisions.deploy.model_dump(mode="json"),
            "server_schema_digest": request.observed_server_schema_digest,
            "consumer_schema_digest": request.observed_consumer_schema_digest,
            "consumer_id": request.consumer_id,
            "precondition_evidence": [
                item.model_dump(mode="json")
                for item in request.precondition_evidence
            ],
            "approval_ref": (
                request.approval_ref.model_dump(mode="json")
                if request.approval_ref is not None
                else None
            ),
            "exact_effect_target": request.exact_effect_target,
            "expires_at": plan_expiry.isoformat().replace("+00:00", "Z"),
            "rollback_route": primitive.rollback_route or entry.rollback_route,
        }
        return OrganActivationPlan.model_validate(
            {"plan_id": sha256_digest(unsigned), **unsigned}
        )

    @staticmethod
    def _find_organ(
        organ_id: str,
        projection: OrganRegistryProjection,
    ) -> OrganProjectionEntry:
        for entry in projection.entries:
            if entry.organ_id == organ_id:
                return entry
        raise OrganRegistryError(f"unknown organ {organ_id!r}")


def _catalog_capability(
    organ_id: str,
    capability: CapabilityContract,
) -> CatalogCapability:
    return CatalogCapability(
        capability_id=capability.capability_id,
        summary=capability.summary,
        policy_family=capability.policy_family,
        primitive_ids=tuple(item.primitive_id for item in capability.primitives),
        primitive_namespaces=tuple(
            f"{organ_id}.{capability.capability_id}.{item.primitive_id}"
            for item in capability.primitives
        ),
        effect_classes=tuple(
            sorted({item.effect_class for item in capability.primitives})
        ),
        task_intent_terms=capability.task_intent_terms,
    )


def _matches(
    entry: OrganProjectionEntry,
    capabilities: tuple[CatalogCapability, ...],
    tokens: set[str],
) -> bool:
    haystack = " ".join(
        (
            entry.organ_id,
            entry.display_name,
            entry.description,
            *(
                value
                for capability in capabilities
                for value in (
                    capability.capability_id,
                    capability.summary,
                    *capability.task_intent_terms,
                )
            ),
        )
    ).lower().replace("_", " ")
    return all(token in haystack for token in tokens)
