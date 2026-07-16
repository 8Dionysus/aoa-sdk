from __future__ import annotations

import json
from pathlib import Path

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


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_e2e_fixture_is_generated_from_sdk_builder() -> None:
    assert load_fixture() == build_summon_return_checkpoint_fixture()


def test_e2e_fixture_preserves_reviewed_owner_handoff_chain() -> None:
    fixture = load_fixture()

    assert fixture["dry_run"] is True
    assert fixture["live_automation"] is False
    assert fixture["capability_execution_claimed"] is False
    assert fixture["summon_request"]["summon_request"]["capability_refs"] == [
        "workflow.operations.delegation",
        "workflow.operations.checkpoint-closeout",
    ]
    assert fixture["summon_result"]["capability_execution_claimed"] is False
    assert fixture["return_plan"]["next_hop"] == (
        "workflow.operations.checkpoint-closeout"
    )
    assert fixture["checkpoint_handoff_plan"]["capability_execution_claimed"] is False
    assert fixture["checkpoint_evidence_bundle"]["capability_candidates"] == [
        "workflow.operations.checkpoint-closeout"
    ]
    assert fixture["reviewed_return_handoff"]["request_kind"] == (
        "a2a_return_evidence_handoff"
    )
    assert fixture["runtime_return_closeout_receipt"]["payload"][
        "capability_execution_claimed"
    ] is False
    assert fixture["runtime_closeout_dry_run_receipt_contract"]["source_payload"] == (
        "reviewed_return_handoff"
    )
    assert {item["owner_ref"] for item in fixture["owner_handoffs"]} == {
        "repo:abyss-stack",
        "repo:aoa-evals",
        "repo:aoa-memo",
        "repo:aoa-playbooks",
    }


def test_e2e_fixture_validates_against_sdk_owned_transport_schemas(
    monkeypatch,
) -> None:
    monkeypatch.setenv("AOA_SDK_REPO_PATH_AOA_SDK", str(REPO_ROOT))
    sdk = AoASDK.from_workspace(REPO_ROOT)
    fixture = load_fixture()

    request_errors = list(
        Draft202012Validator(sdk.a2a.summon_request_schema()).iter_errors(
            fixture["summon_request"]
        )
    )
    result_errors = list(
        Draft202012Validator(sdk.a2a.summon_result_schema()).iter_errors(
            fixture["summon_result"]
        )
    )

    assert request_errors == []
    assert result_errors == []
