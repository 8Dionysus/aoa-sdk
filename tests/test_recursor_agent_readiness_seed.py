from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aoa_sdk.recurrence.agent_readiness import (  # noqa: E402
    build_recursor_boundary_scan_report,
    build_recursor_projection_candidates,
    build_recursor_readiness_projection,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def seed_workspace(root: Path) -> Path:
    workspace = root / "workspace"
    config = workspace / "aoa-agents" / "config"
    global_forbidden = [
        "spawn_agent",
        "open_arena_session",
        "issue_verdict",
        "write_scar",
        "mutate_rank",
        "promote_to_tree_of_sophia",
        "hidden_scheduler_action",
    ]
    write_json(
        config / "recursor_roles.seed.json",
        {
            "roles": [
                {
                    "schema_version": "recursor-role-contract/v1",
                    "recursor_id": "recursor.witness",
                    "owner_repo": "aoa-agents",
                    "readiness_status": "candidate",
                    "default_form": {
                        "kind": "assistant",
                        "base_role_gravity": ["reviewer.assistant"],
                        "service_offices": ["monitor"],
                        "arena_eligible": False,
                    },
                    "future_agonic_candidate": {
                        "enabled": False,
                        "candidate_seats": ["witness"],
                        "live_authority": False,
                    },
                    "allowed_inputs": ["change_signal", "boundary_scan_report"],
                    "allowed_outputs": [
                        "recursor_handoff_ledger",
                        "boundary_gap_note",
                    ],
                    "forbidden_actions": [
                        *global_forbidden,
                        "apply_patch",
                        "close_review_decision",
                    ],
                    "memory_policy": {
                        "direct_durable_write_allowed": False,
                        "may_prepare_memo_candidate": True,
                        "memo_owner_repo": "aoa-memo",
                    },
                    "codex_projection": {
                        "status": "candidate_only",
                        "install_by_default": False,
                        "requires_owner_review": True,
                    },
                    "receipts_required": True,
                    "stop_lines": [
                        "readiness_is_not_runtime",
                        "witness_is_not_scar_owner",
                        "assistant_is_not_contestant",
                        "projection_candidate_is_not_install",
                        "no_hidden_scheduler",
                    ],
                },
                {
                    "schema_version": "recursor-role-contract/v1",
                    "recursor_id": "recursor.executor",
                    "owner_repo": "aoa-agents",
                    "readiness_status": "candidate",
                    "default_form": {
                        "kind": "assistant",
                        "base_role_gravity": ["coder.assistant"],
                        "service_offices": ["notary"],
                        "arena_eligible": False,
                    },
                    "future_agonic_candidate": {
                        "enabled": False,
                        "candidate_seats": ["executor"],
                        "live_authority": False,
                    },
                    "allowed_inputs": ["approved_propagation_plan", "witness_preflight"],
                    "allowed_outputs": [
                        "execution_receipt",
                        "patch_summary",
                    ],
                    "forbidden_actions": [
                        *global_forbidden,
                        "execute_without_approved_plan",
                        "self_verify_final_truth",
                    ],
                    "memory_policy": {
                        "direct_durable_write_allowed": False,
                        "may_prepare_memo_candidate": False,
                        "memo_owner_repo": "aoa-memo",
                    },
                    "codex_projection": {
                        "status": "candidate_only",
                        "install_by_default": False,
                        "requires_owner_review": True,
                    },
                    "receipts_required": True,
                    "stop_lines": [
                        "readiness_is_not_runtime",
                        "executor_requires_approved_plan",
                        "executor_is_not_self_verifier",
                        "assistant_is_not_contestant",
                        "projection_candidate_is_not_install",
                        "no_hidden_scheduler",
                    ],
                },
            ]
        },
    )
    write_json(
        config / "recursor_pair.seed.json",
        {
            "schema_version": "recursor-pair-contract/v1",
            "pair_ref": "recursor_pair:witness_executor:v1",
            "roles": {
                "witness": "recursor.witness",
                "executor": "recursor.executor",
            },
            "required_separation": [
                "witness_cannot_apply_mutations",
                "executor_cannot_close_review",
                "executor_cannot_self_verify_without_external_check",
                "neither_can_spawn_additional_agents",
                "neither_can_open_arena",
                "owner_decisions_outrank_recursor_pair",
                "main_codex_or_human_keeps_supervisory_lane",
            ],
            "handoff_order": [
                "witness_preflight",
                "executor_bounded_work",
                "witness_trace_check",
                "owner_or_main_codex_review",
            ],
            "activation_status": "readiness_only",
        },
    )
    write_json(
        config / "codex_recursor_projection.candidate.json",
        {
            "projection_status": "candidate_only",
            "install_by_default": False,
            "requires_owner_review": True,
            "candidate_agents": [
                {
                    "recursor_id": "recursor.witness",
                    "activation_status": "candidate_only",
                    "activation_requires": [
                        "explicit_main_codex_call",
                        "no_agonic_runtime_claim",
                    ],
                    "forbidden": [
                        "workspace_write",
                        "agent_spawn",
                        "arena_session",
                        "verdict",
                        "scar_write",
                        "rank_mutation",
                        "hidden_scheduler",
                    ],
                },
                {
                    "recursor_id": "recursor.executor",
                    "activation_status": "candidate_only",
                    "activation_requires": [
                        "explicit_main_codex_call",
                        "no_agonic_runtime_claim",
                    ],
                    "forbidden": [
                        "execute_without_plan",
                        "self_verify_as_final",
                        "agent_spawn",
                        "arena_session",
                        "verdict",
                        "scar_write",
                        "rank_mutation",
                        "hidden_scheduler",
                    ],
                },
            ],
        },
    )
    return workspace


class RecursorAgentReadinessSdkSeedTest(unittest.TestCase):
    def test_readiness_projection_passes_with_seed_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_recursor_readiness_projection(seed_workspace(Path(tmp)))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["projection_status"], "candidate_only")
        self.assertFalse(report["install_by_default"])
        self.assertEqual(len(report["roles"]), 2)

    def test_boundary_scan_is_readiness_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_recursor_boundary_scan_report(seed_workspace(Path(tmp)))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["pair_activation_status"], "readiness_only")
        self.assertIn("no_hidden_scheduler", report["checked_stop_lines"])

    def test_projection_candidates_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = build_recursor_projection_candidates(seed_workspace(Path(tmp)))
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["projection_status"], "candidate_only")
        self.assertFalse(report["install_by_default"])

    def test_readiness_preserves_fail_when_diagnostics_and_violations_coexist(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = seed_workspace(Path(tmp))
            (workspace / "aoa-agents" / "config" / "recursor_roles.seed.json").unlink()
            projection_path = (
                workspace / "aoa-agents" / "config" / "codex_recursor_projection.candidate.json"
            )
            projection = json.loads(projection_path.read_text(encoding="utf-8"))
            projection["install_by_default"] = True
            write_json(projection_path, projection)
            report = build_recursor_readiness_projection(workspace)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(report["violations"])
        self.assertTrue(report["diagnostics"])

    def test_readiness_flags_invalid_seed_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = seed_workspace(Path(tmp))
            roles_path = workspace / "aoa-agents" / "config" / "recursor_roles.seed.json"
            roles_path.write_text("{not-json", encoding="utf-8")
            report = build_recursor_readiness_projection(workspace)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(
            any(diagnostic["kind"] == "invalid_seed_json" for diagnostic in report["diagnostics"])
        )

    def test_projection_rejects_unexpected_candidate_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = seed_workspace(Path(tmp))
            projection_path = (
                workspace / "aoa-agents" / "config" / "codex_recursor_projection.candidate.json"
            )
            projection = json.loads(projection_path.read_text(encoding="utf-8"))
            projection["candidate_agents"].append(
                {
                    "recursor_id": "recursor.admin",
                    "activation_status": "candidate_only",
                    "activation_requires": [
                        "explicit_main_codex_call",
                        "no_agonic_runtime_claim",
                    ],
                    "forbidden": [
                        "agent_spawn",
                        "arena_session",
                        "verdict",
                        "scar_write",
                        "rank_mutation",
                        "hidden_scheduler",
                    ],
                }
            )
            write_json(projection_path, projection)
            report = build_recursor_projection_candidates(workspace)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(
            any(violation["kind"] == "unexpected_projection_agent" for violation in report["violations"])
        )

    def test_readiness_rejects_invalid_pair_activation_and_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = seed_workspace(Path(tmp))
            pair_path = workspace / "aoa-agents" / "config" / "recursor_pair.seed.json"
            pair = json.loads(pair_path.read_text(encoding="utf-8"))
            pair["activation_status"] = "active_runtime"
            pair["roles"]["executor"] = "recursor.witness"
            write_json(pair_path, pair)
            report = build_recursor_boundary_scan_report(workspace)
        self.assertEqual(report["status"], "fail")
        kinds = {violation["kind"] for violation in report["violations"]}
        self.assertIn("pair_not_readiness_only", kinds)
        self.assertIn("invalid_pair_roles", kinds)

    def test_readiness_rejects_missing_pair_separation(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = seed_workspace(Path(tmp))
            pair_path = workspace / "aoa-agents" / "config" / "recursor_pair.seed.json"
            pair = json.loads(pair_path.read_text(encoding="utf-8"))
            pair["required_separation"].remove("executor_cannot_close_review")
            write_json(pair_path, pair)
            report = build_recursor_readiness_projection(workspace)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(
            any(violation["kind"] == "missing_pair_separation" for violation in report["violations"])
        )

    def test_readiness_rejects_thin_role_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = seed_workspace(Path(tmp))
            roles_path = workspace / "aoa-agents" / "config" / "recursor_roles.seed.json"
            roles = json.loads(roles_path.read_text(encoding="utf-8"))
            witness = roles["roles"][0]
            witness.pop("schema_version")
            witness.pop("owner_repo")
            witness.pop("receipts_required")
            witness["stop_lines"] = []
            write_json(roles_path, roles)
            report = build_recursor_readiness_projection(workspace)
        self.assertEqual(report["status"], "fail")
        kinds = {violation["kind"] for violation in report["violations"]}
        self.assertIn("invalid_role_schema", kinds)
        self.assertIn("invalid_role_owner", kinds)
        self.assertIn("receipts_not_required", kinds)
        self.assertIn("missing_role_stop_lines", kinds)


if __name__ == "__main__":
    unittest.main()
