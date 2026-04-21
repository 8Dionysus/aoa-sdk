from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[0]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from aoa_sdk.recurrence.agent_readiness import (  # noqa: E402
    build_recursor_boundary_scan_report,
    build_recursor_projection_candidates,
    build_recursor_readiness_projection,
)


class RecursorAgentReadinessSdkSeedTest(unittest.TestCase):
    def test_readiness_projection_passes_with_seed_workspace(self):
        report = build_recursor_readiness_projection(WORKSPACE)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["projection_status"], "candidate_only")
        self.assertFalse(report["install_by_default"])
        self.assertEqual(len(report["roles"]), 2)

    def test_boundary_scan_is_readiness_only(self):
        report = build_recursor_boundary_scan_report(WORKSPACE)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["summary"]["pair_activation_status"], "readiness_only")
        self.assertIn("no_hidden_scheduler", report["checked_stop_lines"])

    def test_projection_candidates_not_installed(self):
        report = build_recursor_projection_candidates(WORKSPACE)
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["projection_status"], "candidate_only")
        self.assertFalse(report["install_by_default"])


if __name__ == "__main__":
    unittest.main()
