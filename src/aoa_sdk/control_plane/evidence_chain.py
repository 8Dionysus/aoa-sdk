"""Assemble and persist owner-safe Agent OS evidence-chain projections."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Mapping
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, TypeVar

from ..contracts.control_plane import (
    CloseoutBundleRef,
    ContentRef,
    ControlPlaneContractError,
    EvalVerdictRef,
    EvidenceBundleRef,
    ExecutionEvent,
    MemoryReceiptRef,
    ProvenanceRef,
    RouteDecision,
    RouteExplanation,
    RouteIntent,
    RunOutcome,
    RunPlan,
    SessionHandle,
    assert_execution_event_chain,
    assert_route_plan_chain,
    canonical_digest,
)
from ..contracts.evidence_chain import (
    CheckpointReceiptRef,
    EvidenceChain,
    EvidenceChainIndex,
    EvidenceChainIndexEntry,
)
from ..errors import AoASDKError


ZERO_DIGEST = "sha256:" + "0" * 64


class EvidenceChainError(AoASDKError, ValueError):
    """The unified evidence chain or its explicit repository is invalid."""


def evidence_chain_digest(chain: EvidenceChain) -> str:
    """Return the canonical digest without the self-referential field."""

    return canonical_digest(chain, exclude={"chain_digest"})


def assemble_evidence_chain(
    *,
    intent: RouteIntent,
    decision: RouteDecision,
    explanation: RouteExplanation,
    plan: RunPlan,
    session: SessionHandle,
    events: Iterable[ExecutionEvent],
    runtime_outcome: RunOutcome,
    eval_verdict_refs: Iterable[EvalVerdictRef] = (),
    memory_receipt_refs: Iterable[MemoryReceiptRef] = (),
    checkpoint_receipt_refs: Iterable[CheckpointReceiptRef] = (),
    closeout_bundle_ref: CloseoutBundleRef | None = None,
    assembled_at: datetime,
    assembled_by: ProvenanceRef,
) -> EvidenceChain:
    """Build one exact chain without copying external proof or memory payloads."""

    event_sequence = tuple(events)
    eval_refs = tuple(eval_verdict_refs)
    memory_refs = tuple(memory_receipt_refs)
    checkpoint_refs = tuple(checkpoint_receipt_refs)
    _assert_base_chain(
        intent,
        decision,
        explanation,
        plan,
        session,
        event_sequence,
        runtime_outcome,
        assembled_at=assembled_at,
    )
    if assembled_by.owner_repo != "aoa-sdk":
        raise EvidenceChainError(
            "evidence chain assembler provenance must be owned by aoa-sdk"
        )
    _assert_ref_ids_unique("eval verdict", eval_refs)
    _assert_ref_ids_unique("memory receipt", memory_refs)
    _assert_ref_ids_unique("checkpoint receipt", checkpoint_refs)

    evidence_covered = _validate_owned_requirement_refs(
        runtime_outcome.evidence_bundle_refs,
        {
            item.requirement_id: item.producer_owner
            for item in plan.evidence_requirements
        },
        label="runtime evidence",
    )
    eval_covered = _validate_owned_requirement_refs(
        eval_refs,
        {
            item.requirement_id: item.eval_owner_ref.owner_repo
            for item in plan.eval_requirements
        },
        label="eval verdict",
        require_coverage=True,
    )
    retention_covered = _validate_owned_requirement_refs(
        memory_refs,
        {
            item.requirement_id: item.memory_owner_ref.owner_repo
            for item in plan.retention_requirements
        },
        label="memory receipt",
        require_coverage=True,
    )
    checkpoint_missing = _checkpoint_missing(
        plan,
        event_sequence,
        checkpoint_refs,
    )
    closeout_missing = _closeout_missing(
        plan,
        closeout_bundle_ref,
        evidence_covered=evidence_covered,
        eval_covered=eval_covered,
        retention_covered=retention_covered,
        checkpoint_refs=checkpoint_refs,
    )

    missing_required = {
        item.requirement_id
        for item in plan.evidence_requirements
        if item.terminal_required and item.requirement_id not in evidence_covered
    }
    missing_required.update(
        item.requirement_id
        for item in plan.eval_requirements
        if item.verdict_required_for_closeout
        and item.requirement_id not in eval_covered
    )
    missing_required.update(
        item.requirement_id
        for item in plan.retention_requirements
        if item.receipt_required_for_closeout
        and item.requirement_id not in retention_covered
    )
    missing_required.update(checkpoint_missing)
    missing_required.update(closeout_missing)

    unresolved_optional = {
        item.requirement_id
        for item in plan.evidence_requirements
        if not item.terminal_required and item.requirement_id not in evidence_covered
    }
    unresolved_optional.update(
        item.requirement_id
        for item in plan.eval_requirements
        if not item.verdict_required_for_closeout
        and item.requirement_id not in eval_covered
    )
    unresolved_optional.update(
        item.requirement_id
        for item in plan.retention_requirements
        if not item.receipt_required_for_closeout
        and item.requirement_id not in retention_covered
    )

    missing = tuple(sorted(missing_required))
    unresolved = tuple(sorted(unresolved_optional))
    if closeout_bundle_ref is not None and missing:
        raise EvidenceChainError(
            "owner closeout bundle cannot precede a complete evidence chain"
        )
    chain = EvidenceChain(
        chain_id=_chain_id(session.session_id),
        session_id=session.session_id,
        correlation_id=session.correlation_id,
        disposition="complete" if not missing else "partial",
        intent=intent,
        decision=decision,
        explanation=explanation,
        plan=plan,
        session=session,
        events=event_sequence,
        runtime_outcome=runtime_outcome,
        eval_verdict_refs=eval_refs,
        memory_receipt_refs=memory_refs,
        checkpoint_receipt_refs=checkpoint_refs,
        closeout_bundle_ref=closeout_bundle_ref,
        missing_required_refs=missing,
        unresolved_optional_refs=unresolved,
        assembled_at=_aware(assembled_at, "assembled_at"),
        assembled_by=assembled_by,
        chain_digest=ZERO_DIGEST,
    )
    return chain.model_copy(update={"chain_digest": evidence_chain_digest(chain)})


def assert_evidence_chain(chain: EvidenceChain) -> None:
    """Rebuild every derived field and require byte-stable contract identity."""

    if chain.chain_digest != evidence_chain_digest(chain):
        raise EvidenceChainError("evidence chain digest is invalid")
    expected = assemble_evidence_chain(
        intent=chain.intent,
        decision=chain.decision,
        explanation=chain.explanation,
        plan=chain.plan,
        session=chain.session,
        events=chain.events,
        runtime_outcome=chain.runtime_outcome,
        eval_verdict_refs=chain.eval_verdict_refs,
        memory_receipt_refs=chain.memory_receipt_refs,
        checkpoint_receipt_refs=chain.checkpoint_receipt_refs,
        closeout_bundle_ref=chain.closeout_bundle_ref,
        assembled_at=chain.assembled_at,
        assembled_by=chain.assembled_by,
    )
    if expected != chain:
        raise EvidenceChainError(
            "evidence chain fields differ from the canonical reconstruction"
        )


def assert_evidence_chain_complete(chain: EvidenceChain) -> CloseoutBundleRef:
    """Require owner-complete refs and return the exact runtime closeout ref."""

    assert_evidence_chain(chain)
    if chain.disposition != "complete" or chain.closeout_bundle_ref is None:
        raise EvidenceChainError(
            "partial evidence chain cannot close the runtime lifecycle"
        )
    return chain.closeout_bundle_ref


class EvidenceChainRepository:
    """Explicit local projection store with exact session/receipt indexes."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        if not self.root.is_absolute():
            raise EvidenceChainError("evidence chain repository root must be absolute")

    def record(self, chain: EvidenceChain) -> EvidenceChainIndexEntry:
        """Persist an immutable revision and atomically advance its exact index."""

        assert_evidence_chain(chain)
        self.root.mkdir(parents=True, exist_ok=True)
        with self._lock():
            index = self._load_index()
            prior_entries = [
                item for item in index.entries if item.session_id == chain.session_id
            ]
            for item in prior_entries:
                if item.chain_digest == chain.chain_digest:
                    return item
            if prior_entries:
                previous_entry = max(
                    prior_entries,
                    key=lambda item: item.revision,
                )
                previous = self._load_entry(previous_entry)
                _assert_monotonic_revision(previous, chain)
                revision = previous_entry.revision + 1
            else:
                revision = 1
            object_ref = f"objects/{chain.chain_digest.removeprefix('sha256:')}.json"
            object_path = self._resolve_object_ref(object_ref)
            if not object_path.exists():
                _atomic_write_json(
                    object_path,
                    chain.model_dump(mode="json"),
                )
            entry = EvidenceChainIndexEntry(
                session_id=chain.session_id,
                chain_id=chain.chain_id,
                chain_digest=chain.chain_digest,
                disposition=chain.disposition,
                revision=revision,
                object_ref=object_ref,
                closeout_ref_id=(
                    chain.closeout_bundle_ref.ref_id
                    if chain.closeout_bundle_ref is not None
                    else None
                ),
            )
            next_index = EvidenceChainIndex(entries=(*index.entries, entry))
            _atomic_write_json(
                self._index_path,
                next_index.model_dump(mode="json"),
            )
            return entry

    def resolve_session(
        self,
        session: SessionHandle | str,
    ) -> EvidenceChain:
        """Resolve one exact current chain by stable session identity."""

        session_id = (
            session.session_id if isinstance(session, SessionHandle) else session
        )
        index = self._load_index()
        matches = [item for item in index.entries if item.session_id == session_id]
        if not matches:
            raise EvidenceChainError(
                f"no evidence chain is indexed for session {session_id!r}"
            )
        chain = self._load_entry(max(matches, key=lambda item: item.revision))
        if isinstance(session, SessionHandle) and chain.session != session:
            raise EvidenceChainError(
                "indexed evidence chain differs from the supplied session handle"
            )
        return chain

    def resolve_closeout(
        self,
        closeout: CloseoutBundleRef | str,
    ) -> EvidenceChain:
        """Resolve one exact complete chain by owner closeout receipt identity."""

        ref_id = (
            closeout.ref_id if isinstance(closeout, CloseoutBundleRef) else closeout
        )
        index = self._load_index()
        matches = [item for item in index.entries if item.closeout_ref_id == ref_id]
        if len(matches) != 1:
            raise EvidenceChainError(
                f"closeout receipt {ref_id!r} does not resolve to one chain"
            )
        chain = self._load_entry(matches[0])
        if (
            isinstance(closeout, CloseoutBundleRef)
            and chain.closeout_bundle_ref != closeout
        ):
            raise EvidenceChainError(
                "indexed evidence chain differs from the supplied closeout receipt"
            )
        return chain

    @property
    def _index_path(self) -> Path:
        return self.root / "index.json"

    def _load_index(self) -> EvidenceChainIndex:
        if not self._index_path.exists():
            return EvidenceChainIndex()
        try:
            return EvidenceChainIndex.model_validate_json(
                self._index_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            raise EvidenceChainError(
                "evidence chain repository index is invalid"
            ) from exc

    def _load_entry(self, entry: EvidenceChainIndexEntry) -> EvidenceChain:
        path = self._resolve_object_ref(entry.object_ref)
        try:
            chain = EvidenceChain.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise EvidenceChainError(
                "indexed evidence chain object is unavailable or invalid"
            ) from exc
        assert_evidence_chain(chain)
        if (
            chain.session_id != entry.session_id
            or chain.chain_id != entry.chain_id
            or chain.chain_digest != entry.chain_digest
            or chain.disposition != entry.disposition
            or (
                chain.closeout_bundle_ref.ref_id
                if chain.closeout_bundle_ref is not None
                else None
            )
            != entry.closeout_ref_id
        ):
            raise EvidenceChainError(
                "evidence chain index entry differs from its object"
            )
        return chain

    def _resolve_object_ref(self, object_ref: str) -> Path:
        relative = Path(object_ref)
        if relative.is_absolute() or ".." in relative.parts:
            raise EvidenceChainError(
                "evidence chain index contains an unsafe object ref"
            )
        path = (self.root / relative).resolve()
        try:
            path.relative_to(self.root.resolve())
        except ValueError as exc:
            raise EvidenceChainError(
                "evidence chain object ref escapes the repository"
            ) from exc
        return path

    @contextmanager
    def _lock(self) -> Iterator[None]:
        self.root.mkdir(parents=True, exist_ok=True)
        lock_path = self.root / ".index.lock"
        with lock_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _assert_base_chain(
    intent: RouteIntent,
    decision: RouteDecision,
    explanation: RouteExplanation,
    plan: RunPlan,
    session: SessionHandle,
    events: tuple[ExecutionEvent, ...],
    outcome: RunOutcome,
    *,
    assembled_at: datetime,
) -> None:
    try:
        assert_route_plan_chain(intent, decision, explanation, plan)
        assert_execution_event_chain(events, session=session)
    except ControlPlaneContractError as exc:
        raise EvidenceChainError(str(exc)) from exc
    plan_ref = ContentRef(
        object_id=plan.plan_id,
        owner_repo=plan.provenance.owner_repo,
        schema_version=plan.schema_version,
        digest=plan.plan_digest,
    )
    if (
        session.plan_ref != plan_ref
        or session.plan_digest != plan.plan_digest
        or session.snapshot_digest != plan.snapshot.snapshot_digest
        or session.correlation_id != plan.correlation_id
    ):
        raise EvidenceChainError("session handle does not reference the exact run plan")
    if (
        outcome.session_id != session.session_id
        or outcome.correlation_id != session.correlation_id
        or outcome.plan_digest != plan.plan_digest
        or outcome.runtime_result_ref.owner_repo != plan.runtime_profile.runtime_owner
    ):
        raise EvidenceChainError(
            "runtime outcome is outside the exact session or runtime owner"
        )
    if (
        outcome.eval_verdict_refs
        or outcome.memory_receipt_refs
        or outcome.closeout_bundle_ref is not None
    ):
        raise EvidenceChainError(
            "runtime outcome must not synthesize eval, memory, or closeout refs"
        )
    if not events:
        raise EvidenceChainError("evidence chain requires runtime events")
    outcome_ref = ContentRef(
        object_id=outcome.outcome_id,
        owner_repo=outcome.runtime_result_ref.owner_repo,
        schema_version=outcome.schema_version,
        digest=canonical_digest(outcome),
    )
    outcome_events = [
        (index, item)
        for index, item in enumerate(events)
        if item.event_kind == "outcome" and item.outcome_ref == outcome_ref
    ]
    if len(outcome_events) != 1:
        raise EvidenceChainError(
            "verified event stream must contain the exact runtime outcome once"
        )
    outcome_index, _outcome_event = outcome_events[0]
    trailing_events = events[outcome_index + 1 :]
    if any(item.event_kind != "command_ack" for item in trailing_events):
        raise EvidenceChainError(
            "only command acknowledgement may follow the exact runtime outcome"
        )
    assembled = _aware(assembled_at, "assembled_at")
    if assembled < outcome.completed_at:
        raise EvidenceChainError(
            "evidence chain assembly cannot predate the runtime outcome"
        )


_OwnedRefT = TypeVar(
    "_OwnedRefT",
    EvidenceBundleRef,
    EvalVerdictRef,
    MemoryReceiptRef,
)


def _validate_owned_requirement_refs(
    refs: Iterable[_OwnedRefT],
    expected_owners: Mapping[str, str],
    *,
    label: str,
    require_coverage: bool = False,
) -> set[str]:
    covered: set[str] = set()
    for ref in refs:
        if require_coverage and not ref.satisfies_requirement_ids:
            raise EvidenceChainError(
                f"{label} ref must satisfy at least one declared requirement"
            )
        if len(ref.satisfies_requirement_ids) != len(
            set(ref.satisfies_requirement_ids)
        ):
            raise EvidenceChainError(f"{label} ref requirement coverage must be unique")
        for requirement_id in ref.satisfies_requirement_ids:
            owner = expected_owners.get(requirement_id)
            if owner is None:
                raise EvidenceChainError(
                    f"{label} ref claims unknown requirement {requirement_id!r}"
                )
            if ref.provenance.owner_repo != owner:
                raise EvidenceChainError(
                    f"{label} ref owner differs from requirement {requirement_id!r}"
                )
            covered.add(requirement_id)
    return covered


def _checkpoint_missing(
    plan: RunPlan,
    events: tuple[ExecutionEvent, ...],
    refs: tuple[CheckpointReceiptRef, ...],
) -> set[str]:
    known_steps = {item.step_id for item in plan.steps}
    wrong_owners = {
        ref.provenance.owner_repo
        for ref in refs
        if ref.provenance.owner_repo != plan.checkpoint_policy.owner.owner_repo
    }
    if wrong_owners:
        raise EvidenceChainError(
            "checkpoint receipt owner differs from the plan checkpoint owner"
        )
    if any(not set(ref.covered_step_ids).issubset(known_steps) for ref in refs):
        raise EvidenceChainError(
            "checkpoint receipt claims a step outside the run plan"
        )
    eligible = [ref for ref in refs if ref.review_status in {"reviewed", "closed"}]
    covered_steps = {step_id for ref in eligible for step_id in ref.covered_step_ids}
    missing = {
        f"checkpoint:step:{step_id}"
        for step_id in plan.checkpoint_policy.required_after_step_ids
        if step_id not in covered_steps
    }
    if (
        plan.checkpoint_policy.required_on_pause
        and any(item.state_after == "paused" for item in events)
        and not any(item.covers_pause for item in eligible)
    ):
        missing.add("checkpoint:pause")
    if (
        plan.checkpoint_policy.required_on_recoverable_failure
        and any(item.state_after == "recoverable_failure" for item in events)
        and not any(item.covers_recoverable_failure for item in eligible)
    ):
        missing.add("checkpoint:recoverable-failure")
    return missing


def _closeout_missing(
    plan: RunPlan,
    bundle: CloseoutBundleRef | None,
    *,
    evidence_covered: set[str],
    eval_covered: set[str],
    retention_covered: set[str],
    checkpoint_refs: tuple[CheckpointReceiptRef, ...],
) -> set[str]:
    if bundle is None:
        return {
            "closeout:bundle",
            *(item.requirement_id for item in plan.closeout_requirements),
        }
    requirements = {item.requirement_id: item for item in plan.closeout_requirements}
    unknown = set(bundle.satisfies_requirement_ids) - set(requirements)
    if unknown:
        raise EvidenceChainError(
            f"closeout bundle claims unknown requirements: {sorted(unknown)}"
        )
    missing: set[str] = set()
    available_kinds = {
        item.artifact_kind
        for item in plan.evidence_requirements
        if item.requirement_id in evidence_covered
    }
    if eval_covered:
        available_kinds.add("eval_verdict")
    if retention_covered:
        available_kinds.add("memory_receipt")
    if any(item.review_status in {"reviewed", "closed"} for item in checkpoint_refs):
        available_kinds.add("checkpoint_receipt")
    for requirement in plan.closeout_requirements:
        if (
            requirement.requirement_id not in bundle.satisfies_requirement_ids
            or bundle.provenance.owner_repo != requirement.owner_ref.owner_repo
        ):
            missing.add(requirement.requirement_id)
        for artifact_kind in requirement.required_ref_kinds:
            if artifact_kind not in available_kinds:
                missing.add(
                    f"closeout-kind:{requirement.requirement_id}:{artifact_kind}"
                )
    return missing


def _assert_ref_ids_unique(
    label: str,
    refs: Iterable[EvalVerdictRef | MemoryReceiptRef | CheckpointReceiptRef],
) -> None:
    values = [item.ref_id for item in refs]
    if len(values) != len(set(values)):
        raise EvidenceChainError(f"{label} ref ids must be unique")


def _assert_monotonic_revision(
    previous: EvidenceChain,
    current: EvidenceChain,
) -> None:
    core_fields = (
        "chain_id",
        "session_id",
        "correlation_id",
        "intent",
        "decision",
        "explanation",
        "plan",
        "session",
        "events",
        "runtime_outcome",
        "assembled_by",
    )
    if any(
        getattr(previous, field) != getattr(current, field) for field in core_fields
    ):
        raise EvidenceChainError(
            "evidence chain revision changed immutable execution identity"
        )
    for label, prior, next_refs in (
        (
            "eval verdict",
            previous.eval_verdict_refs,
            current.eval_verdict_refs,
        ),
        (
            "memory receipt",
            previous.memory_receipt_refs,
            current.memory_receipt_refs,
        ),
        (
            "checkpoint receipt",
            previous.checkpoint_receipt_refs,
            current.checkpoint_receipt_refs,
        ),
    ):
        next_by_id = {item.ref_id: item for item in next_refs}
        if any(next_by_id.get(item.ref_id) != item for item in prior):
            raise EvidenceChainError(
                f"evidence chain revision removed or changed a {label} ref"
            )
    if (
        previous.closeout_bundle_ref is not None
        and previous.closeout_bundle_ref != current.closeout_bundle_ref
    ):
        raise EvidenceChainError(
            "evidence chain revision changed the owner closeout receipt"
        )
    if previous.disposition == "complete":
        raise EvidenceChainError("a complete evidence chain is immutable")
    if current.assembled_at < previous.assembled_at:
        raise EvidenceChainError(
            "evidence chain revision predates the previous projection"
        )


def _chain_id(session_id: str) -> str:
    token = hashlib.sha256(session_id.encode("utf-8")).hexdigest()
    return f"evidence-chain:{token}"


def _aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise EvidenceChainError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
