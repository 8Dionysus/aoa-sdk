"""Visible-session replay helpers for Titan praxis.

The replay layer consumes visible Codex session exports. It must not use hidden reasoning,
encrypted payloads or compacted replacement history.
"""
from __future__ import annotations

import argparse
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TITAN_PHASE_DEFAULTS = {"Atlas": "route_frame", "Sentinel": "risk_frame", "Mneme": "provenance_frame"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _id(prefix: str) -> str:
    return f"{prefix}:{uuid.uuid4().hex}"


def parse_visible_export(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    messages = [ln for ln in lines if ln.startswith("### Message ")]
    command_rows = [ln for ln in lines if re.match(r"\|\s*\d+\s*\|", ln)]
    compactions = [ln for ln in lines if "compacted event present" in ln]
    phases: list[dict[str, Any]] = []
    phase_graph: dict[str, Any] = {
        "schema_version": "titan_phase_graph/v1",
        "phase_graph_id": _id("phase-graph"),
        "source_ref": str(path),
        "generated_at": utc_now(),
        "visible_only": True,
        "counts": {"messages": len(messages), "executed_shell_command_rows": len(command_rows), "compaction_markers": len(compactions)},
        "phases": phases,
    }
    if messages:
        phases.append({"phase_id": "phase:visible-dialogue", "kind": "visible_dialogue", "evidence_refs": ["markdown:Conversation"], "summary": f"{len(messages)} visible message headings observed."})
    if command_rows:
        phases.append({"phase_id": "phase:executed-commands", "kind": "executed_commands", "evidence_refs": ["markdown:Executed Shell Command Index"], "summary": f"{len(command_rows)} shell command index rows observed."})
    if compactions:
        phases.append({"phase_id": "phase:compaction-boundary", "kind": "compaction_boundary", "evidence_refs": ["markdown:Compaction Markers"], "summary": f"{len(compactions)} visible compaction markers observed; hidden history excluded."})
    return phase_graph


def packets_from_phase_graph(graph: dict[str, Any]) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for phase in graph.get("phases", []):
        for titan, kind in TITAN_PHASE_DEFAULTS.items():
            packets.append({"schema_version": "titan_agent_packet/v1", "packet_id": _id(f"packet:{titan.lower()}"), "phase_id": phase.get("phase_id"), "titan_name": titan, "packet_kind": kind, "source_refs": phase.get("evidence_refs", []), "summary": phase.get("summary", ""), "authority": "candidate", "created_at": utc_now()})
    return packets


def learning_deltas(graph: dict[str, Any], packets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    counts = graph.get("counts", {})
    if counts.get("compaction_markers", 0):
        deltas.append({"schema_version": "titan_learning_delta/v1", "delta_id": _id("learning"), "kind": "compaction_memory_boundary", "summary": "Replay must not infer hidden replacement history from compaction markers.", "source_refs": ["markdown:Compaction Markers"], "recommended_owner": "aoa-memo", "promotion_status": "candidate"})
    if counts.get("executed_shell_command_rows", 0):
        deltas.append({"schema_version": "titan_learning_delta/v1", "delta_id": _id("learning"), "kind": "command_trace_route", "summary": "Executed command rows can feed Atlas route variants and Sentinel failure canaries.", "source_refs": ["markdown:Executed Shell Command Index"], "recommended_owner": "aoa-playbooks", "promotion_status": "candidate"})
    return deltas


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Titan visible-session replay")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_segment = sub.add_parser("segment")
    p_segment.add_argument("--session-md", required=True)
    p_segment.add_argument("--out", required=True)
    p_packets = sub.add_parser("packets")
    p_packets.add_argument("--phase-graph", required=True)
    p_packets.add_argument("--out", required=True)
    p_lessons = sub.add_parser("lessons")
    p_lessons.add_argument("--phase-graph", required=True)
    p_lessons.add_argument("--packets", required=True)
    p_lessons.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "segment":
        write_json(Path(args.out), parse_visible_export(Path(args.session_md)))
        return 0
    if args.cmd == "packets":
        graph = json.loads(Path(args.phase_graph).read_text(encoding="utf-8"))
        write_json(Path(args.out), packets_from_phase_graph(graph))
        return 0
    if args.cmd == "lessons":
        graph = json.loads(Path(args.phase_graph).read_text(encoding="utf-8"))
        packets = json.loads(Path(args.packets).read_text(encoding="utf-8"))
        write_json(Path(args.out), learning_deltas(graph, packets))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(cli())
