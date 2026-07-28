from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


PART_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = (
    PART_ROOT / "evidence" / "routing-succession-x1-consumer-zero-candidate.json"
)
SCHEMA_PATH = (
    PART_ROOT / "schemas" / "routing-succession-x1-consumer-zero-candidate.schema.json"
)


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_evidence() -> dict[str, object]:
    evidence = load_json(EVIDENCE_PATH)
    validator = Draft202012Validator(
        load_json(SCHEMA_PATH),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(evidence), key=lambda item: list(item.path))
    assert errors == []
    return evidence


def test_x1_accounts_for_every_known_consumer_without_claiming_landing() -> None:
    evidence = load_evidence()
    accounting = evidence["consumer_accounting"]
    candidates = evidence["candidate_migrations"]
    unchanged = evidence["unchanged_classifications"]

    assert accounting == {
        "r0_registered_consumers": 16,
        "post_r0_discovered_consumers": 1,
        "total_accounted_consumers": 17,
        "candidate_migrations": 13,
        "unchanged_classifications": 4,
        "all_known_consumers_accounted": True,
    }
    assert {item["repo"] for item in candidates} == {
        "aoa-sdk",
        "abyss-stack",
        "aoa-kag",
        "aoa-stats",
        "aoa-agents",
        "aoa-evals",
        "Tree-of-Sophia",
        "aoa-playbooks",
        "Agents-of-Abyss",
        "8Dionysus",
        "aoa-techniques",
        "aoa-memo",
        "aoa-skills",
    }
    assert {item["repo"] for item in unchanged} == {
        "abyss-machine",
        "Dionysus",
        "aoa-session-memory",
        "ATM10-Agent",
    }
    assert all(item["landed"] is False for item in candidates)


def test_x1_candidate_has_zero_active_direct_checkout_dependencies() -> None:
    evidence = load_evidence()
    observed = [
        *evidence["candidate_migrations"],
        *evidence["unchanged_classifications"],
        *evidence["zero_reference_repositories"],
    ]

    assert all(
        item["direct_predecessor_checkout_dependencies"] == 0
        for item in observed
    )
    assert all(
        item["active_dependency_residuals"] == []
        for item in evidence["candidate_migrations"]
    )
    assert len(evidence["allowed_residuals"]) >= 7


def test_x1_keeps_compatibility_and_archive_stop_lines_false() -> None:
    evidence = load_evidence()
    compatibility = evidence["compatibility_exit"]
    verdict = evidence["verdict"]

    assert compatibility["completed_post_landing_validation_cycles"] == 0
    assert compatibility["required_validation_cycles"] == 2
    assert compatibility["compatibility_window_exited"] is False
    assert compatibility["rollback_retired"] is False
    assert sum(
        item["exit_satisfied"] is True
        for item in compatibility["criteria"]
    ) == 1
    assert verdict["candidate_direct_checkout_consumer_zero"] is True
    assert verdict["landed_direct_checkout_consumer_zero"] is False
    assert verdict["all_consumers_landed_green"] is False
    assert verdict["archive_ready"] is False
    assert verdict["archive_authorized"] is False


def test_x1_predecessor_remains_maintenance_only_and_operator_gated() -> None:
    predecessor = load_evidence()["predecessor_candidate"]

    assert predecessor["repo"] == "aoa-routing"
    assert predecessor["posture"] == "maintenance_only_with_rollback_retained"
    assert predecessor["landed"] is False
    assert predecessor["archive_authorized"] is False
