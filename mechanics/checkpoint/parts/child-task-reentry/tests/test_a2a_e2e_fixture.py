from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from aoa_sdk import AoASDK
from aoa_sdk.a2a.rebase import build_summon_return_checkpoint_fixture


PART_ROOT = Path(__file__).resolve().parents[1]


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "aoa_sdk"
        ).is_dir():
            return candidate
    raise RuntimeError(f"could not find aoa-sdk repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
FIXTURE_PATH = PART_ROOT / "examples" / "summon_return_checkpoint_e2e.fixture.json"
WORKSPACE_ROOT = REPO_ROOT.parent


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_e2e_fixture_is_generated_from_sdk_builder() -> None:
    assert load_fixture() == build_summon_return_checkpoint_fixture()


def test_sdk_api_exposes_e2e_fixture_builder(workspace_root: Path) -> None:
    sdk = AoASDK.from_workspace(workspace_root / "aoa-sdk")

    fixture = sdk.a2a.build_summon_return_checkpoint_fixture()

    assert fixture["fixture_id"] == "a2a-summon-return-checkpoint-e2e"
    assert fixture["reviewed_closeout_request"]["request_kind"] == "a2a_return_closeout_request"


def test_e2e_fixture_preserves_full_return_contract_chain() -> None:
    fixture = load_fixture()

    assert fixture["dry_run"] is True
    assert fixture["live_automation"] is False
    assert fixture["summon_request"]["summon_request"]["playbook_ref"] == "AOA-P-0031"
    assert fixture["summon_decision"]["lane"] == "codex_local_reviewed"
    assert fixture["codex_local_target"]["config_path"] == "/srv/AbyssOS/.codex/agents/reviewer.toml"
    assert fixture["child_task_result"]["reviewed"] is True
    assert fixture["return_plan"]["next_hop"] == "aoa-checkpoint-closeout-bridge"
    assert fixture["return_plan"]["navigation_target"] == (
        "aoa-routing/generated/return_navigation_hints.min.json"
    )
    assert fixture["checkpoint_bridge_plan"]["execution_order"] == [
        "aoa-session-donor-harvest",
        "aoa-session-progression-lift",
        "aoa-quest-harvest",
    ]
    assert fixture["memo_writeback_candidate"]["contains_raw_trace"] is False
    assert fixture["reviewed_closeout_request"]["reviewed"] is True
    assert fixture["runtime_return_closeout_receipt"]["event_kind"] == (
        "runtime_return_closeout_receipt"
    )
    assert fixture["runtime_closeout_dry_run_receipt_contract"] == {
        "artifact_kind": "aoa.runtime-a2a-return-closeout-dry-run",
        "dry_run": True,
        "live_automation": False,
        "exported_by": "scripts/aoa-a2a-return-closeout-dry-run",
        "source_payload": "reviewed_closeout_request",
    }
    assert fixture["routing_reentry"]["primary_action"] == {
        "verb": "inspect",
        "target_repo": "aoa-playbooks",
        "target_surface": "generated/playbook_registry.min.json",
        "match_field": "id",
        "target_value": "AOA-P-0031",
    }

    publishers = [item["publisher"] for item in fixture["owner_publication_plan"]]
    assert publishers == [
        "abyss-stack.runtime-return-closeouts",
        "aoa-evals.eval-result",
        "aoa-playbooks.reviewed-run",
        "aoa-memo.writeback",
    ]


def test_e2e_fixture_validates_against_live_aoa_summon_schemas() -> None:
    request_schema_path = (
        WORKSPACE_ROOT
        / "aoa-skills"
        / "skills"
        / "aoa-summon"
        / "references"
        / "summon-request-v3.schema.json"
    )
    result_schema_path = (
        WORKSPACE_ROOT
        / "aoa-skills"
        / "skills"
        / "aoa-summon"
        / "references"
        / "summon-result-v3.schema.json"
    )
    if not request_schema_path.exists() or not result_schema_path.exists():
        pytest.skip("live aoa-summon schemas are unavailable")

    fixture = load_fixture()
    request_schema = json.loads(request_schema_path.read_text(encoding="utf-8"))
    result_schema = json.loads(result_schema_path.read_text(encoding="utf-8"))

    request_errors = sorted(
        Draft202012Validator(request_schema).iter_errors(fixture["summon_request"]),
        key=lambda error: list(error.absolute_path),
    )
    result_errors = sorted(
        Draft202012Validator(result_schema).iter_errors(fixture["summon_result"]),
        key=lambda error: list(error.absolute_path),
    )

    assert request_errors == []
    assert result_errors == []
