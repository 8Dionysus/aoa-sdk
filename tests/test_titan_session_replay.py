from __future__ import annotations

from pathlib import Path

from aoa_sdk.titans.session_replay import learning_deltas, packets_from_phase_graph, parse_visible_export


def test_visible_export_replay_produces_phase_graph(tmp_path: Path):
    md = tmp_path / "session.md"
    md.write_text("# Current Codex Session Visible Export\n## Compaction Markers\n- line `1`: compacted event present; hidden replacement history omitted.\n## Conversation\n### Message 1: user / user\n## Executed Shell Command Index\n| 1 | `2026` | `0` | `/srv` | `echo hi` |\n", encoding="utf-8")
    graph = parse_visible_export(md)
    assert graph["visible_only"] is True
    assert graph["counts"]["messages"] == 1
    packets = packets_from_phase_graph(graph)
    assert {p["titan_name"] for p in packets} >= {"Atlas", "Sentinel", "Mneme"}
    deltas = learning_deltas(graph, packets)
    assert any(d["kind"] == "compaction_memory_boundary" for d in deltas)
