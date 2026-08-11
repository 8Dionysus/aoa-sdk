from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path

import importlib.util

import pytest
import yaml

from evals.suites.test_agent_os_control_plane_g11 import CASES
from scripts import release_check


REPO_ROOT = Path(__file__).resolve().parents[5]
RUNNER_PATH = (
    REPO_ROOT
    / "mechanics"
    / "release-support"
    / "parts"
    / "validation-evidence-graph"
    / "scripts"
    / "validation_graph.py"
)
MANIFEST_PATH = RUNNER_PATH.parents[1] / "config" / "validation_graph.json"
SPEC = importlib.util.spec_from_file_location("aoa_sdk_validation_graph", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
validation_graph = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validation_graph)


def load_manifest() -> dict[str, object]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def minimal_manifest(*, failing: bool = False) -> dict[str, object]:
    exit_code = "3" if failing else "0"
    return {
        "schema_version": validation_graph.SCHEMA_VERSION,
        "graph_id": "test-graph",
        "owner_repo": "aoa-sdk",
        "default_profile": "full",
        "unknown_change_policy": "full",
        "routing_status": "shadow_only",
        "instant_budget_seconds": 1.0,
        "max_workers": 2,
        "claims": [
            {
                "id": "graph",
                "risk": "test graph drift",
                "required_evidence": ["graph-valid"],
            },
            {
                "id": "work",
                "risk": "test work drift",
                "required_evidence": ["work-a", "work-b"],
            },
        ],
        "profiles": {"instant": ["graph"], "full": ["graph", "work"]},
        "routes": [
            {"id": "known", "patterns": ["known/**"], "claims": ["work"]}
        ],
        "nodes": [
            {
                "id": "graph",
                "tier": "instant",
                "priority": 100,
                "depends_on": [],
                "provides_evidence": ["graph-valid"],
                "timeout_seconds": 5,
                "inputs": [
                    "mechanics/release-support/parts/validation-evidence-graph/"
                    "scripts/validation_graph.py"
                ],
                "steps": [
                    {
                        "id": "graph",
                        "argv": ["{python}", "-c", f"raise SystemExit({exit_code})"],
                    }
                ],
            },
            {
                "id": "work-a",
                "tier": "contextual",
                "priority": 50,
                "depends_on": ["graph"],
                "provides_evidence": ["work-a"],
                "timeout_seconds": 5,
                "inputs": ["src/**"],
                "steps": [
                    {
                        "id": "work-a",
                        "argv": ["{python}", "-c", "import time; time.sleep(0.25)"],
                    }
                ],
            },
            {
                "id": "work-b",
                "tier": "contextual",
                "priority": 50,
                "depends_on": ["graph"],
                "provides_evidence": ["work-b"],
                "timeout_seconds": 5,
                "inputs": ["tests/**"],
                "steps": [
                    {
                        "id": "work-b",
                        "argv": ["{python}", "-c", "import time; time.sleep(0.25)"],
                    }
                ],
            },
        ],
    }


def normalized(command: list[str]) -> list[str]:
    return ["{python}" if token == sys.executable else token for token in command]


def graph_commands(manifest: dict[str, object]) -> list[list[str]]:
    nodes = manifest["nodes"]
    assert isinstance(nodes, list)
    return [step["argv"] for node in nodes for step in node["steps"]]


def workflow_steps(relative_path: str, job_id: str) -> dict[str, dict[str, object]]:
    payload = yaml.safe_load((REPO_ROOT / relative_path).read_text(encoding="utf-8"))
    steps = payload["jobs"][job_id]["steps"]
    return {step["name"]: step for step in steps}


def test_shipped_manifest_is_fail_closed_and_full_profile_is_complete() -> None:
    manifest = validation_graph.load_manifest(MANIFEST_PATH)
    full_claims, route = validation_graph.select_claims(
        manifest, profile="full", changed_paths=[], shadow_route=False
    )
    activated = validation_graph.activate_nodes(manifest, full_claims)

    assert route["authoritative"] is True
    assert full_claims == manifest["profiles"]["full"]
    assert activated == [node["id"] for node in manifest["nodes"]]


