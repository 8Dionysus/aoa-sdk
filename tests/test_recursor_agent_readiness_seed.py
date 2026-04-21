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
                    "recursor_id": "recursor.witness",
                    "readiness_status": "candidate",
                    "default_form": {"kind": "assistant", "arena_eligible": False},
                    "future_agonic_candidate": {
                        "enabled": False,
                        "live_authority": False,
                    },
                    "allowed_inputs": [],
                    "forbidden_actions": [
                        *global_forbidden,
                        "apply_patch",
                        "close_review_decision",
                    ],
                    "memory_policy": {"direct_durable_write_allowed": False},
                    "codex_projection": {
                        "status": "candidate_only",
                        "install_by_default": False,
                        "requires_owner_review": True,
                    },
                },
                {
                    "recursor_id": "recursor.executor",
                    "readiness_status": "candidate",
                    "default_form": {"kind": "assistant", "arena_eligible": False},
                    "future_agonic_candidate": {
                        "enabled": False,
                        "live_authority": False,
                    },
                    "allowed_inputs": [],
                    "forbidden_actions": [
                        *global_forbidden,
                        "execute_without_approved_plan",
                        "self_verify_final_truth",
                    ],
                    "memory_policy": {"direct_durable_write_allowed": False},
                    "codex_projection": {
                        "status": "candidate_only",
                        "install_by_default": False,
                        "requires_owner_review": True,
                    },
                },
            ]
        },
    )
    write_json(
        config / "recursor_pair.seed.json",
        {"activation_status": "readiness_only"},
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
                    "forbidden": [
                        "agent_spawn",
                        "arena_session",
                        "verdict",
                        "scar_write",
                        "hidden_scheduler",
                    ],
                },
                {
                    "recursor_id": "recursor.executor",
                    "activation_status": "candidate_only",
                    "forbidden": [
                        "agent_spawn",
                        "arena_session",
                        "verdict",
                        "scar_write",
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


if __name__ == "__main__":
    unittest.main()
