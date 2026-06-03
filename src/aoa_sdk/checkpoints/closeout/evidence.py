"""Reviewed artifact and Codex trace evidence readers for checkpoint closeout."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ...loaders import load_json

CODEX_TRACE_TEXT_ITEM_TYPES = {"input_text", "output_text"}
CODEX_TRACE_MAX_CHARS = 120_000
CODEX_TRACE_MAX_CHUNK_CHARS = 3_000


def _read_reviewed_artifact(path: Path) -> dict[str, object]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FileNotFoundError(f"could not read reviewed artifact: {path}") from exc
    payload: object | None = None
    if path.suffix == ".json":
        try:
            payload = load_json(path)
        except Exception:
            payload = None
    return {
        "text": raw_text,
        "payload": payload,
        "ref": str(path),
        "tokens": set(re.findall(r"[a-z0-9_:-]+", raw_text.lower())),
    }


def _read_session_trace(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(f"missing Codex session trace: {path}")
    chunks: list[str] = []
    total_chars = 0
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        extracted = _extract_codex_trace_entry(payload)
        if extracted is None:
            continue
        normalized = re.sub(r"\s+", " ", extracted).strip()
        if not normalized:
            continue
        clipped = normalized[:CODEX_TRACE_MAX_CHUNK_CHARS]
        if total_chars + len(clipped) > CODEX_TRACE_MAX_CHARS:
            remaining = CODEX_TRACE_MAX_CHARS - total_chars
            if remaining <= 0:
                break
            clipped = clipped[:remaining]
        chunks.append(clipped)
        total_chars += len(clipped)
        if total_chars >= CODEX_TRACE_MAX_CHARS:
            break
    text = "\n".join(chunks)
    return {
        "text": text,
        "ref": str(path),
        "tokens": set(re.findall(r"[a-z0-9_:-]+", text.lower())),
    }


def _extract_codex_trace_entry(record: dict[str, object]) -> str | None:
    record_type = record.get("type")
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None
    if record_type == "event_msg" and payload.get("type") == "user_message":
        message = payload.get("message")
        return f"user: {message}" if isinstance(message, str) and message.strip() else None
    if record_type != "response_item":
        return None

    payload_type = payload.get("type")
    if payload_type == "message" and payload.get("role") == "assistant":
        text = _flatten_codex_content_text(payload.get("content"))
        return f"assistant: {text}" if text else None
    if payload_type == "function_call":
        name = payload.get("name")
        arguments = payload.get("arguments")
        parts = []
        if isinstance(name, str) and name.strip():
            parts.append(name.strip())
        if isinstance(arguments, str) and arguments.strip():
            parts.append(arguments.strip())
        return f"tool_call: {' '.join(parts)}" if parts else None
    if payload_type == "custom_tool_call":
        name = payload.get("name")
        input_value = payload.get("input")
        parts = []
        if isinstance(name, str) and name.strip():
            parts.append(name.strip())
        if isinstance(input_value, str) and input_value.strip():
            parts.append(input_value.strip())
        return f"tool_call: {' '.join(parts)}" if parts else None
    if payload_type in {"function_call_output", "custom_tool_call_output", "tool_search_output"}:
        output = payload.get("output")
        return f"tool_output: {output}" if isinstance(output, str) and output.strip() else None
    return None


def _flatten_codex_content_text(content: object) -> str:
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") not in CODEX_TRACE_TEXT_ITEM_TYPES:
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    return "\n".join(parts)


def _merge_closeout_evidence(
    *,
    primary: dict[str, object],
    secondary: dict[str, object] | None,
) -> dict[str, object]:
    if secondary is None:
        return primary
    texts = [
        text
        for text in (
            primary.get("text"),
            secondary.get("text"),
        )
        if isinstance(text, str) and text.strip()
    ]
    tokens: set[str] = set()
    for source in (primary, secondary):
        source_tokens = source.get("tokens")
        if isinstance(source_tokens, set) and all(isinstance(token, str) for token in source_tokens):
            tokens.update(source_tokens)
    refs = [
        ref
        for ref in (
            primary.get("ref"),
            secondary.get("ref"),
        )
        if isinstance(ref, str) and ref.strip()
    ]
    return {
        "text": "\n\n".join(texts),
        "payload": primary.get("payload"),
        "ref": primary.get("ref"),
        "refs": refs,
        "tokens": tokens,
    }