def test_full_graph_preserves_every_non_pytest_release_check_command() -> None:
    manifest = validation_graph.load_manifest(MANIFEST_PATH)
    commands = graph_commands(manifest)

    for label, command in release_check.COMMANDS:
        if label == "run tests":
            continue
        assert commands.count(normalized(command)) == 1, label


def test_shadow_workflow_matches_serial_setup_and_explicit_prerequisites() -> None:
    serial = workflow_steps(".github/workflows/repo-validation.yml", "release_audit")
    shadow = workflow_steps(
        ".github/workflows/validation-evidence-shadow.yml",
        "validation_evidence_shadow",
    )
    common_steps = (
        "Checkout",
        "Check repo-local KAG index family",
        "Fetch routing succession evidence history",
        "Checkout aoa-stats validator",
        "Checkout abyss-machine verifier",
        "Setup Python",
        "Install dependencies",
        "Check routing succession G4 evidence",
    )

    for name in common_steps:
        assert shadow[name] == serial[name]


def test_g11_shards_cover_every_exact_case_once_and_keep_ordinary_suite_separate() -> None:
    manifest = validation_graph.load_manifest(MANIFEST_PATH)
    commands = graph_commands(manifest)
    wrapper_prefix = "evals/suites/test_agent_os_control_plane_g11.py::test_g11_case["
    selected = [
        token.removeprefix(wrapper_prefix).removesuffix("]")
        for command in commands
        for token in command
        if token.startswith(wrapper_prefix)
    ]
    expected = [case_id for case_id, _ in CASES]

    assert sorted(selected) == sorted(expected)
    assert len(selected) == len(set(selected)) == len(expected)
    ordinary = next(node for node in manifest["nodes"] if node["id"] == "ordinary-tests")
    assert "--ignore=evals/suites/test_agent_os_control_plane_g11.py" in ordinary["steps"][0]["argv"]


def test_unknown_changed_path_falls_back_to_the_full_claim_set() -> None:
    manifest = validation_graph.load_manifest(MANIFEST_PATH)
    claims, route = validation_graph.select_claims(
        manifest,
        profile=None,
        changed_paths=["unowned/new-surface.txt"],
        shadow_route=True,
    )

    assert claims == manifest["profiles"]["full"]
    assert route["fallback_to_full"] is True
    assert route["authoritative"] is False


def test_known_shadow_route_is_bounded_but_never_authoritative() -> None:
    manifest = validation_graph.load_manifest(MANIFEST_PATH)
    claims, route = validation_graph.select_claims(
        manifest,
        profile=None,
        changed_paths=["docs/RELEASING.md"],
        shadow_route=True,
    )

    assert set(claims) < set(manifest["profiles"]["full"])
    assert "validation-graph-integrity" in claims
    assert route["fallback_to_full"] is False
    assert route["authoritative"] is False


@pytest.mark.parametrize("mutation", ["duplicate-node", "evidence-collision", "cycle"])
def test_manifest_rejects_identity_collisions_and_cycles(mutation: str) -> None:
    manifest = minimal_manifest()
    nodes = manifest["nodes"]
    assert isinstance(nodes, list)
    if mutation == "duplicate-node":
        duplicate = copy.deepcopy(nodes[-1])
        duplicate["provides_evidence"] = ["work-c"]
        manifest["claims"][1]["required_evidence"].append("work-c")
        nodes.append(duplicate)
    elif mutation == "evidence-collision":
        nodes[-1]["provides_evidence"] = ["work-a"]
    else:
        nodes[0]["depends_on"] = ["work-a"]

    with pytest.raises(validation_graph.ManifestError):
        validation_graph.validate_manifest(manifest)


def test_scheduler_runs_independent_nodes_concurrently_and_fans_in_in_manifest_order() -> None:
    manifest = minimal_manifest()
    validation_graph.validate_manifest(manifest)
    activated = validation_graph.activate_nodes(manifest, manifest["profiles"]["full"])
    started = time.monotonic()
    results = validation_graph.execute_nodes(
        manifest,
        activated,
        repo_root=REPO_ROOT,
        max_workers=2,
        announce=False,
    )
    elapsed = time.monotonic() - started

    assert elapsed < 0.5
    assert [result["id"] for result in results] == activated
    assert {result["status"] for result in results} == {"passed"}


