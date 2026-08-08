"""Feature-gated MCP Tasks extension adapter over an owner TaskStore.

The adapter owns wire translation only.  It neither starts owner work nor
turns a task handle or terminal state into owner acceptance, admission, or
effect authority.
"""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal, Protocol

from ..contracts.tasks import OwnerTaskRecord, TaskInputRequest
from .registry import canonical_json_bytes, sha256_digest
from .task_store import FileTaskStore, TaskStoreError


TASKS_EXTENSION_ID = "io.modelcontextprotocol/tasks"
MCP_TASKS_PROTOCOL_VERSION = "2026-07-28"
HEADER_MISMATCH = -32020
MISSING_REQUIRED_CLIENT_CAPABILITY = -32021
INVALID_PARAMS = -32602
METHOD_NOT_FOUND = -32601
INTERNAL_ERROR = -32603
RATE_LIMITED = -32029


class MCPTasksAdapterError(ValueError):
    """A bounded JSON-RPC error produced by the Tasks adapter boundary."""

    def __init__(
        self,
        code: int,
        message: str,
        *,
        data: Mapping[str, Any] | None = None,
        http_status: int = 200,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = dict(data) if data is not None else None
        self.http_status = http_status

    def as_jsonrpc_error(self) -> dict[str, Any]:
        result: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass(frozen=True)
class MCPTaskRequestContext:
    """Authenticated request facts supplied by the transport/auth boundary."""

    principal_id: str
    organ_id: str
    contour_id: str
    protocol_version: str
    client_capabilities: Mapping[str, Any]
    transport: Literal["streamable_http", "stdio"]
    headers: Mapping[str, str]


class MCPTaskPayloadResolver(Protocol):
    """Resolve owner-issued payload refs without moving their truth into MCP."""

    def resolve_result(self, record: OwnerTaskRecord) -> Mapping[str, Any]: ...

    def resolve_error(self, record: OwnerTaskRecord) -> Mapping[str, Any]: ...

    def resolve_input_request(
        self,
        record: OwnerTaskRecord,
        request: TaskInputRequest,
    ) -> Mapping[str, Any]: ...


CancelSink = Callable[[OwnerTaskRecord], None]


class MCPTasksAdapter:
    """SEP-2663 wire adapter with an explicit disabled-by-default gate."""

    def __init__(
        self,
        store: FileTaskStore,
        payload_resolver: MCPTaskPayloadResolver,
        *,
        enabled: bool = False,
        cancel_sink: CancelSink | None = None,
        maximum_input_response_bytes: int = 64 * 1024,
        enforce_poll_interval: bool = True,
    ) -> None:
        if maximum_input_response_bytes < 1:
            raise ValueError("maximum_input_response_bytes must be positive")
        self.store = store
        self.payload_resolver = payload_resolver
        self.enabled = enabled
        self.cancel_sink = cancel_sink
        self.maximum_input_response_bytes = maximum_input_response_bytes
        self.enforce_poll_interval = enforce_poll_interval
        self._poll_lock = threading.Lock()
        self._last_poll_at: dict[str, datetime] = {}

    def server_capabilities(self) -> dict[str, Any]:
        if not self.enabled:
            return {}
        return {"extensions": {TASKS_EXTENSION_ID: {}}}

    def client_declares_extension(self, context: MCPTaskRequestContext) -> bool:
        extensions = context.client_capabilities.get("extensions")
        return isinstance(extensions, Mapping) and isinstance(
            extensions.get(TASKS_EXTENSION_ID), Mapping
        )

    def create_task_result(
        self,
        context: MCPTaskRequestContext,
        *,
        tool_name: str,
        arguments: Any,
        owner_run_ref: str,
        idempotency_key: str,
        ttl_seconds: int,
        poll_interval_ms: int,
        task_support: Literal["optional", "required"] = "optional",
        now: datetime | None = None,
    ) -> dict[str, Any] | None:
        """Durably create a task, or signal that sync fallback must be used."""

        self._require_enabled()
        self._require_protocol(context)
        self._validate_headers(context, method="tools/call", name=tool_name)
        if not self.client_declares_extension(context):
            if task_support == "optional":
                return None
            self._raise_missing_capability()
        try:
            mutation = self.store.create(
                principal_id=context.principal_id,
                organ_id=context.organ_id,
                contour_id=context.contour_id,
                tool_name=tool_name,
                arguments=arguments,
                owner_run_ref=owner_run_ref,
                idempotency_key=idempotency_key,
                ttl_seconds=ttl_seconds,
                poll_interval_ms=poll_interval_ms,
                now=now,
            )
        except TaskStoreError as exc:
            raise self._store_error(exc) from exc
        result = self._task_base(mutation.record)
        result["resultType"] = "task"
        return result

    def get_task(
        self,
        context: MCPTaskRequestContext,
        *,
        task_id: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        self._require_task_request(
            context,
            method="tasks/get",
            task_id=task_id,
        )
        record = self._get_record(context, task_id, now=now)
        self._enforce_poll_rate(context, record, now=now)
        return self._detailed_task(record)

    def update_task(
        self,
        context: MCPTaskRequestContext,
        *,
        task_id: str,
        input_responses: Mapping[str, Any],
        now: datetime | None = None,
    ) -> dict[str, Any]:
        self._require_task_request(
            context,
            method="tasks/update",
            task_id=task_id,
        )
        if not isinstance(input_responses, Mapping):
            raise MCPTasksAdapterError(INVALID_PARAMS, "inputResponses must be an object")
        if len(canonical_json_bytes(input_responses)) > self.maximum_input_response_bytes:
            raise MCPTasksAdapterError(INVALID_PARAMS, "inputResponses exceeds the byte limit")
        record = self._get_record(context, task_id, now=now)
        if record.status != "input_required":
            raise MCPTasksAdapterError(
                INVALID_PARAMS,
                "task is not waiting for input",
            )
        outstanding = {item.request_key for item in record.outstanding_inputs}
        for request_key, input_value in input_responses.items():
            if not isinstance(request_key, str):
                raise MCPTasksAdapterError(
                    INVALID_PARAMS,
                    "inputResponses keys must be strings",
                )
            if request_key not in outstanding:
                # SEP-2663 says unknown, superseded, and already fulfilled keys
                # SHOULD be ignored rather than elevated into a new write.
                continue
            input_digest = hashlib.sha256(
                canonical_json_bytes(
                    {"requestKey": request_key, "inputResponse": input_value}
                )
            ).hexdigest()
            input_key = f"mcp-{input_digest}"
            try:
                mutation = self.store.apply_input(
                    task_id,
                    principal_id=context.principal_id,
                    organ_id=context.organ_id,
                    contour_id=context.contour_id,
                    expected_revision=record.revision,
                    request_key=request_key,
                    input_key=input_key,
                    input_value=input_value,
                    now=now,
                )
            except TaskStoreError as exc:
                raise self._store_error(exc) from exc
            record = mutation.record
            outstanding.discard(request_key)
        return {"resultType": "complete"}

    def cancel_task(
        self,
        context: MCPTaskRequestContext,
        *,
        task_id: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        self._require_task_request(
            context,
            method="tasks/cancel",
            task_id=task_id,
        )
        record = self._get_record(context, task_id, now=now)
        if record.status in {"completed", "failed", "cancelled", "expired"}:
            return {"resultType": "complete"}
        try:
            mutation = self.store.request_cancel(
                task_id,
                principal_id=context.principal_id,
                organ_id=context.organ_id,
                contour_id=context.contour_id,
                expected_revision=record.revision,
                now=now,
            )
        except TaskStoreError as exc:
            # A terminal race is an idempotent acknowledgement.  Other CAS or
            # authorization failures remain explicit and fail closed.
            if "terminal task" in str(exc):
                return {"resultType": "complete"}
            raise self._store_error(exc) from exc
        if self.cancel_sink is not None:
            self.cancel_sink(mutation.record)
        return {"resultType": "complete"}

    def _detailed_task(self, record: OwnerTaskRecord) -> dict[str, Any]:
        result = self._task_base(record)
        result["resultType"] = "complete"
        if record.status == "completed":
            payload = dict(self.payload_resolver.resolve_result(record))
            self._require_payload_digest(payload, record.result_digest, "result")
            meta = payload.get("_meta")
            if isinstance(meta, Mapping) and "io.modelcontextprotocol/related-task" in meta:
                raise MCPTasksAdapterError(
                    INTERNAL_ERROR,
                    "owner result contains removed related-task metadata",
                )
            result["result"] = payload
        elif record.status == "failed":
            payload = dict(self.payload_resolver.resolve_error(record))
            self._require_payload_digest(payload, record.error_digest, "error")
            if not isinstance(payload.get("code"), int) or not isinstance(
                payload.get("message"), str
            ):
                raise MCPTasksAdapterError(
                    INTERNAL_ERROR,
                    "owner error is not a JSON-RPC error object",
                )
            result["error"] = payload
        elif record.status == "input_required":
            requests: dict[str, Any] = {}
            for request in record.outstanding_inputs:
                payload = dict(
                    self.payload_resolver.resolve_input_request(record, request)
                )
                if not isinstance(payload.get("method"), str) or not isinstance(
                    payload.get("params"), Mapping
                ):
                    raise MCPTasksAdapterError(
                        INTERNAL_ERROR,
                        "owner input request is not an MCP request object",
                    )
                requests[request.request_key] = payload
            if not requests:
                raise MCPTasksAdapterError(
                    INTERNAL_ERROR,
                    "input_required task has no resolvable input requests",
                )
            result["inputRequests"] = requests
        elif record.status == "expired":
            # `expired` is an owner-store lifecycle state, not an SEP-2663
            # wire status.  The extension permits a server to surface an
            # elapsed task as failed and subsequently delete it.
            result["status"] = "failed"
            result["error"] = {
                "code": INTERNAL_ERROR,
                "message": "Task expired before completion",
            }
        return result

    @staticmethod
    def _task_base(record: OwnerTaskRecord) -> dict[str, Any]:
        ttl_ms = int((record.expires_at - record.created_at).total_seconds() * 1000)
        return {
            "taskId": record.task_id,
            "status": record.status,
            "createdAt": _wire_time(record.created_at),
            "lastUpdatedAt": _wire_time(record.updated_at),
            "ttlMs": ttl_ms,
            "pollIntervalMs": record.poll_interval_ms,
        }

    def _get_record(
        self,
        context: MCPTaskRequestContext,
        task_id: str,
        *,
        now: datetime | None,
    ) -> OwnerTaskRecord:
        try:
            return self.store.get(
                task_id,
                principal_id=context.principal_id,
                organ_id=context.organ_id,
                contour_id=context.contour_id,
                now=now,
            )
        except TaskStoreError as exc:
            raise self._store_error(exc) from exc

    def _require_task_request(
        self,
        context: MCPTaskRequestContext,
        *,
        method: str,
        task_id: str,
    ) -> None:
        self._require_enabled()
        self._require_protocol(context)
        self._validate_headers(context, method=method, name=task_id)
        if not self.client_declares_extension(context):
            self._raise_missing_capability()

    def _enforce_poll_rate(
        self,
        context: MCPTaskRequestContext,
        record: OwnerTaskRecord,
        *,
        now: datetime | None,
    ) -> None:
        if not self.enforce_poll_interval:
            return
        timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        key_material = "\0".join(
            (
                context.principal_id,
                context.organ_id,
                context.contour_id,
                record.task_id,
            )
        )
        key = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
        with self._poll_lock:
            prior = self._last_poll_at.get(key)
            if prior is not None:
                elapsed_ms = int((timestamp - prior).total_seconds() * 1000)
                if elapsed_ms < record.poll_interval_ms:
                    raise MCPTasksAdapterError(
                        RATE_LIMITED,
                        "Task polling exceeds the advised interval",
                        data={"retryAfterMs": record.poll_interval_ms - elapsed_ms},
                        http_status=429,
                    )
            self._last_poll_at[key] = timestamp

    def _require_enabled(self) -> None:
        if not self.enabled:
            raise MCPTasksAdapterError(METHOD_NOT_FOUND, "Tasks extension is disabled")

    @staticmethod
    def _require_protocol(context: MCPTaskRequestContext) -> None:
        if context.protocol_version != MCP_TASKS_PROTOCOL_VERSION:
            raise MCPTasksAdapterError(
                INVALID_PARAMS,
                "Tasks extension requires MCP 2026-07-28",
            )

    @staticmethod
    def _validate_headers(
        context: MCPTaskRequestContext,
        *,
        method: str,
        name: str,
    ) -> None:
        if context.transport != "streamable_http":
            return
        headers = {key.lower(): value for key, value in context.headers.items()}
        if headers.get("mcp-method") != method or headers.get("mcp-name") != name:
            raise MCPTasksAdapterError(
                HEADER_MISMATCH,
                "MCP routing headers do not match the JSON-RPC request",
                http_status=400,
            )

    @staticmethod
    def _raise_missing_capability() -> None:
        raise MCPTasksAdapterError(
            MISSING_REQUIRED_CLIENT_CAPABILITY,
            "Missing required client capability",
            data={
                "requiredCapabilities": {
                    "extensions": {TASKS_EXTENSION_ID: {}}
                }
            },
        )

    @staticmethod
    def _store_error(error: TaskStoreError) -> MCPTasksAdapterError:
        message = str(error)
        if "unknown task" in message or "not authorized" in message:
            # Deliberately collapse absence and authorization denial to prevent
            # task enumeration across principals or contours.
            return MCPTasksAdapterError(INVALID_PARAMS, "Unknown task")
        if (
            "quota" in message
            or "byte bound" in message
            or "TTL" in message
            or "secret-material policy" in message
        ):
            return MCPTasksAdapterError(INVALID_PARAMS, "Task request exceeds policy")
        if "CAS conflict" in message:
            return MCPTasksAdapterError(INVALID_PARAMS, "Task revision conflict")
        return MCPTasksAdapterError(INTERNAL_ERROR, "Task store operation failed")

    @staticmethod
    def _require_payload_digest(
        payload: Mapping[str, Any],
        expected: str | None,
        label: str,
    ) -> None:
        if expected is None or sha256_digest(payload) != expected:
            raise MCPTasksAdapterError(
                INTERNAL_ERROR,
                f"owner {label} digest does not match the task record",
            )


def _wire_time(value: datetime) -> str:
    timestamp = value.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    return timestamp.removesuffix("+00:00") + "Z"
