from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

TITANS = {
    "Atlas": {"role": "architect", "lane": "structure", "gate": "none"},
    "Sentinel": {"role": "reviewer", "lane": "risk", "gate": "none"},
    "Mneme": {"role": "memory-keeper", "lane": "memory", "gate": "none"},
    "Forge": {"role": "coder", "lane": "implementation", "gate": "mutation"},
    "Delta": {"role": "evaluator", "lane": "verdict", "gate": "judgment"},
}

DEFAULT_POLICY = {
    "authority": "candidate_only",
    "retention": "operator_controlled",
    "redaction_modes": ["mask", "tombstone"],
    "default_confidence": 0.45,
    "stronger_than_recall": [
        "operator_instruction",
        "owner_repo_source",
        "wave_manifest_or_source_seed",
        "reviewed_receipt_or_planting_report",
    ],
}


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def stable_id(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()[:16]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def split_tags(raw: str | None) -> List[str]:
    if not raw:
        return []
    out = []
    for part in re.split(r"[,\s]+", raw.strip()):
        if part:
            out.append(part)
    return sorted(set(out))


def new_index(workspace: str, operator: str) -> Dict[str, Any]:
    now = utc_now()
    return {
        "version": 0,
        "kind": "titan_memory_index",
        "wave": "fourteenth_wave",
        "created_at": now,
        "updated_at": now,
        "workspace": workspace,
        "operator": operator,
        "authority": "candidate_only",
        "policy": DEFAULT_POLICY,
        "titans": TITANS,
        "records": [],
        "redactions": [],
        "digests": [],
        "status": "open",
    }


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def make_record(
    *,
    titan: str,
    kind: str,
    text: str,
    source_kind: str,
    session_id: str | None = None,
    source_ref: str | None = None,
    tags: List[str] | None = None,
    confidence: float | None = None,
    authority_note: str = "candidate_only",
    lineage: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    if titan not in TITANS:
        raise ValueError(f"unknown titan: {titan}")
    text = normalize_text(text)
    now = utc_now()
    rid = stable_id(
        titan, kind, text, source_kind, session_id or "", source_ref or "", now
    )
    return {
        "record_id": rid,
        "created_at": now,
        "updated_at": now,
        "status": "candidate",
        "titan": titan,
        "role": TITANS[titan]["role"],
        "lane": TITANS[titan]["lane"],
        "kind": kind,
        "text": text,
        "source_kind": source_kind,
        "source_ref": source_ref,
        "session_id": session_id,
        "tags": sorted(set(tags or [])),
        "confidence": confidence
        if confidence is not None
        else DEFAULT_POLICY["default_confidence"],
        "authority_note": authority_note,
        "lineage": lineage or {},
    }


def add_record(index: Dict[str, Any], record: Dict[str, Any]) -> Dict[str, Any]:
    index.setdefault("records", []).append(record)
    index["updated_at"] = utc_now()
    return index


def ingest_receipt(
    index: Dict[str, Any],
    receipt_path: Path,
    source_kind: str,
    summary: str | None,
    tags: List[str],
) -> Dict[str, Any]:
    data = load_json(receipt_path)
    session_id = str(
        data.get("session_id")
        or data.get("id")
        or data.get("thread_id")
        or receipt_path.stem
    )
    text_bits = []
    if summary:
        text_bits.append(summary)
    for key in (
        "summary",
        "final_summary",
        "closure_summary",
        "operator_note",
        "title",
    ):
        if data.get(key):
            text_bits.append(normalize_text(data[key]))
    if not text_bits:
        text_bits.append(f"Ingested receipt {receipt_path.name}")
    titan = "Mneme"
    if isinstance(data.get("titan"), str) and data["titan"] in TITANS:
        titan = data["titan"]
    record = make_record(
        titan=titan,
        kind="receipt_ingest",
        text="\n".join(text_bits),
        source_kind=source_kind,
        session_id=session_id,
        source_ref=str(receipt_path),
        tags=tags + ["receipt", source_kind],
        lineage={"receipt_keys": sorted(data.keys())[:40]},
    )
    return add_record(index, record)


def recall(
    index: Dict[str, Any],
    query: str,
    titan: str | None = None,
    tag: str | None = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    words = [w.lower() for w in re.findall(r"[\w\-]+", query or "")]
    results = []
    for rec in index.get("records", []):
        if rec.get("status") == "tombstone":
            continue
        if titan and rec.get("titan") != titan:
            continue
        if tag and tag not in rec.get("tags", []):
            continue
        hay = " ".join(
            [
                rec.get("text", ""),
                rec.get("kind", ""),
                rec.get("source_kind", ""),
                " ".join(rec.get("tags", [])),
            ]
        ).lower()
        score = sum(1 for w in words if w in hay)
        if not words:
            score = 1
        if score > 0:
            item = dict(rec)
            item["recall_score"] = score + float(rec.get("confidence", 0))
            item["recall_authority_warning"] = (
                "candidate recall; verify owner-repo or source seed before treating as truth"
            )
            results.append(item)
    results.sort(
        key=lambda r: (r.get("recall_score", 0), r.get("created_at", "")), reverse=True
    )
    return results[:limit]


def redact(
    index: Dict[str, Any], record_id: str, mode: str, reason: str
) -> Dict[str, Any]:
    if mode not in {"mask", "tombstone"}:
        raise ValueError("mode must be mask or tombstone")
    for rec in index.get("records", []):
        if rec.get("record_id") == record_id:
            before_status = rec.get("status")
            if mode == "mask":
                rec["text"] = "[REDACTED]"
                rec["status"] = "redacted"
            else:
                rec["text"] = "[TOMBSTONED]"
                rec["status"] = "tombstone"
            rec["updated_at"] = utc_now()
            tomb = {
                "record_id": record_id,
                "mode": mode,
                "reason": reason,
                "created_at": utc_now(),
                "previous_status": before_status,
            }
            index.setdefault("redactions", []).append(tomb)
            index["updated_at"] = utc_now()
            return index
    raise ValueError(f"record not found: {record_id}")


def digest(index: Dict[str, Any]) -> Dict[str, Any]:
    records = index.get("records", [])
    active = [r for r in records if r.get("status") not in {"tombstone"}]
    by_titan: Dict[str, int] = {name: 0 for name in TITANS}
    by_kind: Dict[str, int] = {}
    tags: Dict[str, int] = {}
    for rec in active:
        by_titan[rec.get("titan", "?")] = by_titan.get(rec.get("titan", "?"), 0) + 1
        by_kind[rec.get("kind", "?")] = by_kind.get(rec.get("kind", "?"), 0) + 1
        for tag in rec.get("tags", []):
            tags[tag] = tags.get(tag, 0) + 1
    recent = sorted(active, key=lambda r: r.get("created_at", ""), reverse=True)[:5]
    d = {
        "digest_id": stable_id(
            index.get("workspace", ""), index.get("updated_at", ""), str(len(records))
        ),
        "created_at": utc_now(),
        "authority": "derived_digest",
        "record_count": len(records),
        "active_record_count": len(active),
        "redaction_count": len(index.get("redactions", [])),
        "by_titan": by_titan,
        "by_kind": by_kind,
        "top_tags": sorted(tags.items(), key=lambda kv: kv[1], reverse=True)[:10],
        "recent_records": [
            {
                k: r.get(k)
                for k in (
                    "record_id",
                    "created_at",
                    "titan",
                    "kind",
                    "text",
                    "authority_note",
                )
            }
            for r in recent
        ],
        "warning": "Digest is a derived memory surface, not owner-repo truth.",
    }
    index.setdefault("digests", []).append(d)
    index["updated_at"] = utc_now()
    return d


def validate_index(index: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if index.get("kind") != "titan_memory_index":
        errors.append("kind must be titan_memory_index")
    if index.get("authority") != "candidate_only":
        errors.append("authority must be candidate_only")
    seen = set()
    for rec in index.get("records", []):
        rid = rec.get("record_id")
        if not rid:
            errors.append("record missing record_id")
        elif rid in seen:
            errors.append(f"duplicate record_id: {rid}")
        seen.add(rid)
        if rec.get("titan") not in TITANS:
            errors.append(f"unknown titan in record {rid}: {rec.get('titan')}")
        if not rec.get("authority_note"):
            errors.append(f"record missing authority_note: {rid}")
        if rec.get("titan") == "Forge" and rec.get("lineage", {}).get("gate") not in (
            None,
            "mutation",
        ):
            errors.append(f"Forge record has wrong gate: {rid}")
        if rec.get("titan") == "Delta" and rec.get("lineage", {}).get("gate") not in (
            None,
            "judgment",
        ):
            errors.append(f"Delta record has wrong gate: {rid}")
    return errors


def cmd_init(args: argparse.Namespace) -> int:
    data = new_index(args.workspace, args.operator)
    save_json(Path(args.out), data)
    print(args.out)
    return 0


def cmd_event(args: argparse.Namespace) -> int:
    path = Path(args.index)
    idx = load_json(path)
    lineage = {}
    if args.gate:
        expected = TITANS[args.titan]["gate"]
        if expected != "none" and args.gate != expected:
            raise SystemExit(f"{args.titan} requires gate {expected}, got {args.gate}")
        lineage["gate"] = args.gate
    record = make_record(
        titan=args.titan,
        kind=args.kind,
        text=args.text,
        source_kind="manual_event",
        session_id=args.session_id,
        source_ref=args.source_ref,
        tags=split_tags(args.tags),
        confidence=args.confidence,
        authority_note=args.authority_note,
        lineage=lineage,
    )
    add_record(idx, record)
    save_json(path, idx)
    print(record["record_id"])
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    path = Path(args.index)
    idx = load_json(path)
    ingest_receipt(
        idx, Path(args.receipt), args.source_kind, args.summary, split_tags(args.tags)
    )
    save_json(path, idx)
    print("ingested")
    return 0


def cmd_recall(args: argparse.Namespace) -> int:
    idx = load_json(Path(args.index))
    results = recall(idx, args.query, args.titan, args.tag, args.limit)
    print(
        json.dumps(
            {"query": args.query, "results": results, "authority": "candidate_only"},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_redact(args: argparse.Namespace) -> int:
    path = Path(args.index)
    idx = load_json(path)
    redact(idx, args.record_id, args.mode, args.reason)
    save_json(path, idx)
    print("redacted")
    return 0


def cmd_digest(args: argparse.Namespace) -> int:
    path = Path(args.index)
    idx = load_json(path)
    d = digest(idx)
    save_json(path, idx)
    if args.out:
        save_json(Path(args.out), d)
    print(json.dumps(d, indent=2, ensure_ascii=False))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    idx = load_json(Path(args.index))
    errors = validate_index(idx)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2, ensure_ascii=False))
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "records": len(idx.get("records", [])),
                "status": idx.get("status"),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_close(args: argparse.Namespace) -> int:
    path = Path(args.index)
    idx = load_json(path)
    idx["status"] = "closed"
    idx["closed_at"] = utc_now()
    idx["closure_note"] = args.note
    idx["updated_at"] = utc_now()
    save_json(path, idx)
    print("closed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Titan Memory Loom CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("init")
    sp.add_argument("--workspace", required=True)
    sp.add_argument("--operator", default="Dionysus")
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("event")
    sp.add_argument("--index", required=True)
    sp.add_argument("--titan", required=True, choices=sorted(TITANS))
    sp.add_argument("--kind", required=True)
    sp.add_argument("--text", required=True)
    sp.add_argument("--session-id")
    sp.add_argument("--source-ref")
    sp.add_argument("--tags")
    sp.add_argument("--confidence", type=float)
    sp.add_argument("--authority-note", default="candidate_only")
    sp.add_argument("--gate")
    sp.set_defaults(func=cmd_event)

    sp = sub.add_parser("ingest")
    sp.add_argument("--index", required=True)
    sp.add_argument("--receipt", required=True)
    sp.add_argument("--source-kind", default="receipt")
    sp.add_argument("--summary")
    sp.add_argument("--tags")
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("recall")
    sp.add_argument("--index", required=True)
    sp.add_argument("--query", required=True)
    sp.add_argument("--titan")
    sp.add_argument("--tag")
    sp.add_argument("--limit", type=int, default=10)
    sp.set_defaults(func=cmd_recall)

    sp = sub.add_parser("redact")
    sp.add_argument("--index", required=True)
    sp.add_argument("--record-id", required=True)
    sp.add_argument("--mode", choices=["mask", "tombstone"], default="mask")
    sp.add_argument("--reason", required=True)
    sp.set_defaults(func=cmd_redact)

    sp = sub.add_parser("digest")
    sp.add_argument("--index", required=True)
    sp.add_argument("--out")
    sp.set_defaults(func=cmd_digest)

    sp = sub.add_parser("validate")
    sp.add_argument("--index", required=True)
    sp.set_defaults(func=cmd_validate)

    sp = sub.add_parser("close")
    sp.add_argument("--index", required=True)
    sp.add_argument("--note", default="Memory Loom closed by operator.")
    sp.set_defaults(func=cmd_close)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