def test_failed_evidence_node_yields_a_bound_insufficient_receipt(tmp_path: Path) -> None:
    manifest = minimal_manifest(failing=True)
    manifest_path = tmp_path / "graph.json"
    receipt_path = tmp_path / "receipt.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    exit_code = validation_graph.main(
        [
            "--manifest",
            str(manifest_path),
            "--profile",
            "full",
            "--receipt",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["decision"]["sufficient"] is False
    assert receipt["decision"]["authoritative_for_owner_gate"] is True
    assert receipt["evidence"]["missing"] == ["graph-valid", "work-a", "work-b"]
    assert receipt["node_results"][0]["status"] == "failed"
    assert {result["status"] for result in receipt["node_results"][1:]} == {
        "blocked_dependency"
    }


def test_changed_paths_require_explicit_shadow_mode() -> None:
    manifest = validation_graph.load_manifest(MANIFEST_PATH)
    with pytest.raises(validation_graph.ManifestError, match="shadow"):
        validation_graph.select_claims(
            manifest,
            profile="full",
            changed_paths=["README.md"],
            shadow_route=False,
        )


def test_input_identity_changes_with_exact_file_content(tmp_path: Path) -> None:
    source = tmp_path / "src" / "package" / "example.py"
    source.parent.mkdir(parents=True)
    source.write_text("value = 1\n", encoding="utf-8")
    before = validation_graph.input_identity(tmp_path, ["src/**"])
    source.write_text("value = 2\n", encoding="utf-8")
    after = validation_graph.input_identity(tmp_path, ["src/**"])

    assert before["file_count"] == after["file_count"] == 1
    assert before["sha256"] != after["sha256"]


def test_recursive_route_patterns_cover_arbitrary_depth() -> None:
    assert validation_graph._matches("src/aoa_sdk/control_plane/core.py", "src/**")
    assert validation_graph._matches("src", "src/**")
    assert not validation_graph._matches("tests/test_core.py", "src/**")


def test_timeout_is_a_hard_failure_and_kills_the_child_group() -> None:
    result = validation_graph._run_step(
        {
            "id": "timeout",
            "argv": ["{python}", "-c", "import time; time.sleep(5)"],
        },
        repo_root=REPO_ROOT,
        timeout_seconds=0.05,
    )

    assert result["status"] == "timed_out"
    assert result["timed_out"] is True
    assert result["duration_seconds"] < 1


def test_repository_drift_blocks_an_otherwise_green_receipt(tmp_path: Path) -> None:
    manifest = minimal_manifest()
    manifest_path = tmp_path / "graph.json"
    manifest_bytes = json.dumps(manifest).encode()
    manifest_path.write_bytes(manifest_bytes)
    claims = manifest["profiles"]["full"]
    activated = validation_graph.activate_nodes(manifest, claims)
    node_results = [
        {
            "id": node["id"],
            "tier": node["tier"],
            "status": "passed",
            "duration_seconds": 0.01,
            "input_identity": {
                "patterns": node["inputs"],
                "file_count": 1,
                "sha256": "0" * 64,
                "unreadable": [],
            },
            "provides_evidence": node["provides_evidence"],
            "steps": [],
        }
        for node in manifest["nodes"]
    ]
    initial_identity = validation_graph.repository_identity(REPO_ROOT)
    initial_identity["git_commit"] = "tampered"
    receipt = validation_graph.build_receipt(
        manifest,
        manifest_path=manifest_path,
        claims=claims,
        activated=activated,
        route={"mode": "profile", "authoritative": True},
        node_results=node_results,
        repo_root=REPO_ROOT,
        max_workers=2,
        started_at=dt.datetime.now(dt.UTC),
        elapsed_seconds=0.1,
        initial_repository_identity=initial_identity,
        initial_manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        initial_environment_identity=validation_graph.environment_identity(),
    )

    assert receipt["evidence"]["missing"] == []
    assert receipt["decision"]["sufficient"] is False
    assert receipt["decision"]["integrity_blockers"] == [
        "repository_identity_changed_during_run"
    ]
