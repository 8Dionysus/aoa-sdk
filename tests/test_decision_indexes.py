from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "generate_decision_indexes.py"
SPEC = importlib.util.spec_from_file_location("generate_decision_indexes", SCRIPT_PATH)
decision_indexes = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = decision_indexes
SPEC.loader.exec_module(decision_indexes)


def test_live_decision_indexes_are_current() -> None:
    assert decision_indexes.validate_decision_indexes(REPO_ROOT) == []


def test_by_number_index_exposes_canonical_id_and_path() -> None:
    records, issues = decision_indexes.collect_decision_records(REPO_ROOT)

    assert issues == []
    rendered = decision_indexes.render_index_files(records)
    by_number = rendered[decision_indexes.INDEX_DIR / "by-number.md"]

    assert "| Decision ID | Date | Decision | Path |" in by_number
    assert (
        "`docs/decisions/AOA-SDK-D-0001-decision-rationale-lane-before-mechanics.md`"
        in by_number
    )


def test_grouped_indexes_are_lookup_bullets_not_repeated_ledgers() -> None:
    records, issues = decision_indexes.collect_decision_records(REPO_ROOT)

    assert issues == []
    rendered = decision_indexes.render_index_files(records)
    by_surface = rendered[decision_indexes.INDEX_DIR / "by-surface.md"]

    assert "| Decision | Date |" not in by_surface
    assert "- [AOA-SDK-D-" in by_surface
    assert "(`docs/decisions/AOA-SDK-D-" in by_surface


def test_decision_id_must_match_filename_prefix(tmp_path: Path) -> None:
    decision_dir = tmp_path / "docs" / "decisions"
    decision_dir.mkdir(parents=True)
    decision = decision_dir / "AOA-SDK-D-0001-example.md"
    decision.write_text(
        "\n".join(
            [
                "# Example",
                "",
                "## Index Metadata",
                "",
                "- Decision ID: AOA-SDK-D-0002",
                "- Original date: 2026-05-31",
                "- Surface classes: root/topology",
                "- SDK facets: decision lane",
                "- Mechanic parents: none",
                "- Guard families: source topology",
                "- Posture: accepted",
                "",
            ]
        ),
        encoding="utf-8",
    )

    _, issues = decision_indexes.collect_decision_records(tmp_path)

    assert any("Decision ID must match filename prefix" in message for _, message in issues)
