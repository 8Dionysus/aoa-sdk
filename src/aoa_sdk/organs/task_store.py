"""Durable protocol-independent task store with principal-bound CAS updates."""

from __future__ import annotations

import fcntl
import hashlib
import os
import secrets
import stat
import tempfile
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator, Literal

from pydantic import ValidationError

from ..contracts.control_plane import canonical_digest
from ..contracts.tasks import (
    AcceptedTaskInput,
    OwnerTaskRecord,
    TASK_STATUSES,
    TaskAuditReceipt,
    TaskInputRequest,
    TaskMutationResult,
    TaskStoreQuotaStatus,
    TaskStoreStatus,
    TERMINAL_TASK_STATUSES,
)
from ..errors import AoASDKError
from .registry import (
    OrganRegistryError,
    canonical_json_bytes,
    reject_secret_material,
    sha256_digest,
)


class TaskStoreError(AoASDKError, ValueError):
    """A task is absent, unauthorized, stale, conflicting, or malformed."""


@dataclass(frozen=True)
class TaskStoreLimits:
    maximum_active_tasks: int = 256
    maximum_active_tasks_per_principal: int = 32
    maximum_arguments_bytes: int = 64 * 1024
    maximum_record_bytes: int = 256 * 1024
    maximum_inputs: int = 32
    maximum_ttl_seconds: int = 7 * 24 * 60 * 60


class FileTaskStore:
    """Small local durable store; no listing or authority by task ID."""

    def __init__(self, root: str | Path, *, limits: TaskStoreLimits | None = None):
        # Preserve the caller's final path component so a symlink cannot be
        # normalized away before the store applies its fail-closed path gate.
        self.root = Path(os.path.abspath(Path(root).expanduser()))
        self.limits = limits or TaskStoreLimits()
        self.records_root = self.root / "records"
        self.audit_root = self.root / "audit"
        self.lock_path = self.root / ".task-store.lock"
        self._ensure_root()

    def create(
        self,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        tool_name: str,
        arguments: Any,
        owner_run_ref: str,
        idempotency_key: str,
        ttl_seconds: int,
        poll_interval_ms: int,
        now: datetime | None = None,
    ) -> TaskMutationResult:
        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        if not 1 <= ttl_seconds <= self.limits.maximum_ttl_seconds:
            raise TaskStoreError("task TTL is outside the configured bound")
        _reject_task_secret_material(arguments, context="task arguments")
        arguments_bytes = canonical_json_bytes(arguments)
        if len(arguments_bytes) > self.limits.maximum_arguments_bytes:
            raise TaskStoreError("task arguments exceed the configured byte bound")
        arguments_digest = sha256_digest(arguments)
        with self._locked():
            records = self._load_all_records()
            for existing in records:
                if (
                    existing.principal_id == principal_id
                    and existing.organ_id == organ_id
                    and existing.contour_id == contour_id
                    and existing.tool_name == tool_name
                    and existing.idempotency_key == idempotency_key
                    and existing.expires_at > timestamp
                ):
                    if existing.arguments_digest != arguments_digest:
                        raise TaskStoreError(
                            "idempotency key conflicts with different task arguments"
                        )
                    return self._result(
                        existing,
                        action="create",
                        prior_revision=existing.revision,
                        outcome="idempotent",
                        occurred_at=timestamp,
                    )
            active = [
                item
                for item in records
                if item.status not in TERMINAL_TASK_STATUSES
                and item.expires_at > timestamp
            ]
            if len(active) >= self.limits.maximum_active_tasks:
                raise TaskStoreError("global active task quota exceeded")
            if sum(item.principal_id == principal_id for item in active) >= (
                self.limits.maximum_active_tasks_per_principal
            ):
                raise TaskStoreError("principal active task quota exceeded")
            record = OwnerTaskRecord(
                task_id=secrets.token_urlsafe(32),
                principal_id=principal_id,
                organ_id=organ_id,
                contour_id=contour_id,
                tool_name=tool_name,
                arguments_digest=arguments_digest,
                owner_run_ref=owner_run_ref,
                idempotency_key=idempotency_key,
                status="working",
                revision=1,
                created_at=timestamp,
                updated_at=timestamp,
                expires_at=timestamp + timedelta(seconds=ttl_seconds),
                poll_interval_ms=poll_interval_ms,
            )
            self._write_record(record)
            return self._result(
                record,
                action="create",
                prior_revision=0,
                outcome="applied",
                occurred_at=timestamp,
            )

    def get(
        self,
        task_id: str,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        now: datetime | None = None,
    ) -> OwnerTaskRecord:
        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        with self._locked():
            record = self._load_record(task_id)
            self._authorize(record, principal_id, organ_id, contour_id)
            if record.expires_at <= timestamp and record.status != "expired":
                raise TaskStoreError("task is expired; owner must persist expiry")
            self._result(
                record,
                action="get",
                prior_revision=record.revision,
                outcome="idempotent",
                occurred_at=timestamp,
            )
            return record

    def require_input(
        self,
        task_id: str,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        expected_revision: int,
        request: TaskInputRequest,
        now: datetime | None = None,
    ) -> TaskMutationResult:
        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        with self._locked():
            record = self._authorized_for_update(
                task_id,
                principal_id,
                organ_id,
                contour_id,
                expected_revision,
                timestamp,
            )
            self._require_nonterminal(record)
            if len(record.outstanding_inputs) >= self.limits.maximum_inputs:
                raise TaskStoreError("outstanding task input limit exceeded")
            if request.expires_at > record.expires_at:
                raise TaskStoreError("task input request cannot outlive the task")
            if any(
                item.request_key == request.request_key
                for item in record.outstanding_inputs
            ):
                raise TaskStoreError("task input request key already exists")
            updated = self._replace(
                record,
                timestamp,
                status="input_required",
                outstanding_inputs=tuple((*record.outstanding_inputs, request)),
            )
            self._write_record(updated)
            return self._result(
                updated,
                action="require_input",
                prior_revision=record.revision,
                outcome="applied",
                occurred_at=timestamp,
            )

    def apply_input(
        self,
        task_id: str,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        expected_revision: int,
        request_key: str,
        input_key: str,
        input_value: Any,
        now: datetime | None = None,
    ) -> TaskMutationResult:
        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        _reject_task_secret_material(input_value, context="task input")
        digest = sha256_digest(input_value)
        with self._locked():
            record = self._load_record(task_id)
            self._authorize(record, principal_id, organ_id, contour_id)
            existing = next(
                (item for item in record.accepted_inputs if item.input_key == input_key),
                None,
            )
            if existing is not None:
                if existing.request_key != request_key or existing.input_digest != digest:
                    raise TaskStoreError("input key conflicts with prior accepted input")
                return self._result(
                    record,
                    action="apply_input",
                    prior_revision=record.revision,
                    outcome="idempotent",
                    occurred_at=timestamp,
                )
            self._assert_revision(record, expected_revision)
            self._require_live(record, timestamp)
            request = next(
                (
                    item
                    for item in record.outstanding_inputs
                    if item.request_key == request_key
                ),
                None,
            )
            if request is None:
                raise TaskStoreError("unknown outstanding task input request")
            if request.expires_at <= timestamp:
                raise TaskStoreError("task input request is expired")
            accepted = AcceptedTaskInput(
                request_key=request_key,
                input_key=input_key,
                input_digest=digest,
                accepted_at=timestamp,
            )
            outstanding = tuple(
                item for item in record.outstanding_inputs if item.request_key != request_key
            )
            updated = self._replace(
                record,
                timestamp,
                status="input_required" if outstanding else "working",
                outstanding_inputs=outstanding,
                accepted_inputs=tuple((*record.accepted_inputs, accepted)),
            )
            self._write_record(updated)
            return self._result(
                updated,
                action="apply_input",
                prior_revision=record.revision,
                outcome="applied",
                occurred_at=timestamp,
            )

    def request_cancel(
        self,
        task_id: str,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        expected_revision: int,
        now: datetime | None = None,
    ) -> TaskMutationResult:
        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        with self._locked():
            record = self._load_record(task_id)
            self._authorize(record, principal_id, organ_id, contour_id)
            if record.cancellation_outcome in {"pending", "accepted"}:
                return self._result(
                    record,
                    action="request_cancel",
                    prior_revision=record.revision,
                    outcome="idempotent",
                    occurred_at=timestamp,
                )
            self._assert_revision(record, expected_revision)
            self._require_live(record, timestamp)
            if record.status in TERMINAL_TASK_STATUSES:
                raise TaskStoreError("terminal task cannot accept cancellation")
            updated = self._replace(
                record,
                timestamp,
                cancellation_requested_at=timestamp,
                cancellation_outcome="pending",
            )
            self._write_record(updated)
            return self._result(
                updated,
                action="request_cancel",
                prior_revision=record.revision,
                outcome="applied",
                occurred_at=timestamp,
            )

    def acknowledge_cancel(
        self,
        task_id: str,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        expected_revision: int,
        accepted: bool,
        now: datetime | None = None,
    ) -> TaskMutationResult:
        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        with self._locked():
            record = self._authorized_for_update(
                task_id,
                principal_id,
                organ_id,
                contour_id,
                expected_revision,
                timestamp,
            )
            if record.cancellation_outcome != "pending":
                raise TaskStoreError("task has no pending cancellation")
            updated = self._replace(
                record,
                timestamp,
                status="cancelled" if accepted else record.status,
                outstanding_inputs=() if accepted else record.outstanding_inputs,
                cancellation_outcome="accepted" if accepted else "rejected",
            )
            self._write_record(updated)
            return self._result(
                updated,
                action="acknowledge_cancel",
                prior_revision=record.revision,
                outcome="applied",
                occurred_at=timestamp,
            )

    def complete(
        self,
        task_id: str,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        expected_revision: int,
        result_ref: str,
        result_digest: str,
        evidence_refs: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> TaskMutationResult:
        return self._terminal(
            task_id,
            principal_id=principal_id,
            organ_id=organ_id,
            contour_id=contour_id,
            expected_revision=expected_revision,
            status="completed",
            result_ref=result_ref,
            result_digest=result_digest,
            evidence_refs=evidence_refs,
            now=now,
        )

    def fail(
        self,
        task_id: str,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        expected_revision: int,
        error_ref: str,
        error_digest: str,
        evidence_refs: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> TaskMutationResult:
        return self._terminal(
            task_id,
            principal_id=principal_id,
            organ_id=organ_id,
            contour_id=contour_id,
            expected_revision=expected_revision,
            status="failed",
            error_ref=error_ref,
            error_digest=error_digest,
            evidence_refs=evidence_refs,
            now=now,
        )

    def expire(
        self,
        task_id: str,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        expected_revision: int,
        now: datetime | None = None,
    ) -> TaskMutationResult:
        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        with self._locked():
            record = self._load_record(task_id)
            self._authorize(record, principal_id, organ_id, contour_id)
            if record.status == "expired":
                return self._result(
                    record,
                    action="expire",
                    prior_revision=record.revision,
                    outcome="idempotent",
                    occurred_at=timestamp,
                )
            self._assert_revision(record, expected_revision)
            if timestamp < record.expires_at:
                raise TaskStoreError("task cannot expire before its TTL")
            if record.status in TERMINAL_TASK_STATUSES:
                raise TaskStoreError("completed terminal task cannot be reclassified")
            updated = self._replace(
                record,
                timestamp,
                status="expired",
                outstanding_inputs=(),
            )
            self._write_record(updated)
            return self._result(
                updated,
                action="expire",
                prior_revision=record.revision,
                outcome="applied",
                occurred_at=timestamp,
            )

    def cleanup_expired(self, *, now: datetime | None = None) -> int:
        """Delete only already-persisted expired records after their TTL."""

        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        removed = 0
        with self._locked():
            for path in self.records_root.glob("*.json"):
                record = self._load_record_path(path)
                if record.status == "expired" and record.expires_at <= timestamp:
                    path.unlink()
                    removed += 1
        return removed

    def status(
        self,
        *,
        now: datetime | None = None,
        orphan_after_seconds: int = 300,
    ) -> TaskStoreStatus:
        """Return aggregate owner-private operations data without enumeration."""

        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        if orphan_after_seconds < 60:
            raise TaskStoreError("orphan observation threshold must be at least 60 seconds")
        threshold = timestamp - timedelta(seconds=orphan_after_seconds)
        with self._locked(shared=True):
            records = self._load_all_records()
        status_counts = Counter(item.status for item in records)
        active = [
            item
            for item in records
            if item.status not in TERMINAL_TASK_STATUSES and item.expires_at > timestamp
        ]
        active_per_principal = Counter(item.principal_id for item in active)
        return TaskStoreStatus(
            observed_at=timestamp,
            record_count=len(records),
            active_count=len(active),
            status_counts={
                status: status_counts[status] for status in TASK_STATUSES
            },
            outstanding_input_count=sum(len(item.outstanding_inputs) for item in active),
            pending_cancellation_count=sum(
                item.cancellation_outcome == "pending" for item in active
            ),
            expired_unpersisted_count=sum(
                item.status not in TERMINAL_TASK_STATUSES
                and item.expires_at <= timestamp
                for item in records
            ),
            orphan_candidate_count=sum(
                item.cancellation_outcome == "pending" and item.updated_at <= threshold
                for item in active
            ),
            orphan_after_seconds=orphan_after_seconds,
            oldest_active_updated_at=(
                min(item.updated_at for item in active) if active else None
            ),
            next_expiry_at=(min(item.expires_at for item in active) if active else None),
            quota=TaskStoreQuotaStatus(
                maximum_active_tasks=self.limits.maximum_active_tasks,
                maximum_active_tasks_per_principal=(
                    self.limits.maximum_active_tasks_per_principal
                ),
                active_tasks=len(active),
                maximum_observed_active_per_principal=max(
                    active_per_principal.values(), default=0
                ),
                global_remaining=max(
                    self.limits.maximum_active_tasks - len(active), 0
                ),
            ),
        )

    def _terminal(
        self,
        task_id: str,
        *,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        expected_revision: int,
        status: Literal["completed", "failed"],
        result_ref: str | None = None,
        result_digest: str | None = None,
        error_ref: str | None = None,
        error_digest: str | None = None,
        evidence_refs: tuple[str, ...],
        now: datetime | None,
    ) -> TaskMutationResult:
        timestamp = _aware_utc(now or datetime.now(timezone.utc))
        with self._locked():
            record = self._authorized_for_update(
                task_id,
                principal_id,
                organ_id,
                contour_id,
                expected_revision,
                timestamp,
            )
            self._require_nonterminal(record)
            cancel_outcome = record.cancellation_outcome
            if cancel_outcome == "pending":
                cancel_outcome = "too_late"
            updated = self._replace(
                record,
                timestamp,
                status=status,
                outstanding_inputs=(),
                cancellation_outcome=cancel_outcome,
                result_ref=result_ref,
                result_digest=result_digest,
                error_ref=error_ref,
                error_digest=error_digest,
                evidence_refs=tuple(dict.fromkeys((*record.evidence_refs, *evidence_refs))),
            )
            self._write_record(updated)
            return self._result(
                updated,
                action=status,
                prior_revision=record.revision,
                outcome="applied",
                occurred_at=timestamp,
            )

    def _ensure_root(self) -> None:
        if self.root.is_symlink() or (
            self.root.exists() and not self.root.is_dir()
        ):
            raise TaskStoreError("task store root must be a non-symlink directory")
        self.records_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.audit_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for path, label in (
            (self.records_root, "records"),
            (self.audit_root, "audit"),
        ):
            if path.is_symlink() or not path.is_dir():
                raise TaskStoreError(
                    f"task store {label} root must be a non-symlink directory"
                )
        os.chmod(self.root, 0o700)
        os.chmod(self.records_root, 0o700)
        os.chmod(self.audit_root, 0o700)
        if self.lock_path.is_symlink():
            raise TaskStoreError("task store lock must be a regular non-symlink file")
        try:
            fd = os.open(
                self.lock_path,
                os.O_CREAT
                | os.O_EXCL
                | os.O_WRONLY
                | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        except FileExistsError:
            pass
        else:
            os.close(fd)
        if self.lock_path.is_symlink() or not self.lock_path.is_file():
            raise TaskStoreError("task store lock must be a regular non-symlink file")
        os.chmod(self.lock_path, 0o600)

    @contextmanager
    def _locked(self, *, shared: bool = False) -> Iterator[None]:
        try:
            fd = os.open(
                self.lock_path,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            )
        except OSError as exc:
            raise TaskStoreError("task store lock cannot be opened safely") from exc
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            os.close(fd)
            raise TaskStoreError("task store lock must remain a regular file")
        with os.fdopen(fd, "rb") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_SH if shared else fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _record_path(self, task_id: str) -> Path:
        name = hashlib.sha256(task_id.encode("utf-8")).hexdigest() + ".json"
        return self.records_root / name

    def _load_record(self, task_id: str) -> OwnerTaskRecord:
        record = self._load_record_path(self._record_path(task_id))
        if not secrets.compare_digest(record.task_id, task_id):
            raise TaskStoreError("task identity digest collision")
        return record

    def _load_record_path(self, path: Path) -> OwnerTaskRecord:
        if not path.is_file() or path.is_symlink():
            raise TaskStoreError("unknown task")
        if path.stat().st_size > self.limits.maximum_record_bytes:
            raise TaskStoreError("task record exceeds the configured byte bound")
        try:
            return OwnerTaskRecord.model_validate_json(path.read_bytes())
        except (OSError, ValidationError) as exc:
            raise TaskStoreError("task record is invalid") from exc

    def _load_all_records(self) -> list[OwnerTaskRecord]:
        return [self._load_record_path(path) for path in self.records_root.glob("*.json")]

    def _write_record(self, record: OwnerTaskRecord) -> None:
        validated = OwnerTaskRecord.model_validate(record.model_dump(mode="python"))
        payload = canonical_json_bytes(validated.model_dump(mode="json")) + b"\n"
        if len(payload) > self.limits.maximum_record_bytes:
            raise TaskStoreError("task record exceeds the configured byte bound")
        self._atomic_write(self._record_path(record.task_id), payload)

    def _write_audit(self, audit: TaskAuditReceipt) -> None:
        payload = canonical_json_bytes(audit.model_dump(mode="json")) + b"\n"
        self._atomic_write(self.audit_root / f"{audit.audit_id[7:]}.json", payload)

    @staticmethod
    def _atomic_write(path: Path, payload: bytes) -> None:
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            os.chmod(path, 0o600)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass

    @staticmethod
    def _authorize(
        record: OwnerTaskRecord,
        principal_id: str,
        organ_id: str,
        contour_id: str,
    ) -> None:
        expected = (record.principal_id, record.organ_id, record.contour_id)
        observed = (principal_id, organ_id, contour_id)
        if expected != observed:
            raise TaskStoreError("task access is not authorized for this principal contour")

    @staticmethod
    def _assert_revision(record: OwnerTaskRecord, expected_revision: int) -> None:
        if record.revision != expected_revision:
            raise TaskStoreError(
                f"task CAS conflict: expected revision {expected_revision}, "
                f"observed {record.revision}"
            )

    @staticmethod
    def _require_nonterminal(record: OwnerTaskRecord) -> None:
        if record.status in TERMINAL_TASK_STATUSES:
            raise TaskStoreError("terminal task cannot transition")

    @staticmethod
    def _require_live(record: OwnerTaskRecord, now: datetime) -> None:
        if record.expires_at <= now:
            raise TaskStoreError("task TTL has expired")

    def _authorized_for_update(
        self,
        task_id: str,
        principal_id: str,
        organ_id: str,
        contour_id: str,
        expected_revision: int,
        now: datetime,
    ) -> OwnerTaskRecord:
        record = self._load_record(task_id)
        self._authorize(record, principal_id, organ_id, contour_id)
        self._assert_revision(record, expected_revision)
        self._require_live(record, now)
        return record

    @staticmethod
    def _replace(record: OwnerTaskRecord, now: datetime, **updates: Any) -> OwnerTaskRecord:
        return record.model_copy(
            update={
                "revision": record.revision + 1,
                "updated_at": now,
                **updates,
            }
        )

    def _result(
        self,
        record: OwnerTaskRecord,
        *,
        action: str,
        prior_revision: int,
        outcome: Literal["applied", "idempotent", "denied"],
        occurred_at: datetime,
    ) -> TaskMutationResult:
        record_digest = sha256_digest(record.model_dump(mode="json"))
        placeholder = TaskAuditReceipt(
            audit_id="sha256:" + "0" * 64,
            task_id_digest=sha256_digest(record.task_id),
            principal_id=record.principal_id,
            organ_id=record.organ_id,
            contour_id=record.contour_id,
            action=_audit_action(action),
            prior_revision=prior_revision,
            resulting_revision=record.revision,
            occurred_at=occurred_at,
            outcome=outcome,
            record_digest=record_digest,
        )
        audit = placeholder.model_copy(
            update={"audit_id": canonical_digest(placeholder, exclude={"audit_id"})}
        )
        self._write_audit(audit)
        return TaskMutationResult(record=record, audit=audit)


def _audit_action(
    value: str,
) -> Literal["create", "get", "apply_input", "request_cancel", "complete", "fail", "expire"]:
    aliases = {
        "require_input": "apply_input",
        "acknowledge_cancel": "request_cancel",
        "completed": "complete",
        "failed": "fail",
    }
    result = aliases.get(value, value)
    if result not in {
        "create",
        "get",
        "apply_input",
        "request_cancel",
        "complete",
        "fail",
        "expire",
    }:
        raise TaskStoreError(f"unsupported task audit action {value!r}")
    return result  # type: ignore[return-value]


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise TaskStoreError("task store timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _reject_task_secret_material(value: Any, *, context: str) -> None:
    try:
        reject_secret_material(value, context=context)
    except OrganRegistryError as exc:
        raise TaskStoreError("task payload violates secret-material policy") from exc
